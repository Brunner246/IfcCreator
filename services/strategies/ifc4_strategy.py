from services.strategies.model_strategy import IfcModelStrategy


class IFC4Strategy(IfcModelStrategy):
    """IFC4 implementation strategy"""

    def get_schema(self) -> str:
        return "IFC4"

    def create_specific_entities(self, model_manager: 'IfcModelManager') -> None: pass
