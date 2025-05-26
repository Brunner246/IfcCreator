import abc
from typing import Optional

import ifcopenshell

from core.cartesian_point import CartesianPoint


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
    def _create_local_placement(model: ifcopenshell.file,
                                parent_placement: Optional[ifcopenshell.entity_instance] = None,
                                location: tuple = (0.0, 0.0, 0.0),
                                axis: tuple = (0.0, 0.0, 1.0),
                                ref_direction: tuple = (1.0, 0.0, 0.0)) -> ifcopenshell.entity_instance:
        """Create a standard placement for an element"""
        origin = IfcBuildingElementCreator._create_cartesian_point(location, model)
        z_axis = IfcBuildingElementCreator._create_direction(axis, model)
        x_axis = IfcBuildingElementCreator._create_direction(ref_direction, model)

        axis_placement = IfcBuildingElementCreator._create_axis_2_placement_3d(model, origin, x_axis, z_axis)

        return model.create_entity(
            "IfcLocalPlacement",
            PlacementRelTo=parent_placement,
            RelativePlacement=axis_placement
        )

    @staticmethod
    def _create_direction(axis, model):
        z_axis = model.create_entity("IfcDirection", DirectionRatios=axis)
        return z_axis

    @staticmethod
    def _create_cartesian_point(location: CartesianPoint, model):
        origin = model.create_entity("IfcCartesianPoint", Coordinates=tuple(location))
        return origin

    @staticmethod
    def _create_axis_2_placement_3d(model, origin, x_axis, z_axis):
        axis_placement = model.create_entity(
            "IfcAxis2Placement3D",
            Location=origin,
            Axis=z_axis,
            RefDirection=x_axis
        )
        return axis_placement
