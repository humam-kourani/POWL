from __future__ import annotations

from enum import Enum


class ModelType(Enum):
    ChoiceGraph = "ChoiceGraph"
    PartialOrder = "PartialOrder"
    Activity = "Activity"
