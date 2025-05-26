from dataclasses import dataclass, field
from typing import Tuple

from core.cartesian_point import CartesianPoint


@dataclass(slots=True)
class BuildingElementDTO:
    """Base DTO for IFC building elements"""
    name: str
    location: CartesianPoint = field(default_factory=lambda: CartesianPoint(0.0, 0.0, 0.0))
