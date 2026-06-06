from datetime import datetime

import mongomock
import pytest

import app.db as db_module
from config import TestConfig


@pytest.fixture
def client(monkeypatch):
    # Make the app factory build an in-memory Mongo instead of a real one.
    monkeypatch.setattr(db_module, "MongoClient", mongomock.MongoClient)
    db_module._client = None
    db_module._db = None

    from app import create_app
    app = create_app(TestConfig)

    # Seed a few documents covering the filter/sort cases.
    db_module.movies_collection().insert_many([
        {"title": "Alpha", "original_language": "en", "year": 1999,
         "release_date": datetime(1999, 5, 1), "vote_average": 8.1,
         "languages": ["English"]},
        {"title": "Beta", "original_language": "fr", "year": 2005,
         "release_date": datetime(2005, 3, 2), "vote_average": 6.4,
         "languages": ["Français"]},
        {"title": "Gamma", "original_language": "en", "year": 2005,
         "release_date": datetime(2005, 8, 9), "vote_average": 7.2,
         "languages": ["English"]},
    ])
    return app.test_client()


def test_health(client):
    assert client.get("/health").status_code == 200


def test_list_returns_envelope(client):
    body = client.get("/api/v1/movies").get_json()
    assert "data" in body and "pagination" in body
    assert body["pagination"]["total"] == 3


def test_filter_by_language(client):
    body = client.get("/api/v1/movies?language=en").get_json()
    assert body["pagination"]["total"] == 2
    assert all(m["original_language"] == "en" for m in body["data"])


def test_filter_by_year(client):
    body = client.get("/api/v1/movies?year=2005").get_json()
    assert body["pagination"]["total"] == 2


def test_sort_by_rating_desc(client):
    body = client.get("/api/v1/movies?sort=ratings&order=desc").get_json()
    ratings = [m["vote_average"] for m in body["data"]]
    assert ratings == sorted(ratings, reverse=True)


def test_invalid_sort_field_is_400(client):
    resp = client.get("/api/v1/movies?sort=budget")
    assert resp.status_code == 400
    assert resp.get_json()["error"]["code"] == "BAD_REQUEST"


def test_pagination(client):
    body = client.get("/api/v1/movies?limit=2&page=1").get_json()
    assert len(body["data"]) == 2
    assert body["pagination"]["has_next"] is True