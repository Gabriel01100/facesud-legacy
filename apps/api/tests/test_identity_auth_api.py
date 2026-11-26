import os

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.identity.security import hash_password
from app.main import app
from app.models.base import Base
from app.models.identity import Account, AccountStatus, PasswordCredential, UserSession


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
    client = TestClient(app)
    return client, engine


def seed_account(engine, *, status=AccountStatus.ACTIVE):
    with Session(engine) as db:
        account = Account(email_normalized="person@example.com", status=status)
        db.add(account)
        db.flush()
        db.add(PasswordCredential(account_id=account.id, password_hash=hash_password("a-long-test-password")))
        db.commit()
        return account.id


def teardown_client(client, engine):
    app.dependency_overrides.clear()
    client.close()
    engine.dispose()


def test_login_sets_httponly_session_cookie_and_me_returns_account():
    client, engine = build_client()
    try:
        seed_account(engine)
        response = client.post(
            "/api/v1/auth/login",
            json={"email": " Person@Example.com ", "password": "a-long-test-password"},
            headers={"Origin": "http://localhost:5173"},
        )
        assert response.status_code == 200
        assert response.json()["email"] == "person@example.com"
        cookies = response.headers.get_list("set-cookie")
        assert any("facesud_session=" in item and "HttpOnly" in item for item in cookies)
        assert all("facesud_csrf=" not in item for item in cookies)
        assert response.json()["csrf_token"]
        assert response.headers["cache-control"] == "no-store"

        me = client.get("/api/v1/auth/me")
        assert me.status_code == 200
        assert me.json()["email"] == "person@example.com"
    finally:
        teardown_client(client, engine)


def test_successful_new_login_revokes_the_incoming_session():
    client, engine = build_client()
    try:
        seed_account(engine)
        first = client.post(
            "/api/v1/auth/login",
            json={"email": "person@example.com", "password": "a-long-test-password"},
            headers={"Origin": "http://localhost:5173"},
        )
        first_token = client.cookies.get("facesud_session")
        second = client.post(
            "/api/v1/auth/login",
            json={"email": "person@example.com", "password": "a-long-test-password"},
            headers={"Origin": "http://localhost:5173"},
        )
        assert first.status_code == second.status_code == 200
        with Session(engine) as db:
            sessions = list(db.scalars(select(UserSession).order_by(UserSession.created_at)))
            assert len(sessions) == 2
            assert sum(session.revoked_at is not None for session in sessions) == 1
            assert sum(session.revoked_at is None for session in sessions) == 1
        assert client.get("/api/v1/auth/me").status_code == 200
        assert first_token
    finally:
        teardown_client(client, engine)


def test_login_rate_limit_returns_429_after_five_attempts(monkeypatch):
    client, engine = build_client()
    try:
        monkeypatch.setattr("app.api.auth.authenticate_local_account", lambda *_args: None)
        headers = {"Origin": "http://localhost:5173"}
        for _ in range(5):
            response = client.post(
                "/api/v1/auth/login",
                json={"email": "person@example.com", "password": "wrong-password"},
                headers=headers,
            )
            assert response.status_code == 401
        limited = client.post(
            "/api/v1/auth/login",
            json={"email": "person@example.com", "password": "wrong-password"},
            headers=headers,
        )
        assert limited.status_code == 429
        assert int(limited.headers["retry-after"]) > 0
        assert limited.headers["cache-control"] == "no-store"
    finally:
        teardown_client(client, engine)


def test_login_rejects_inactive_account_and_invalid_credentials_generically():
    client, engine = build_client()
    try:
        seed_account(engine, status=AccountStatus.PENDING_EMAIL)
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "person@example.com", "password": "a-long-test-password"},
            headers={"Origin": "http://localhost:5173"},
        )
        assert response.status_code == 401
        assert response.headers["cache-control"] == "no-store"
        assert response.json()["detail"] == "Email or password is incorrect, or the account is not active."
    finally:
        teardown_client(client, engine)


def test_login_rejects_untrusted_origin():
    client, engine = build_client()
    try:
        seed_account(engine)
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "person@example.com", "password": "a-long-test-password"},
            headers={"Origin": "https://attacker.example"},
        )
        assert response.status_code == 403
    finally:
        teardown_client(client, engine)


def test_logout_requires_csrf_and_revokes_session():
    client, engine = build_client()
    try:
        seed_account(engine)
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "person@example.com", "password": "a-long-test-password"},
            headers={"Origin": "http://localhost:5173"},
        )
        assert login.status_code == 200

        with Session(engine) as db:
            last_seen_before = db.scalar(select(UserSession)).last_seen_at

        rejected = client.post(
            "/api/v1/auth/logout",
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": "wrong"},
        )
        assert rejected.status_code == 403
        with Session(engine) as db:
            last_seen_after = db.scalar(select(UserSession)).last_seen_at
        assert last_seen_after == last_seen_before
        assert client.get("/api/v1/auth/me").status_code == 200

        csrf = client.post(
            "/api/v1/auth/csrf",
            headers={"Origin": "http://localhost:5173"},
        ).json()["csrf_token"]
        logged_out = client.post(
            "/api/v1/auth/logout",
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": csrf},
        )
        assert logged_out.status_code == 204
        assert client.get("/api/v1/auth/me").status_code == 401
    finally:
        teardown_client(client, engine)


def test_logout_with_expired_session_still_returns_204_and_clears_cookie():
    from datetime import datetime, timedelta, timezone

    client, engine = build_client()
    try:
        seed_account(engine)
        client.post(
            "/api/v1/auth/login",
            json={"email": "person@example.com", "password": "a-long-test-password"},
            headers={"Origin": "http://localhost:5173"},
        )
        with Session(engine) as db:
            session = db.scalar(select(UserSession))
            session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
            db.commit()

        response = client.post("/api/v1/auth/logout", headers={"Origin": "http://localhost:5173"})
        assert response.status_code == 204
        assert any("facesud_session=" in item and "Max-Age=0" in item for item in response.headers.get_list("set-cookie"))
    finally:
        teardown_client(client, engine)


def test_me_requires_authentication_and_does_not_cache_401():
    client, engine = build_client()
    try:
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
        assert response.headers["cache-control"] == "no-store"
    finally:
        teardown_client(client, engine)


def test_authenticated_password_change_requires_csrf_and_revokes_all_sessions():
    client, engine = build_client()
    try:
        seed_account(engine)
        headers = {"Origin": "http://localhost:5173"}
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "person@example.com", "password": "a-long-test-password"},
            headers=headers,
        )
        assert login.status_code == 200
        csrf_token = login.json()["csrf_token"]

        rejected = client.post(
            "/api/v1/auth/password/change",
            json={"current_password": "a-long-test-password", "new_password": "a-new-long-password"},
            headers=headers,
        )
        assert rejected.status_code == 403

        changed = client.post(
            "/api/v1/auth/password/change",
            json={"current_password": "a-long-test-password", "new_password": "a-new-long-password"},
            headers={**headers, "X-CSRF-Token": csrf_token},
        )
        assert changed.status_code == 204
        assert client.get("/api/v1/auth/me").status_code == 401

        old_login = client.post(
            "/api/v1/auth/login",
            json={"email": "person@example.com", "password": "a-long-test-password"},
            headers=headers,
        )
        new_login = client.post(
            "/api/v1/auth/login",
            json={"email": "person@example.com", "password": "a-new-long-password"},
            headers=headers,
        )
        assert old_login.status_code == 401
        assert new_login.status_code == 200
    finally:
        teardown_client(client, engine)
