import dataclasses
from typing import Iterator


@dataclasses.dataclass(slots=True)
class CartesianPoint:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __post_init__(self):
        if not isinstance(self.x, (int, float)):
            raise TypeError(f"x must be a number, got {type(self.x).__name__}")
        if not isinstance(self.y, (int, float)):
            raise TypeError(f"y must be a number, got {type(self.y).__name__}")
        if not isinstance(self.z, (int, float)):
            raise TypeError(f"z must be a number, got {type(self.z).__name__}")

    def __iter__(self) -> Iterator[float]:
        """Allow unpacking of CartesianPoint as (x, y, z)"""
        yield self.x
        yield self.y
        yield self.z
