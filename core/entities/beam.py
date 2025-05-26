from core.entities.building_element import BuildingElement


class Beam(BuildingElement):
    def __init__(self, guid: str, name: str, length: float, width: float, height: float):
        super().__init__(guid, name)
        self.length = length
        self.width = width
        self.height = height
        self.validate()

    def validate(self):
        """Enforce domain rules for beams"""
        if self.length <= 0 or self.width <= 0 or self.height <= 0:
            raise ValueError("Beam dimensions must be positive")
