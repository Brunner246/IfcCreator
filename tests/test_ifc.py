import pytest


@pytest.fixture
def setup_beam_request():
    from models.ifc_schemas import IfcBeamCreateRequest
    return IfcBeamCreateRequest(
        name="TestBeam",
        length=5,
        width=0.200,
        height=0.400
    )


def test_test():
    assert True


def test_ifc_creation(setup_beam_request):
    # from services.ifc_creator import create_ifc_file
    from services.ifc_model_manager_factory import create_ifc_file

    model = create_ifc_file(setup_beam_request)
    assert model is not None
    # assert len(model.by_type("IfcBeam")) == 1
