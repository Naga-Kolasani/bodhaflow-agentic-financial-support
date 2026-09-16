from fastapi.testclient import TestClient

from bodhaflow.main import create_app


def test_openapi_schema_metadata() -> None:
    client = TestClient(create_app())

    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "BodhaFlow"
    assert schema["info"]["version"] == "0.1.0"
    assert schema["info"]["description"] == (
        "BodhaFlow is a fictional, policy-grounded financial support "
        "platform built with synthetic data and mock tools only."
    )
    assert schema["tags"] == [
        {"name": "System", "description": "System health and operational endpoints."}
    ]
    assert schema["paths"]["/health"]["get"]["tags"] == ["System"]
