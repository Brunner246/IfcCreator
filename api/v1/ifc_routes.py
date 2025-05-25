from fastapi import APIRouter, Response

from models.ifc_schemas import IfcBeamCreateRequest
from services.ifc_creator import create_ifc_file

router = APIRouter()


@router.post("/create_ifc_beam")
async def create_ifc_beam(data: IfcBeamCreateRequest):
    path = create_ifc_file(data)
    with open(path, "rb") as f:
        return Response(content=f.read(), media_type="application/octet-stream",
                        headers={"Content-Disposition": f"attachment; filename=beam.ifc"})
