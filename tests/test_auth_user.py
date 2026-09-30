"""Tests for role-based User login (public /api/login + /api/session + logout)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

import backend.database.init_db as init_db_mod
from backend.database import init_db
from backend.database.seed_reference_data import seed

_ORIGINAL_DB = init_db_mod.DATABASE_PATH


@pytest.fixture(scope="session")
def client(tmp_path_factory):
    db = str(tmp_path_factory.mktemp("auth_user") / "auth_user_test.db")
    init_db_mod.DATABASE_PATH = db
    init_db.init_db(db)
    seed(db_path=db)

    from backend.app import create_app
    app = create_app({"TESTING": True})
    with app.test_client() as c:
        yield c
    init_db_mod.DATABASE_PATH = _ORIGINAL_DB


def test_user_can_log_in_and_receive_a_bearer_token(client):
    res = client.post("/api/login", json={"username": "tce_user", "password": "tce2026"})
    assert res.status_code == 200
    body = res.get_json()
    assert body["role"] == "user"
    assert body["username"] == "tce_user"
    assert body["token"]

    session = client.get("/api/session", headers={"Authorization": f"Bearer {body['token']}"})
    assert session.get_json() == {"authenticated": True, "username": "tce_user", "role": "user"}


def test_admin_credentials_are_recognised_by_the_unified_login(client):
    res = client.post("/api/login", json={"username": "shalini", "password": "shalini02"})
    assert res.status_code == 200
    body = res.get_json()
    assert body["role"] == "admin"
    assert body["token"]


def test_any_other_credentials_sign_in_as_a_standard_user(client):
    for payload in (
        {"username": "tce_user", "password": "wrong-password"},
        {"username": "no_such_user", "password": "anything"},
    ):
        res = client.post("/api/login", json=payload)
        assert res.status_code == 200
        body = res.get_json()
        assert body["role"] == "user"
        assert body["username"] == payload["username"]
        assert body["token"]


def test_login_requires_both_fields(client):
    assert client.post("/api/login", json={"username": "tce_user"}).status_code == 400
    assert client.post("/api/login", json={"password": "tce2026"}).status_code == 400
    assert client.post("/api/login", json={}).status_code == 400


def test_session_is_unauthenticated_without_a_token(client):
    body = client.get("/api/session").get_json()
    assert body == {"authenticated": False}


def test_user_token_cannot_access_admin_routes(client):
    user = client.post("/api/login", json={"username": "tce_user", "password": "tce2026"}).get_json()
    headers = {"Authorization": f"Bearer {user['token']}"}
    assert client.get("/api/admin/overview", headers=headers).status_code == 401
    assert client.get("/api/admin/activities", headers=headers).status_code == 401
    assert client.get("/api/admin/activities/1", headers=headers).status_code == 401


def test_logout_revokes_the_token(client):
    user = client.post("/api/login", json={"username": "tce_user", "password": "tce2026"}).get_json()
    headers = {"Authorization": f"Bearer {user['token']}"}
    res = client.post("/api/logout", headers=headers)
    assert res.status_code == 200
    assert client.get("/api/session", headers=headers).get_json() == {"authenticated": False}


def test_admin_login_alias_still_works(client):
    res = client.post("/api/admin/login", json={"username": "shalini", "password": "shalini02"})
    assert res.status_code == 200
    assert res.get_json()["token"]