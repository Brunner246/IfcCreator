import ifcopenshell
import ifcopenshell.guid

from core.cartesian_point import CartesianPoint
from models.dto.beam_dto import BeamDTO
from services.strategies.building_element_creator import IfcBuildingElementCreator


class IfcBeamCreator(IfcBuildingElementCreator):
    def __init__(self, properties: BeamDTO):
        super().__init__()
        self._beam_properties = properties

    def create_element(self, model: ifcopenshell.file,
                       context: ifcopenshell.entity_instance,
                       owner_history: ifcopenshell.entity_instance,
                       storey: ifcopenshell.entity_instance) -> ifcopenshell.entity_instance:
        """Create an IfcBeam with both 3D and 2D representation."""

        object_placement = self._create_local_placement(
            model,
            storey.ObjectPlacement,
            location=tuple(self._beam_properties.building_element.location)
        )

        shape_3d = self._create_beam_shape(model, context,
                                           self._beam_properties.width,
                                           self._beam_properties.height,
                                           self._beam_properties.length)

        # context_2d = None
        #
        # contex_identifier = "Plan 2d View"
        # project = model.by_type("IfcProject")[0]
        # if contex_identifier not in map(lambda x: x.ContextIdentifier, project.RepresentationContexts):
        #     context_2d = model.create_entity(
        #         "IfcGeometricRepresentationContext",
        #         ContextIdentifier=contex_identifier,
        #         ContextType="Plan",
        #         CoordinateSpaceDimension=2,
        #         Precision=1e-5,
        #         WorldCoordinateSystem=model.create_entity(
        #             "IfcAxis2Placement2D",
        #             Location=model.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0))
        #         )
        #     )
        #     project.RepresentationContexts = list(project.RepresentationContexts) + [context_2d]
        # else:
        #     context_2d = next(
        #         ctx for ctx in project.RepresentationContexts if ctx.ContextIdentifier == contex_identifier
        #     )
        #
        # # --- Create 2D shape ---
        # w = self._beam_properties.width
        # l = self._beam_properties.height
        #
        # points = [
        #     model.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0)),
        #     model.create_entity("IfcCartesianPoint", Coordinates=(l, 0.0)),
        #     model.create_entity("IfcCartesianPoint", Coordinates=(l, w)),
        #     model.create_entity("IfcCartesianPoint", Coordinates=(0.0, w)),
        #     model.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0))
        # ]
        # polyline = model.create_entity("IfcPolyline", Points=points)
        #
        # shape_2d = model.create_entity(
        #     "IfcShapeRepresentation",
        #     ContextOfItems=context_2d,
        #     RepresentationIdentifier="Plan",
        #     RepresentationType="GeometricCurveSet",  # or Annotation2D
        #     Items=[polyline]
        # )
        #
        # merged_shape = model.create_entity(
        #     "IfcProductDefinitionShape",
        #     Representations=[
        #         shape_3d.Representations[0],  # 3D
        #         shape_2d  # 2D
        #     ]
        # )

        beam = model.create_entity(
            "IfcBeam",
            GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=owner_history,
            Name=self._beam_properties.building_element.name,
            ObjectPlacement=object_placement,
            Representation=shape_3d  # merged_shape
        )

        # --- Add to spatial structure ---
        self._find_or_create_containment_relationship(model, owner_history, storey, beam)

        return beam

    @staticmethod
    def _find_or_create_containment_relationship(model, owner_history, storey, element):
        for rel in model.by_type("IfcRelContainedInSpatialStructure"):
            if rel.RelatingStructure == storey:
                # Existing relationship found, add the element to it
                # rel.RelatedElements.append(element)
                related_elements = list(rel.RelatedElements)
                related_elements.append(element)
                rel.RelatedElements = related_elements
                return rel

        return model.create_entity(
            "IfcRelContainedInSpatialStructure",
            GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=owner_history,
            RelatingStructure=storey,
            RelatedElements=[element]
        )

    def _create_beam_shape(self, model, context, width, height, length):
        """Create shape representation for a beam"""
        axis2placement2d = self._create_axis_2_placement_2d(model)

        # Create profile and solid
        profile = self._create_rectangle_profile_def(axis2placement2d, height, model, width)

        axis2placement3d = self._create_local_placement(model)
        direction_z = model.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0))

        extruded = model.create_entity(
            "IfcExtrudedAreaSolid",
            SweptArea=profile,
            Depth=length,
            ExtrudedDirection=direction_z,
            Position=axis2placement3d.RelativePlacement
        )

        body_rep = model.create_entity(
            "IfcShapeRepresentation",
            ContextOfItems=context,
            RepresentationIdentifier="Body",
            RepresentationType="SweptSolid",
            Items=[extruded]
        )

        return model.create_entity(
            "IfcProductDefinitionShape",
            Representations=[body_rep]
        )

    @staticmethod
    def _create_rectangle_profile_def(axis2placement2d, height, model, width):
        profile = model.create_entity(
            "IfcRectangleProfileDef",
            ProfileType="AREA",
            XDim=width,
            YDim=height,
            Position=axis2placement2d
        )
        return profile

    def _create_axis_2_placement_2d(self, model):
        origin = self._create_cartesian_point(CartesianPoint(0.0, 0.0, 0.0), model)
        ref_dir_2d = model.create_entity("IfcDirection", DirectionRatios=(1.0, 0.0))
        axis2placement2d = model.create_entity(
            "IfcAxis2Placement2D",
            Location=origin,
            RefDirection=ref_dir_2d
        )
        return axis2placement2d
