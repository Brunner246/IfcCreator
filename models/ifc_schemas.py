# models/ifc_schemas.py
from pydantic import BaseModel
from typing import List

class Point3D(BaseModel):
    x: float
    y: float
    z: float

from pydantic import BaseModel

class IfcBeamCreateRequest(BaseModel):
    name: str
    length: float
    width: float
    height: float

