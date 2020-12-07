from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable, Mapping

from santa_19.inputs import Family
from santa_19.parameters import MAX_OCCUPANCY, MIN_OCCUPANCY
from santa_19.typing import Assignments, Day, FamilyID, Occupancies

logger = logging.getLogger(__name__)


def _calculate_occupancy_per_day(
    assignments: Assignments,
    days: Iterable[Day],
    families: Mapping[FamilyID, Family],
) -> Occupancies:
    occupancy = {day: 0 for day in days}
    for family_id, day in assignments.items():
        occupancy[day] += families[family_id].number_of_members

    return occupancy


@dataclass(frozen=True)
class Solution:
    assignments: Assignments
    daily_occupancy: Occupancies

    @classmethod
    def from_assignments(
        cls,
        assignments: Assignments,
        days: Iterable[Day],
        family_index: Mapping[FamilyID, Family],
    ) -> Solution:
        return cls(
            assignments=assignments,
            daily_occupancy=_calculate_occupancy_per_day(
                assignments, days, family_index
            ),
        )


def is_capacity_infeasible(occupancies: Iterable[int]) -> bool:
    return any(
        (occupancy < MIN_OCCUPANCY) or (occupancy > MAX_OCCUPANCY)
        for occupancy in occupancies
    )


def is_feasible(
    solution: Solution,
    families: Mapping[FamilyID, Family],
) -> bool:
    if is_capacity_infeasible(solution.daily_occupancy.values()):
        logger.info("Minimum or maximum occupancy violated.")
        return False

    unassigned_families = set(families.keys()).difference(
        set(solution.assignments.keys())
    )
    if not unassigned_families:
        return True

    logger.info(
        f"The following families were unassigned: " f"{unassigned_families}"
    )
    return False
