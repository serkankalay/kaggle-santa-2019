from __future__ import annotations

import csv
from dataclasses import dataclass
from itertools import islice
from pathlib import Path
from typing import (
    Callable,
    Collection,
    Iterable,
    Iterator,
    Mapping,
    Sequence,
    T,
)

from santa_19.typing import (
    Assignments,
    ChoiceIndex,
    ChoicesByDay,
    Day,
    FamilyID,
    OrderedChoices,
)

_UNRELATED_CHOICE_INDEX = 10


@dataclass(frozen=True)
class Family:
    id: FamilyID
    choices: OrderedChoices
    choice_index: ChoicesByDay
    number_of_members: int

    @staticmethod
    def parse(row: Sequence[str]) -> Family:
        return Family(
            id=int(row[0]),
            choices=[int(c) for c in row[1:11]],
            choice_index={int(c): i for i, c in enumerate(row[1:11])},
            number_of_members=int(row[11]),
        )


def families_per_day(
    families: Collection[Family],
    days: Iterable[Day],
) -> Mapping[Day, Collection[Family]]:
    per_day = {day: [] for day in days}
    for family in families:
        for choice_day in family.choices:
            per_day[choice_day].append(family)

    return per_day


def choice(choices_by_day: ChoicesByDay, day: Day) -> ChoiceIndex:
    try:
        return choices_by_day[day]
    except KeyError:
        return _UNRELATED_CHOICE_INDEX


def parse_assignments(
    p: Path,
) -> Assignments:
    with p.open("rt") as rfile:
        return {
            int(sub[0]): int(sub[1])
            for sub in islice(csv.reader(rfile), 1, None)
        }


def parse_csv(
    p: Path,
    parser: Callable[[Sequence[str]], T],
) -> Iterator[T]:
    with p.open("rt") as rfile:
        yield from map(parser, islice(csv.reader(rfile), 1, None))
