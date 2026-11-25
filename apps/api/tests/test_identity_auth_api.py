from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.identity.security import hash_password
from app.main import app
from app.models.base import Base
from app.models.identity import Account, AccountStatus, PasswordCredential


def build_client():
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
        assert any("facesud_csrf=" in item and "HttpOnly" not in item for item in cookies)

        me = client.get("/api/v1/auth/me")
        assert me.status_code == 200
        assert me.json()["email"] == "person@example.com"
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

        csrf = client.cookies.get("facesud_csrf")
        rejected = client.post(
            "/api/v1/auth/logout",
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": "wrong"},
        )
        assert rejected.status_code == 403
        assert client.get("/api/v1/auth/me").status_code == 200

        logged_out = client.post(
            "/api/v1/auth/logout",
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": csrf},
        )
        assert logged_out.status_code == 204
        assert client.get("/api/v1/auth/me").status_code == 401
    finally:
        teardown_client(client, engine)


def test_me_requires_authentication():
    client, engine = build_client()
    try:
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
    finally:
        teardown_client(client, engine)
