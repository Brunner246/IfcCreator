# services/ifc_model_manager.py

import time
import uuid
from pathlib import Path

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.api.context
import ifcopenshell.api.project
import ifcopenshell.api.root
import ifcopenshell.api.unit
import ifcopenshell.guid

from core.cartesian_point import CartesianPoint
from models.ifc_schemas import IfcBeamCreateRequest
from services.strategies.building_element_creator import IfcBuildingElementCreator
from services.strategies.ifc4_strategy import IFC4Strategy
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

        self._building_element_entities = []

        # model = ifcopenshell.api.project.create_file()

    def create_file(self) -> 'IfcModelManager':
        self.model = ifcopenshell.file(schema=self.strategy.get_schema())
        # header: IfcSpfHeader = None
        # header.file_schema
        print(self.model.wrapped_data.header)
        return self

    def initialize_model(self, project_name: str = "Demo Project",
                         description: str = "IFC Reference View") -> 'IfcModelManager':
        origin = self._create_cartesian_point(CartesianPoint(0.0, 0.0, 0.0))
        axis = self._create_direction(CartesianPoint(0.0, 0.0, 1.0))  # Z-axis
        ref_direction = self._create_direction(CartesianPoint(1.0, 0.0, 0.0))
        world_coordinate_system = self._create_axis_2placement_3d(origin, axis, ref_direction)

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

    def _create_cartesian_point(self, point: CartesianPoint):
        origin = self.model.create_entity("IfcCartesianPoint", Coordinates=(point.x, point.y, point.z))
        return origin

    def add_building_element(self, creator: IfcBuildingElementCreator) -> 'IfcModelManager':
        """Add a building element to the model using the provided creator"""
        if not self.model or not self.storey:
            raise ValueError("Model must be initialized before adding elements")

        instance = creator.create_element(
            self.model,
            self.context,
            self.owner_history,
            self.storey
        )
        self._building_element_entities.append(instance)

        return self

    def _create_axis_2placement_3d(self, origin: ifcopenshell.entity_instance, axis: ifcopenshell.entity_instance,
                                   ref_direction: ifcopenshell.entity_instance) -> ifcopenshell.entity_instance:
        axis2placement3d = self.model.create_entity(
            "IfcAxis2Placement3D",
            Location=origin,
            Axis=axis,
            RefDirection=ref_direction
        )
        return axis2placement3d

    def _create_direction(self, point: CartesianPoint):
        axis = self.model.create_entity("IfcDirection", DirectionRatios=(point.x, point.y, point.z))
        return axis

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
