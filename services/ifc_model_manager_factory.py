from core.cartesian_point import CartesianPoint
from models.dto.beam_dto import BeamDTO
from models.dto.building_element_dto import BuildingElementDTO
from models.ifc_schemas import IfcBeamCreateRequest
from services.ifc_model_manager import IfcModelManager
from services.strategies.beam_creator import IfcBeamCreator
from services.strategies.ifc2x3_strategy import IFC2X3Strategy
from services.strategies.ifc4_strategy import IFC4Strategy
from services.strategies.ifc4x3_strategy import IFC4X3Strategy
import copy


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

    beam_data1 = BeamDTO(
        building_element=BuildingElementDTO(
            name="beam",
            location=CartesianPoint(2.0, 0.0, 0.5)
        ),
        width=data.width,
        height=data.height,
        length=data.length)

    beam_data2 = copy.deepcopy(beam_data1)
    beam_data2.building_element.location = CartesianPoint(2.5, 0.0, 0.5)

    beam_entity = IfcBeamCreator(beam_data1)
    beam_entity2 = IfcBeamCreator(beam_data2)

    (manager
     .create_file()
     .initialize_model()
     .add_building_element(beam_entity)
     .add_building_element(beam_entity2)
     # .add_beam(data)
     )

    return manager.save()
