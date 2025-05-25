import uuid
from pathlib import Path

import ifcopenshell
import ifcopenshell.api

from models.ifc_schemas import IfcBeamCreateRequest

class IfcModel:
    def __init__(self, ifc_file_path: str):
        self.ifc_file_path = ifc_file_path
        self.ifc = ifcopenshell.open(ifc_file_path)

    def save(self):
        self.ifc.write(self.ifc_file_path)


def create_ifc_file_path() -> str:
    output_dir = Path("generated")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"{uuid.uuid4()}.ifc"
    return str(output_path)


def create_ifc_file(data: IfcBeamCreateRequest) -> str:
    ifc = ifcopenshell.file(schema="IFC4")
    origin = ifc.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0))
    axis = ifc.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0))  # Z-axis
    ref_direction = ifc.create_entity("IfcDirection", DirectionRatios=(1.0, 0.0, 0.0))  # X-axis
    world_coordinate_system = ifc.create_entity("IfcAxis2Placement3D", Location=origin,
                                                Axis=axis, RefDirection=ref_direction)
    true_north = create_true_north(ifc)
    context = ifc.create_entity("IfcGeometricRepresentationContext", ContextIdentifier="Body",
                                ContextType="Model",
                                CoordinateSpaceDimension=3, Precision=1e-5,
                                WorldCoordinateSystem=world_coordinate_system,
                                TrueNorth=true_north, )
    owner_history = def_create_owner_history(ifc)
    project = ifc.create_entity("IfcProject", GlobalId=ifcopenshell.guid.new(), OwnerHistory=owner_history,
                                Name="DemoProject",
                                Description="Intended View: IFC4 Reference View",
                                RepresentationContexts=[context],
                                )

    site = create_site(ifc, owner_history, world_coordinate_system)
    building = create_building(ifc, owner_history, site)
    storey = create_storey(building, ifc, owner_history)

    create_rel_aggregates_relation(ifc, owner_history, project, site)
    create_rel_aggregates_relation(ifc, owner_history, site, building)
    create_rel_aggregates_relation(ifc, owner_history, building, storey)

    axis2placement3d = ifc.create_entity("IfcAxis2Placement3D", Location=origin,
                                         Axis=axis, RefDirection=ref_direction)

    ref_dir_2d = ifc.create_entity("IfcDirection", DirectionRatios=(1.0, 0.0))  # X-axis
    axis2placement2d = ifc.create_entity("IfcAxis2Placement2D", Location=origin, RefDirection=ref_dir_2d)

    # Profile and solid
    profile = ifc.create_entity(
        "IfcRectangleProfileDef",
        ProfileType="AREA",
        XDim=data.width,
        YDim=data.height,
        Position=axis2placement2d,
    )

    direction_z = ifc.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0))  # Extrude in Z
    extruded = ifc.create_entity(
        "IfcExtrudedAreaSolid",
        SweptArea=profile,
        Depth=data.length,
        ExtrudedDirection=direction_z,
        Position=axis2placement3d,
    )

    body_rep = ifc.create_entity(
        "IfcShapeRepresentation",
        ContextOfItems=context,
        RepresentationIdentifier="Body",
        RepresentationType="SweptSolid",
        Items=[extruded],
    )

    shape = ifc.create_entity("IfcProductDefinitionShape", Representations=[body_rep])

    # Beam
    beam = ifc.create_entity(
        "IfcBeam",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner_history,
        Name=data.name,
        ObjectPlacement=ifc.create_entity(
            "IfcLocalPlacement",
            PlacementRelTo=storey.ObjectPlacement,
            RelativePlacement=axis2placement3d,
        ),
        Representation=shape,
    )

    ifc.create_entity(
        "IfcRelContainedInSpatialStructure",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner_history,
        RelatingStructure=storey,
        RelatedElements=[beam],
    )

    output_path = create_ifc_file_path()
    ifc.write(output_path)
    return output_path


def create_rel_aggregates_relation(ifc, owner_history, project, site):
    ifc.create_entity("IfcRelAggregates", GlobalId=ifcopenshell.guid.new(), OwnerHistory=owner_history,
                      RelatingObject=project, RelatedObjects=[site])


def create_storey(building, ifc, owner_history):
    # Storey placement relative to Building
    storey_placement = create_local_placement_and_relations(building.ObjectPlacement, ifc)
    storey = ifc.create_entity(
        "IfcBuildingStorey",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner_history,
        Name="Storey",
        ObjectPlacement=storey_placement
    )
    return storey


def create_local_placement_and_relations(object_placement, ifc):
    # https://standards.buildingsmart.org/IFC/DEV/IFC4_2/FINAL/HTML/schema/ifcgeometricconstraintresource/lexical/ifclocalplacement.htm
    storey_placement = ifc.create_entity(
        "IfcLocalPlacement",
        PlacementRelTo=object_placement,
        RelativePlacement=ifc.create_entity("IfcAxis2Placement3D",
                                            Location=ifc.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0))
                                            )
    )
    return storey_placement


def create_building(ifc, owner_history, site):
    # Building placement relative to Site
    building_placement = create_local_placement_and_relations(site.ObjectPlacement, ifc)

    building = ifc.create_entity(
        "IfcBuilding",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner_history,
        Name="Building",
        ObjectPlacement=building_placement
    )
    return building


def create_site(ifc, owner_history, world_coordinate_system):
    site_placement = ifc.create_entity(
        "IfcLocalPlacement",
        PlacementRelTo=None,
        RelativePlacement=world_coordinate_system
    )
    site = ifc.create_entity(
        "IfcSite",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner_history,
        Name="Site",
        ObjectPlacement=site_placement
    )
    return site


def create_true_north(ifc):
    true_north = ifc.create_entity("IfcDirection", DirectionRatios=(0.0, 1.0))
    return true_north


def def_create_owner_history(ifc):
    import time
    creation_date_time = int(time.time())
    person = ifc.create_entity("IfcPerson", FamilyName="Brunner", GivenName="Michael")
    organization = ifc.create_entity("IfcOrganization", Identification="", Name="Brunner246", Description="Brunner246")
    person_and_organization = ifc.create_entity("IfcPersonAndOrganization", ThePerson=person,
                                                TheOrganization=organization)
    organization = ifc.create_entity("IfcOrganization", Name="Brunner246")
    owning_application = ifc.create_entity("IfcApplication", ApplicationDeveloper=organization, Version="0.1.0",
                                           ApplicationFullName="IfcCreator", ApplicationIdentifier="ABC123")
    creation_date = ifc.create_entity("IfcTimeStamp", creation_date_time)
    owner_history = ifc.create_entity("IfcOwnerHistory", OwningUser=person_and_organization,
                                      OwningApplication=owning_application, CreationDate=creation_date_time,)
    return owner_history
