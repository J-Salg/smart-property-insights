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


# Price API

def test_price_missing_body(client):
    res = client.post("/api/predict/price", content_type="application/json")
    assert res.status_code == 400


def test_price_missing_fields(client):
    res = client.post("/api/predict/price", json={"overall_qual": 7})
    assert res.status_code in (422, 503)


# Energy API

def test_energy_missing_body(client):
    res = client.post("/api/predict/energy", content_type="application/json")
    assert res.status_code == 400


def test_energy_missing_fields(client):
    res = client.post("/api/predict/energy", json={"relative_compactness": 0.98})
    assert res.status_code in (422, 503)
