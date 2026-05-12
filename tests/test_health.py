import pytest
from app import create_app


@pytest.fixture()
def client():
    app = create_app("development")
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.app_context():
        from app.extensions import db
        db.create_all()
        yield app.test_client()


def test_health_returns_200(client):
    res = client.get("/api/health")
    assert res.status_code == 200


def test_health_shape(client):
    data = client.get("/api/health").get_json()
    assert data["status"] == "ok"
    assert "price" in data["models"]
    assert "energy" in data["models"]
