from dataclasses import dataclass
from typing import Tuple


@dataclass(slots=True)
class BuildingElementDTO:
    """Base DTO for IFC building elements"""
    name: str
    location: Tuple[float, float, float] = (0.0, 0.0, 0.0)