import pytest
from app.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_home_page(client):
    """Test that home page loads successfully"""
    rv = client.get("/")
    assert rv.status_code == 200


def test_hello_api(client):
    """Test the hello API endpoint"""
    rv = client.get("/api/hello")
    json_data = rv.get_json()
    assert rv.status_code == 200
    assert json_data["message"] == "Hello, World!"
    assert json_data["status"] == "success"


def test_greet_api(client):
    """Test the greet API endpoint with different names"""
    test_names = ["Alice", "Bob", "Charlie"]

    for name in test_names:
        rv = client.get(f"/api/greet/{name}")
        json_data = rv.get_json()
        assert rv.status_code == 200
        assert json_data["message"] == f"Hello, {name}!"
        assert json_data["status"] == "success"


@pytest.mark.parametrize("invalid_path", ["/api/invalid", "/api/greet", "/nonexistent"])
def test_invalid_routes(client, invalid_path):
    """Test handling of invalid routes"""
    rv = client.get(invalid_path)
    assert rv.status_code == 404
