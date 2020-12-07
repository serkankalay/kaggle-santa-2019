from typing import Callable, Iterable, Mapping

from santa_19.inputs import Family
from santa_19.typing import (
    Assignments,
    ChoiceIndex,
    ChoicesByDay,
    Day,
    FamilyID,
    Occupancies,
)

BUFFET_VALUE = 36
NORTH_POLE_HELICOPTER_RIDE_TICKET_VALUE = 398


def _cost_choice_0(family_size: int) -> float:
    return 0


def _cost_choice_1(family_size: int) -> float:
    return 50


def _cost_choice_2(family_size: int) -> float:
    return 50 + BUFFET_VALUE * 0.25 * family_size


def _cost_choice_3(family_size: int) -> float:
    return 100 + BUFFET_VALUE * 0.25 * family_size


def _cost_choice_4(family_size: int) -> float:
    return 200 + BUFFET_VALUE * 0.25 * family_size


def _cost_choice_5(family_size: int) -> float:
    return 200 + BUFFET_VALUE * 0.5 * family_size


def _cost_choice_6(family_size: int) -> float:
    return 300 + BUFFET_VALUE * 0.5 * family_size


def _cost_choice_7(family_size: int) -> float:
    return 300 + BUFFET_VALUE * family_size


def _cost_choice_8(family_size: int) -> float:
    return 400 + BUFFET_VALUE * 0.5 * family_size


def _cost_choice_9(family_size: int) -> float:
    return (
        500
        + BUFFET_VALUE * 0.5 * family_size
        + NORTH_POLE_HELICOPTER_RIDE_TICKET_VALUE * 0.5 * family_size
    )


CHOICE_COST_FUNCS: Mapping[ChoiceIndex, Callable[[int], float]] = {
    0: _cost_choice_0,
    1: _cost_choice_1,
    2: _cost_choice_2,
    3: _cost_choice_3,
    4: _cost_choice_4,
    5: _cost_choice_5,
    6: _cost_choice_6,
    7: _cost_choice_7,
    8: _cost_choice_8,
    9: _cost_choice_9,
}


def preference_cost(
    assigned: Day,
    choices: ChoicesByDay,
    family_size: int,
) -> float:
    try:
        choice = choices[assigned]
        return CHOICE_COST_FUNCS[choice](family_size)
    except KeyError:
        return (
            500
            + BUFFET_VALUE * family_size
            + NORTH_POLE_HELICOPTER_RIDE_TICKET_VALUE * family_size
        )


def preference_cost_of_assignments(
    assignments: Assignments, family_index: Mapping[FamilyID, Family]
) -> float:
    preference = 0
    for family_id, day in assignments.items():
        family = family_index[family_id]
        preference += preference_cost(
            day,
            family.choice_index,
            family.number_of_members,
        )
    return preference


def accounting_cost(occupancy: int, occupancy_next_day: int) -> float:
    return (
        (occupancy - 125.0)
        / 400.0
        * occupancy ** (0.5 + abs(occupancy - occupancy_next_day) / 50.0)
    )


def accounting_cost_of_daily_occupancy(
    daily_occupancy: Occupancies, days: Iterable[Day]
) -> float:
    accounting = 0
    for day in days:
        accounting += accounting_cost(
            daily_occupancy[day],
            daily_occupancy.get(day + 1, daily_occupancy[day]),
        )
    return accounting
