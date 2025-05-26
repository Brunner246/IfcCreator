class BuildingElement:
    def __init__(self, guid: str, name: str):
        self._guid = guid
        self._name = name

        guid = property(fget=lambda self: self._guid)

        @property
        def name(self) -> str:
            return self._name
