# models/ifc_schemas.py
from pydantic import BaseModel
from typing import List


class Point3D(BaseModel):
    x: float
    y: float
    z: float


class IfcBeamCreateRequest(BaseModel):
    name: str
    length: float
    width: float
    height: float
