import logging
from collections import defaultdict
from itertools import repeat
from pathlib import Path
from typing import Dict, Mapping

import click
from plotly import graph_objects as go

from .inputs import (
    ChoiceIndex,
    Day,
    Family,
    FamilyID,
    choice,
    families_per_day,
    parse_assignments,
    parse_csv,
)
from .result import evaluate, write_solution
from .solution import Solution, is_feasible
from .solver import MAX_OCCUPANCY, MIN_OCCUPANCY, solve

# from .typing import Solution

DAYS = list(range(1, 101))

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)


@click.group()
def cli():
    "Santa19 Command line interface"


@cli.command()
@click.option(
    "--p/--np", default=False, help="Control to plot the solution by default."
)
def run(p: bool) -> None:
    families = list(parse_csv(Path("data/family_data.csv"), Family.parse))
    family_index = {f.id: f for f in families}
    family_day_index = families_per_day(families, DAYS)

    solution = solve(families, family_day_index, family_index, DAYS)

    if is_feasible(
        solution=solution,
        families=family_index,
    ):
        result = evaluate(solution, family_index, DAYS)
        logger.info(
            f"Solution with total cost: {result.total_cost()} "
            f"(preference: {result.preference_cost}, accounting:{result.accounting_cost})"  # noqa: E501
        )
        file_name = write_solution(solution)
        if p:
            _plot(solution, family_index, file_name)
    else:
        logger.error("Solution infeasible")


def _plot(
    solution: Solution,
    family_index: Mapping[FamilyID, Family],
    solution_file: str,
) -> None:
    if not is_feasible(solution, family_index):
        logger.error("Infeasible solution.")

    targets: Dict[ChoiceIndex, Dict[Day, int]] = {}
    for choice_level in range(0, 11):
        targets[choice_level] = defaultdict(int)

    for family_id, assigned_day in solution.assignments.items():
        choice_level = choice(
            family_index[family_id].choice_index, assigned_day
        )
        target = targets[choice_level]
        target[assigned_day] = (
            target.get(assigned_day, 0)
            + family_index[family_id].number_of_members
        )

    fig = go.Figure(
        data=[
            go.Bar(
                name=f"Choice {choice_level}",
                x=list(targets[choice_level].keys()),
                y=list(targets[choice_level].values()),
            )
            for choice_level in range(0, 11)
        ],
    )
    fig.add_trace(
        go.Scatter(
            x=DAYS,
            y=list(repeat(MIN_OCCUPANCY, len(DAYS))),
            mode="lines",
            name="Min Occupancy",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=DAYS,
            y=list(repeat(MAX_OCCUPANCY, len(DAYS))),
            mode="lines",
            name="Max Occupancy",
        )
    )
    result = evaluate(solution, family_index, DAYS)
    fig.update_layout(
        barmode="stack",
        title=f"Total cost: {round(result.total_cost(), 2)} "
        f"(prefc: {round(result.preference_cost, 2)}, acc.: {round(result.accounting_cost, 2)})"  # noqa: E501
        f" | from {solution_file}",
    )
    fig.show()


@cli.command()
@click.argument("solution_file")
def plot(solution_file: str) -> None:
    family_index = {
        f.id: f for f in parse_csv(Path("data/family_data.csv"), Family.parse)
    }
    assignments = parse_assignments(Path(f"data/outputs/{solution_file}"))
    _plot(
        solution=Solution.from_assignments(assignments, DAYS, family_index),
        family_index=family_index,
        solution_file=solution_file,
    )
