import logging
from functools import partial
from itertools import chain
from operator import attrgetter
from typing import (
    Collection,
    Dict,
    Iterable,
    Iterator,
    Mapping,
    Optional,
    Tuple,
)

from gurobipy.gurobipy import GRB, quicksum, tuplelist

from santa_19 import gurobi
from santa_19.costs import (
    accounting_cost,
    accounting_cost_of_daily_occupancy,
    preference_cost,
)
from santa_19.inputs import Day, Family, choice
from santa_19.parameters import MAX_OCCUPANCY, MIN_OCCUPANCY
from santa_19.result import evaluate
from santa_19.solution import Solution, is_capacity_infeasible
from santa_19.typing import (
    Assignments,
    AssignmentsMutable,
    FamilyID,
    Occupancies,
    OccupanciesMutable,
)

logger = logging.getLogger(__name__)

_FEASIBLE_OCCUPANCIES = frozenset(range(MIN_OCCUPANCY, MAX_OCCUPANCY + 1))


def _can_add(
    number_of_members: int,
    current_occupancy: int,
) -> bool:
    return current_occupancy + number_of_members <= MAX_OCCUPANCY


def _process_unassigned_families(
    solution: Solution,
    unassigned_families: Collection[Family],
) -> Solution:
    still_unassigned = []

    assignments = dict(solution.assignments)
    occupancy_per_day = dict(solution.daily_occupancy)

    for family in sorted(
        unassigned_families, key=attrgetter("number_of_members"), reverse=True
    ):
        for f_choice in family.choices:
            if _can_add(family.number_of_members, occupancy_per_day[f_choice]):
                assignments[family.id] = f_choice
                occupancy_per_day[f_choice] += family.number_of_members
                break
        else:
            still_unassigned.append(family)

    while still_unassigned:
        family = still_unassigned.pop()
        for day, occupancy in occupancy_per_day.items():
            if _can_add(family.number_of_members, occupancy):
                assignments[family.id] = day
                break

    return Solution(assignments, occupancy_per_day)


def _fix_minimum_occupancy_infeasibility(
    solution: Solution,
    families_per_day: Mapping[Day, Collection[Family]],
) -> Solution:

    dates_with_violation: Mapping[Day, int] = {
        day: occupancy
        for day, occupancy in solution.daily_occupancy.items()
        if occupancy < MIN_OCCUPANCY
    }

    assignments = dict(solution.assignments)
    occupancy_per_day = dict(solution.daily_occupancy)

    for day in dates_with_violation.keys():
        related_families = [
            family
            for family in families_per_day[day]
            if (assignments[family.id] != day)
            and (
                occupancy_per_day[assignments[family.id]]
                - family.number_of_members
                >= MIN_OCCUPANCY
            )
        ]
        related_families = sorted(
            related_families, key=attrgetter("number_of_members"), reverse=True
        )

        for family in related_families:
            current_assignment = assignments[family.id]
            assignments[family.id] = day
            occupancy_per_day[day] += family.number_of_members
            occupancy_per_day[current_assignment] -= family.number_of_members

            if occupancy_per_day[day] >= MIN_OCCUPANCY:
                break

    return Solution(assignments, occupancy_per_day)


def _naive_assign(
    families: Collection[Family],
    days: Iterable[Day],
) -> Tuple[Solution, Collection[Family]]:
    sorted_families = sorted(
        families, key=attrgetter("number_of_members"), reverse=True
    )

    occupancy_per_day: Dict[Day, int] = {day: 0 for day in days}
    assignments = {}
    unassigned_families = []

    for family in sorted_families:
        for f_choice in sorted(
            family.choices,
            key=lambda day: (occupancy_per_day[day], family.choice_index[day]),
        ):
            if _can_add(family.number_of_members, occupancy_per_day[f_choice]):
                occupancy_per_day[f_choice] += family.number_of_members
                assignments[family.id] = f_choice
                break
        else:
            unassigned_families.append(family)

    return Solution(assignments, occupancy_per_day), unassigned_families


def _construct_solution(
    families: Collection[Family],
    families_per_day: Mapping[Day, Collection[Family]],
    days: Iterable[Day],
) -> Solution:

    solution, unassigned_families = _naive_assign(families, days)

    solution = _fix_minimum_occupancy_infeasibility(
        solution=solution,
        families_per_day=families_per_day,
    )

    solution = _process_unassigned_families(
        solution=solution,
        unassigned_families=unassigned_families,
    )

    return solution


def _days_related_for_occupancies(day: Day) -> Iterator[Day]:
    days = [day] + ([] if day == 1 else [day - 1])
    for d in days:
        yield d


def _apply_occupancy_change(
    occupancies: OccupanciesMutable,
    current_day: Day,
    new_day: Day,
    n: int,
) -> OccupanciesMutable:
    occupancies[current_day] -= n
    occupancies[new_day] += n
    return occupancies


def _is_feasible_swap(
    number_of_members: int,
    origin_day_occupancy: int,
    target_day_occupancy: Day,
) -> bool:
    return not is_capacity_infeasible(
        [origin_day_occupancy - number_of_members]
        + [target_day_occupancy + number_of_members]
    )


def _is_beneficial(
    family: Family,
    current_day: Day,
    prospective_day: Day,
    occupancies: Occupancies,
) -> bool:
    # Calculate change in preference cost
    pref_cost = partial(
        preference_cost,
        choices=family.choice_index,
        family_size=family.number_of_members,
    )
    current_preference_cost = pref_cost(current_day)
    new_preference_cost = pref_cost(prospective_day)
    pref_cost_change = new_preference_cost - current_preference_cost

    # Calculate change in accounting cost
    days = list(
        chain(
            _days_related_for_occupancies(current_day),
            _days_related_for_occupancies(prospective_day),
        )
    )
    current_accounting_cost = accounting_cost_of_daily_occupancy(
        occupancies, days
    )
    new_occupancies = _apply_occupancy_change(
        dict(occupancies),
        current_day,
        prospective_day,
        family.number_of_members,
    )
    new_accounting_cost = accounting_cost_of_daily_occupancy(
        new_occupancies, days
    )
    accounting_cost_change = new_accounting_cost - current_accounting_cost

    return pref_cost_change + accounting_cost_change < 0


def _apply_change(
    assignments: AssignmentsMutable,
    occupancies: OccupanciesMutable,
    family: Family,
    new_day: Day,
) -> Tuple[Assignments, Occupancies]:
    current_day = assignments[family.id]
    assignments[family.id] = new_day

    return assignments, _apply_occupancy_change(
        occupancies, current_day, new_day, family.number_of_members
    )


def _run_naive_improvement(
    solution: Solution,
    families: Collection[Family],
    days: Iterable[Day],
) -> Solution:
    family_index = {f.id: f for f in families}
    current_assignments = dict(solution.assignments)
    current_occupancies = dict(solution.daily_occupancy)

    for family_id, assigned_day in solution.assignments.items():
        family = family_index[family_id]
        assigned_choice = choice(family.choice_index, assigned_day)
        if assigned_choice > 0:
            for candidate_choice in range(assigned_choice):
                new_day = family.choices[candidate_choice]
                if _is_feasible_swap(
                    family.number_of_members,
                    current_occupancies[assigned_day],
                    current_occupancies[new_day],
                ) and _is_beneficial(
                    family, assigned_day, new_day, current_occupancies
                ):
                    current_assignments, current_occupancies = _apply_change(
                        current_assignments,
                        current_occupancies,
                        family,
                        new_day,
                    )

    return Solution.from_assignments(current_assignments, days, family_index)


def _optimize(
    families: Iterable[Family],
    days: Iterable[Day],
    family_index: Mapping[FamilyID, Family],
    mip_start: Optional[Assignments],
) -> Solution:
    with gurobi.model("santa-19") as model:

        assignment_vars = model.addVars(
            tuplelist(
                (family.id, family_choice)
                for family in families
                for family_choice in family.choices
            ),
            name="x",
            vtype=GRB.BINARY,
        )
        occupancy_vars = model.addVars(
            tuplelist(
                (occupancy, day)
                for day in days
                for occupancy in _FEASIBLE_OCCUPANCIES
            ),
            name="delta",
            vtype=GRB.BINARY,
        )
        occupancy_pairs = {
            (o, o_p, d): accounting_cost(o, o_p)
            for o in _FEASIBLE_OCCUPANCIES
            for o_p in _FEASIBLE_OCCUPANCIES
            for d in days
        }
        occupancy_pair_vars = model.addVars(
            occupancy_pairs.keys(), name="phi", lb=0, ub=1
        )
        logger.info("Created variables")

        model.addConstrs(
            (
                quicksum(
                    assignment_vars[(family_id, family_choice)]
                    for family_choice in family_index[family_id].choices
                )
                == 1
                for family_id in family_index.keys()
            ),
            name="assg",
        )
        model.addConstrs(
            (occupancy_vars.sum("*", day) == 1 for day in days), name="occ_c"
        )
        model.addConstrs(
            (
                quicksum(
                    assignment_vars.get((family.id, day), 0)
                    * family.number_of_members
                    for family in families
                )
                == quicksum(
                    occupancy_vars[(occupancy, day)] * occupancy
                    for occupancy in _FEASIBLE_OCCUPANCIES
                )
                for day in days
            ),
            name="occ",
        )
        logger.info("Set constraints")

        pref_cost_expr = quicksum(
            assignment_vars[(family.id, family_choice)]
            * preference_cost(
                family_choice, family.choice_index, family.number_of_members
            )
            for family in families
            for family_choice in family.choices
        )
        accounting_cost_expr = quicksum(
            occupancy_vars.sum(pair[0], pair[1], "*") * cost
            for pair, cost in occupancy_pairs.items()
        )

        model.setObjective(
            pref_cost_expr + accounting_cost_expr, sense=GRB.MINIMIZE
        )
        logger.info("Set objective")

        if mip_start:
            for family_id, assigned_day in mip_start.items():
                v = assignment_vars.get((family_id, assigned_day), None)
                if v:
                    v.start = 1

        model.optimize()

        if model.status == GRB.INFEASIBLE:
            model.computeIIS()
            model.write("conflict.lp")
            raise Exception("Infeasible model.")
        else:
            assignments = {
                k[0]: k[1] for k, v in assignment_vars.items() if v.X > 0.5
            }
            return Solution.from_assignments(assignments, days, family_index)


def solve(
    families: Collection[Family],
    families_per_day: Mapping[Day, Collection[Family]],
    family_index: Mapping[FamilyID, Family],
    days: Iterable[Day],
) -> Solution:
    solution = _construct_solution(families, families_per_day, days)
    current_result = evaluate(solution, family_index, days)
    logger.info(
        f"Constructed initial solution: {current_result.total_cost()}."
    )
    while True:
        solution = _run_naive_improvement(solution, families, days)
        result = evaluate(solution, family_index, days)
        if result != current_result:
            current_result = result
            logger.info(f"Improved solution: {current_result.total_cost()}.")
            continue
        break

    return _optimize(families, days, family_index, solution.assignments)
