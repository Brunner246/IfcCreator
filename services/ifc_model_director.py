from services.ifc_model_manager import IfcModelManager
from services.strategies.model_strategy import IfcModelStrategy


class IfcModelDirector:

    def __init__(self, model_manager: IfcModelManager):
        self.model_manager = model_manager  # or IfcModelManager()

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
