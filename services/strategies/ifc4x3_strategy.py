from services.strategies.model_strategy import IfcModelStrategy


class IFC4X3Strategy(IfcModelStrategy):
    """IFC4X3 implementation strategy"""

    def get_schema(self) -> str:
        return "IFC4X3"

    def create_specific_entities(self, model_manager: 'IfcModelManager') -> None: pass
