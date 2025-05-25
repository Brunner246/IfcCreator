import abc
import ifcopenshell
from typing import Optional
from models.dto.building_element_dto import BuildingElementDTO


class IfcBuildingElementCreator(abc.ABC):
    def __init__(self): pass

    @abc.abstractmethod
    def create_element(self, model: ifcopenshell.file,
                       context: ifcopenshell.entity_instance,
                       owner_history: ifcopenshell.entity_instance
                       , storey: ifcopenshell.entity_instance
                       ) -> ifcopenshell.entity_instance:
        pass

    @staticmethod
    def _create_placement(model: ifcopenshell.file,
                          parent_placement: Optional[ifcopenshell.entity_instance] = None,
                          location: tuple = (0.0, 0.0, 0.0),
                          axis: tuple = (0.0, 0.0, 1.0),
                          ref_direction: tuple = (1.0, 0.0, 0.0)) -> ifcopenshell.entity_instance:
        """Create a standard placement for an element"""
        origin = model.create_entity("IfcCartesianPoint", Coordinates=location)
        z_axis = model.create_entity("IfcDirection", DirectionRatios=axis)
        x_axis = model.create_entity("IfcDirection", DirectionRatios=ref_direction)

        axis_placement = model.create_entity(
            "IfcAxis2Placement3D",
            Location=origin,
            Axis=z_axis,
            RefDirection=x_axis
        )

        return model.create_entity(
            "IfcLocalPlacement",
            PlacementRelTo=parent_placement,
            RelativePlacement=axis_placement
        )
