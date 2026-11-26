import os

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.identity.security import hash_password
from app.main import app
from app.models.base import Base
from app.models.identity import Account, AccountStatus, PasswordCredential


def build_client():
    database_url = os.getenv("IDENTITY_TEST_DATABASE_URL")
    if database_url:
        engine = create_engine(database_url, pool_pre_ping=True)
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
    else:
        engine = create_engine(
            "sqlite+pysqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(engine)

    def override_get_db():
        with Session(engine, expire_on_commit=False) as db:
            try:
                yield db
                db.commit()
            except Exception:
                db.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), engine


def seed_account(engine, email: str) -> None:
    with Session(engine) as db:
        account = Account(email_normalized=email, status=AccountStatus.ACTIVE)
        db.add(account)
        db.flush()
        db.add(PasswordCredential(account_id=account.id, password_hash=hash_password("a-long-test-password")))
        db.commit()


def login(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "a-long-test-password"},
        headers={"Origin": "http://localhost:5173"},
    )
    assert response.status_code == 200
    return response.json()["csrf_token"]


def teardown(client: TestClient, engine) -> None:
    app.dependency_overrides.clear()
    client.close()
    engine.dispose()


def test_profile_is_private_and_requires_authentication():
    client, engine = build_client()
    try:
        response = client.get("/api/v1/profile/me")
        assert response.status_code == 401
        assert response.headers["cache-control"] == "no-store"
    finally:
        teardown(client, engine)


def test_owner_can_read_empty_profile_without_creating_profile_record():
    client, engine = build_client()
    try:
        seed_account(engine, "owner@example.com")
        login(client, "owner@example.com")

        response = client.get("/api/v1/profile/me")
        assert response.status_code == 200
        body = response.json()
        assert body["display_name"] is None
        assert body["username"] is None
        assert body["bio"] is None
        assert body["avatar_url"] is None
        assert body["community_unit"] is None
        assert body["account_created_at"]
        assert response.headers["cache-control"] == "no-store"
        assert response.headers["vary"] == "Cookie"

        from app.models.profile import UserProfile

        with Session(engine) as db:
            assert db.scalar(select(UserProfile)) is None
    finally:
        teardown(client, engine)


def test_owner_can_update_profile_with_csrf_and_values_are_normalized():
    client, engine = build_client()
    try:
        seed_account(engine, "owner@example.com")
        csrf = login(client, "owner@example.com")
        response = client.patch(
            "/api/v1/profile/me",
            json={"display_name": "  Gabriel   Miranda ", "username": "@Gabriel_011", "bio": "  Hola   comunidad  "},
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": csrf},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["display_name"] == "Gabriel Miranda"
        assert body["username"] == "gabriel_011"
        assert body["bio"] == "Hola comunidad"
        assert body["community_unit"] is None

        fetched = client.get("/api/v1/profile/me")
        assert fetched.status_code == 200
        assert fetched.json()["username"] == "gabriel_011"
    finally:
        teardown(client, engine)


def test_profile_update_rejects_missing_csrf_token():
    client, engine = build_client()
    try:
        seed_account(engine, "owner@example.com")
        login(client, "owner@example.com")
        response = client.patch(
            "/api/v1/profile/me",
            json={"display_name": "Gabriel"},
            headers={"Origin": "http://localhost:5173"},
        )
        assert response.status_code == 403
    finally:
        teardown(client, engine)


def test_profile_username_must_be_unique_and_is_not_case_sensitive():
    client, engine = build_client()
    try:
        seed_account(engine, "first@example.com")
        seed_account(engine, "second@example.com")

        first_csrf = login(client, "first@example.com")
        first = client.patch(
            "/api/v1/profile/me",
            json={"username": "Community_User"},
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": first_csrf},
        )
        assert first.status_code == 200

        client.post(
            "/api/v1/auth/logout",
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": first_csrf},
        )
        second_csrf = login(client, "second@example.com")
        second = client.patch(
            "/api/v1/profile/me",
            json={"username": "community_user"},
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": second_csrf},
        )
        assert second.status_code == 409
    finally:
        teardown(client, engine)


def test_profile_update_rejects_invalid_or_unexpected_fields():
    client, engine = build_client()
    try:
        seed_account(engine, "owner@example.com")
        csrf = login(client, "owner@example.com")
        headers = {"Origin": "http://localhost:5173", "X-CSRF-Token": csrf}

        invalid_username = client.patch(
            "/api/v1/profile/me",
            json={"username": "bad username"},
            headers=headers,
        )
        assert invalid_username.status_code == 422

        unexpected = client.patch(
            "/api/v1/profile/me",
            json={"email": "attacker@example.com"},
            headers=headers,
        )
        assert unexpected.status_code == 422

        empty = client.patch("/api/v1/profile/me", json={}, headers=headers)
        assert empty.status_code == 422
    finally:
        teardown(client, engine)


def test_profile_api_does_not_expose_lookup_routes_for_other_users():
    client, engine = build_client()
    try:
        seed_account(engine, "owner@example.com")
        login(client, "owner@example.com")
        assert client.get("/api/v1/profile/some-other-id").status_code == 404
        assert client.get("/api/v1/profiles").status_code == 404
    finally:
        teardown(client, engine)
