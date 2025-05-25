from dataclasses import dataclass
from models.dto.building_element_dto import BuildingElementDTO


@dataclass(slots=True)
class BeamDTO:
    """DTO for beam properties"""
    building_element: BuildingElementDTO
    width: float = 0.2
    height: float = 0.4
    length: float = 3.0
