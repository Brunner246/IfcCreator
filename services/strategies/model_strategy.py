from abc import ABC, abstractmethod


class IfcModelStrategy(ABC):

    @abstractmethod
    def get_schema(self) -> str: pass

    @abstractmethod
    def create_specific_entities(self, model_manager: 'IfcModelManager') -> None: pass