import ifcopenshell
import ifcopenshell.guid
from models.dto.beam_dto import BeamDTO
from services.strategies.building_element_creator import IfcBuildingElementCreator


class IfcBeamCreator(IfcBuildingElementCreator):
    def __init__(self, properties: BeamDTO):
        super().__init__()
        self._beam_properties = properties

    def create_element(self, model: ifcopenshell.file,
                       context: ifcopenshell.entity_instance,
                       owner_history: ifcopenshell.entity_instance
                       , storey: ifcopenshell.entity_instance
                       ) -> ifcopenshell.entity_instance:
        """Create an IfcBeam with rectangular profile"""
        object_placement = self._create_placement(
            model,
            storey.ObjectPlacement,
            location=self._beam_properties.building_element.location
        )

        shape = self._create_beam_shape(model, context,
                                        self._beam_properties.width,
                                        self._beam_properties.height,
                                        self._beam_properties.length)

        beam = model.create_entity(
            "IfcBeam",
            GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=owner_history,
            Name=self._beam_properties.building_element.name,
            ObjectPlacement=object_placement,
            Representation=shape
        )

        containment_rel = self._find_or_create_containment_relationship(
            model, owner_history, storey, beam
        )

        # model.create_entity(
        #     "IfcRelContainedInSpatialStructure",
        #     GlobalId=ifcopenshell.guid.new(),
        #     OwnerHistory=owner_history,
        #     RelatingStructure=storey,
        #     RelatedElements=[beam]
        # )

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
        origin = model.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0))
        ref_dir_2d = model.create_entity("IfcDirection", DirectionRatios=(1.0, 0.0))
        axis2placement2d = model.create_entity(
            "IfcAxis2Placement2D",
            Location=origin,
            RefDirection=ref_dir_2d
        )

        # Create profile and solid
        profile = model.create_entity(
            "IfcRectangleProfileDef",
            ProfileType="AREA",
            XDim=width,
            YDim=height,
            Position=axis2placement2d
        )

        axis2placement3d = self._create_placement(model)
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
