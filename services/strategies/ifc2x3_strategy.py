from services.strategies.model_strategy import IfcModelStrategy


class IFC2X3Strategy(IfcModelStrategy):
    """IFC2X3 implementation strategy"""

    def get_schema(self) -> str:
        return "IFC2X3"

    def create_specific_entities(self, model_manager: 'IfcModelManager') -> None: pass
