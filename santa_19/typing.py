from typing import Dict, List, Mapping

Day = int
FamilyID = int
ChoiceIndex = int
OrderedChoices = List[Day]
ChoicesByDay = Mapping[Day, ChoiceIndex]
Assignments = Mapping[FamilyID, Day]
AssignmentsMutable = Dict[FamilyID, Day]
Occupancies = Mapping[Day, int]
OccupanciesMutable = Dict[Day, int]
