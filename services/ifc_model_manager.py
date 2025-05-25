# services/ifc_model_manager.py

import time
import uuid
from pathlib import Path
from typing import Dict, Any

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.api.root
import ifcopenshell.api.unit
import ifcopenshell.api.context
import ifcopenshell.api.project
import ifcopenshell.guid
from ifcopenshell.ifcopenshell_wrapper import IfcSpfHeader

from models.ifc_schemas import IfcBeamCreateRequest
from services.strategies.building_element_creator import IfcBuildingElementCreator
from services.strategies.ifc2x3_strategy import IFC2X3Strategy
from services.strategies.ifc4_strategy import IFC4Strategy
from services.strategies.ifc4x3_strategy import IFC4X3Strategy
from services.strategies.model_strategy import IfcModelStrategy

# https://docs.ifcopenshell.org/ifcopenshell-python/code_examples.html

class IfcModelManager:
    def __init__(self, schema_strategy: IfcModelStrategy = None):
        self.strategy = schema_strategy or IFC4Strategy()
        self.model = None
        self.project = None
        self.site = None
        self.building = None
        self.storey = None
        self.context = None
        self.owner_history = None

        # model = ifcopenshell.api.project.create_file()

    def create_file(self) -> 'IfcModelManager':
        self.model = ifcopenshell.file(schema=self.strategy.get_schema())
        # header: IfcSpfHeader = None
        # header.file_schema
        print(self.model.wrapped_data.header)
        return self

    def initialize_model(self, project_name: str = "Demo Project",
                         description: str = "IFC Reference View") -> 'IfcModelManager':
        origin = self.model.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0))
        axis = self.model.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0))
        ref_direction = self.model.create_entity("IfcDirection", DirectionRatios=(1.0, 0.0, 0.0))
        world_coordinate_system = self.model.create_entity(
            "IfcAxis2Placement3D",
            Location=origin,
            Axis=axis,
            RefDirection=ref_direction
        )

        true_north = self.model.create_entity("IfcDirection", DirectionRatios=(0.0, 1.0))
        self.context = self.model.create_entity(
            "IfcGeometricRepresentationContext",
            ContextIdentifier="Body",
            ContextType="Model",
            CoordinateSpaceDimension=3,
            Precision=1e-5,
            WorldCoordinateSystem=world_coordinate_system,
            TrueNorth=true_north
        )

        self.owner_history = self._create_owner_history()

        self.project = self.model.create_entity(
            "IfcProject",
            GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=self.owner_history,
            Name=project_name,
            Description=f"Intended View: {self.strategy.get_schema()} {description}",
            RepresentationContexts=[self.context]
        )


        self.site = self._create_site(world_coordinate_system)
        self.building = self._create_building()
        self.storey = self._create_storey()

        self._create_aggregation(self.project, [self.site])
        self._create_aggregation(self.site, [self.building])
        self._create_aggregation(self.building, [self.storey])

        self.strategy.create_specific_entities(self)

        return self

    def add_building_element(self, creator: IfcBuildingElementCreator) -> ifcopenshell.entity_instance:
        """Add a building element to the model using the provided creator"""
        if not self.model or not self.storey:
            raise ValueError("Model must be initialized before adding elements")

        return creator.create_element(
            self.model,
            self.context,
            self.owner_history,
            self.storey
        )

    def add_beam(self, data: IfcBeamCreateRequest) -> ifcopenshell.entity_instance:
        """Add a beam to the model"""
        # Create placement and direction entities
        origin = self.model.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0))
        axis = self.model.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0))
        ref_direction = self.model.create_entity("IfcDirection", DirectionRatios=(1.0, 0.0, 0.0))
        axis2placement3d = self.model.create_entity(
            "IfcAxis2Placement3D",
            Location=origin,
            Axis=axis,
            RefDirection=ref_direction
        )

        ref_dir_2d = self.model.create_entity("IfcDirection", DirectionRatios=(1.0, 0.0))
        axis2placement2d = self.model.create_entity(
            "IfcAxis2Placement2D",
            Location=origin,
            RefDirection=ref_dir_2d
        )

        # Create profile and solid
        profile = self.model.create_entity(
            "IfcRectangleProfileDef",
            ProfileType="AREA",
            XDim=data.width,
            YDim=data.height,
            Position=axis2placement2d
        )

        direction_z = self.model.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0))
        extruded = self.model.create_entity(
            "IfcExtrudedAreaSolid",
            SweptArea=profile,
            Depth=data.length,
            ExtrudedDirection=direction_z,
            Position=axis2placement3d
        )

        body_rep = self.model.create_entity(
            "IfcShapeRepresentation",
            ContextOfItems=self.context,
            RepresentationIdentifier="Body",
            RepresentationType="SweptSolid",
            Items=[extruded]
        )

        shape = self.model.create_entity("IfcProductDefinitionShape", Representations=[body_rep])

        beam: ifcopenshell.entity_instance = self.model.create_entity(
            "IfcBeam",
            GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=self.owner_history,
            Name=data.name,
            ObjectPlacement=self.model.create_entity(
                "IfcLocalPlacement",
                PlacementRelTo=self.storey.ObjectPlacement,
                RelativePlacement=axis2placement3d
            ),
            Representation=shape
        )

        self.model.create_entity(
            "IfcRelContainedInSpatialStructure",
            GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=self.owner_history,
            RelatingStructure=self.storey,
            RelatedElements=[beam]
        )

        return beam

    def save(self, file_path: str = None) -> str:
        if file_path is None:
            file_path = self._generate_file_path()

        self.model.write(file_path)
        return file_path

    def _create_owner_history(self) -> ifcopenshell.entity_instance:

        creation_date_time = int(time.time())
        person = self.model.create_entity(
            "IfcPerson",
            FamilyName="Brunner",
            GivenName="Michael"
        )
        organization = self.model.create_entity(
            "IfcOrganization",
            Name="Brunner246",
            Description="Brunner246"
        )
        person_and_organization = self.model.create_entity(
            "IfcPersonAndOrganization",
            ThePerson=person,
            TheOrganization=organization
        )
        application = self.model.create_entity(
            "IfcApplication",
            ApplicationDeveloper=organization,
            Version="0.1.0",
            ApplicationFullName="IfcCreator",
            ApplicationIdentifier="ABC123"
        )
        return self.model.create_entity(
            "IfcOwnerHistory",
            OwningUser=person_and_organization,
            OwningApplication=application,
            CreationDate=creation_date_time
        )

    def _create_site(self, world_coordinate_system) -> ifcopenshell.entity_instance:
        """Create site entity"""
        site_placement = self.model.create_entity(
            "IfcLocalPlacement",
            PlacementRelTo=None,
            RelativePlacement=world_coordinate_system
        )
        return self.model.create_entity(
            "IfcSite",
            GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=self.owner_history,
            Name="Site",
            ObjectPlacement=site_placement
        )

    def _create_building(self) -> ifcopenshell.entity_instance:
        building_placement = self.model.create_entity(
            "IfcLocalPlacement",
            PlacementRelTo=self.site.ObjectPlacement,
            RelativePlacement=self.model.create_entity(
                "IfcAxis2Placement3D",
                Location=self.model.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0))
            )
        )
        return self.model.create_entity(
            "IfcBuilding",
            GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=self.owner_history,
            Name="Building",
            ObjectPlacement=building_placement
        )

    def _create_storey(self) -> ifcopenshell.entity_instance:
        storey_placement = self.model.create_entity(
            "IfcLocalPlacement",
            PlacementRelTo=self.building.ObjectPlacement,
            RelativePlacement=self.model.create_entity(
                "IfcAxis2Placement3D",
                Location=self.model.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0))
            )
        )
        return self.model.create_entity(
            "IfcBuildingStorey",
            GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=self.owner_history,
            Name="Storey",
            ObjectPlacement=storey_placement
        )

    def _create_aggregation(self, relating_object, related_objects) -> ifcopenshell.entity_instance:
        return self.model.create_entity(
            "IfcRelAggregates",
            GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=self.owner_history,
            RelatingObject=relating_object,
            RelatedObjects=related_objects
        )

    @staticmethod
    def _generate_file_path() -> str:
        """Generate a unique file path"""
        output_dir = Path("generated")
        output_dir.mkdir(exist_ok=True)
        return str(output_dir / f"{uuid.uuid4()}.ifc")


class IfcModelDirector:

    def __init__(self, model_manager: IfcModelManager):
        self.model_manager = model_manager # or IfcModelManager()

    def set_strategy(self, strategy: IfcModelStrategy) -> 'IfcModelDirector':
        self.model_manager = IfcModelManager(strategy)
        return self

    def construct_basic_model(self, project_name: str = "Demo Project",
                              description: str = "Reference View") -> 'IfcModelDirector':

        self.model_manager.create_file().initialize_model(
            project_name=project_name,
            description=description
        )
        return self

    def get_result(self) -> IfcModelManager:
        return self.model_manager


class IfcModelManagerFactory:
    @staticmethod
    def create_manager(schema_version: str = "IFC4") -> IfcModelManager:
        strategy_map = {
            "IFC4": IFC4Strategy(),
            "IFC2X3": IFC2X3Strategy(),
            "IFC4X3": IFC4X3Strategy()
        }

        strategy = strategy_map.get(schema_version.upper())
        if not strategy:
            raise ValueError(f"Unsupported schema version: {schema_version}")

        return IfcModelManager(strategy)


def create_ifc_file(data: IfcBeamCreateRequest, schema: str = "IFC4") -> str:
    """Create an IFC file with a beam using the object-oriented service"""
    manager = IfcModelManagerFactory.create_manager(schema)

    (manager
     .create_file()
     .initialize_model()
     .add_beam(data))

    return manager.save()
