from fastapi import FastAPI
from api.v1 import ifc_routes
app = FastAPI(title="IFC Creator API")


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


app.include_router(ifc_routes.router, prefix="/api/v1")
