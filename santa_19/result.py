import csv
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Mapping

from santa_19.costs import (
    accounting_cost_of_daily_occupancy,
    preference_cost_of_assignments,
)
from santa_19.inputs import Day, Family, FamilyID
from santa_19.solution import Solution

BUFFET_VALUE = 36
NORTH_POLE_HELICOPTER_RIDE_TICKET_VALUE = 398

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Result:
    preference_cost: float
    accounting_cost: float

    def total_cost(
        self,
    ) -> float:
        return self.preference_cost + self.accounting_cost


def evaluate(
    solution: Solution,
    family_index: Mapping[FamilyID, Family],
    days: Iterable[Day],
) -> Result:
    return Result(
        preference_cost=preference_cost_of_assignments(
            solution.assignments, family_index
        ),
        accounting_cost=accounting_cost_of_daily_occupancy(
            solution.daily_occupancy, days
        ),
    )


def write_solution(solution: Solution) -> str:
    file_name = Path(
        f"data/outputs/solution_{datetime.now():%Y-%m-%d_%H:%M:%S%z}.csv"
    )
    logger.info(f"Printing solution to {file_name}")
    with open(file_name, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["family_id", "assigned_day"])
        for family_id, day in sorted(solution.assignments.items()):
            writer.writerow([family_id, day])
    return file_name
