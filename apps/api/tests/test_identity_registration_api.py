from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.identity.security import token_digest
from app.main import app
from app.models.base import Base
from app.models.identity import Account, AccountStatus, EmailVerificationToken, PasswordCredential


def build_client(monkeypatch):
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
    monkeypatch.setattr("app.api.auth.settings", SimpleNamespace(email_delivery_configured=True))
    sent = []

    def fake_send(recipient, token):
        sent.append((recipient, token))

    monkeypatch.setattr("app.api.auth.send_verification_email", fake_send)
    return TestClient(app), engine, sent


def teardown(client, engine):
    app.dependency_overrides.clear()
    client.close()
    engine.dispose()


def test_registration_creates_pending_account_and_sends_single_use_token(monkeypatch):
    client, engine, sent = build_client(monkeypatch)
    try:
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "Person@Example.com", "password": "a-long-test-password"},
            headers={"Origin": "http://localhost:5173"},
        )
        assert response.status_code == 202
        assert sent and sent[0][0] == "person@example.com"
        with Session(engine) as db:
            account = db.scalar(select(Account))
            credential = db.scalar(select(PasswordCredential))
            token = db.scalar(select(EmailVerificationToken))
            assert account.status == AccountStatus.PENDING_EMAIL
            assert credential.password_hash != "a-long-test-password"
            assert token.token_hash == token_digest(sent[0][1])
            assert token.expires_at - token.created_at == timedelta(hours=24)
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "person@example.com", "password": "a-long-test-password"},
            headers={"Origin": "http://localhost:5173"},
        )
        assert login.status_code == 401
    finally:
        teardown(client, engine)


def test_email_verification_activates_account_and_token_cannot_be_reused(monkeypatch):
    client, engine, sent = build_client(monkeypatch)
    try:
        client.post(
            "/api/v1/auth/register",
            json={"email": "person@example.com", "password": "a-long-test-password"},
            headers={"Origin": "http://localhost:5173"},
        )
        token = sent[0][1]
        verified = client.post(
            "/api/v1/auth/email-verification/verify",
            json={"token": token},
            headers={"Origin": "http://localhost:5173"},
        )
        assert verified.status_code == 200
        with Session(engine) as db:
            assert db.scalar(select(Account)).status == AccountStatus.ACTIVE
        reused = client.post(
            "/api/v1/auth/email-verification/verify",
            json={"token": token},
            headers={"Origin": "http://localhost:5173"},
        )
        assert reused.status_code == 400
    finally:
        teardown(client, engine)


def test_expired_verification_token_is_rejected(monkeypatch):
    client, engine, sent = build_client(monkeypatch)
    try:
        client.post(
            "/api/v1/auth/register",
            json={"email": "person@example.com", "password": "a-long-test-password"},
            headers={"Origin": "http://localhost:5173"},
        )
        with Session(engine) as db:
            token_row = db.scalar(select(EmailVerificationToken))
            token_row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
            db.commit()
        response = client.post(
            "/api/v1/auth/email-verification/verify",
            json={"token": sent[0][1]},
            headers={"Origin": "http://localhost:5173"},
        )
        assert response.status_code == 400
    finally:
        teardown(client, engine)


def test_resend_invalidates_previous_token(monkeypatch):
    client, engine, sent = build_client(monkeypatch)
    try:
        client.post(
            "/api/v1/auth/register",
            json={"email": "person@example.com", "password": "a-long-test-password"},
            headers={"Origin": "http://localhost:5173"},
        )
        client.post(
            "/api/v1/auth/email-verification/resend",
            json={"email": "person@example.com"},
            headers={"Origin": "http://localhost:5173"},
        )
        assert len(sent) == 2
        old_token = client.post(
            "/api/v1/auth/email-verification/verify",
            json={"token": sent[0][1]},
            headers={"Origin": "http://localhost:5173"},
        )
        assert old_token.status_code == 400
        new_token = client.post(
            "/api/v1/auth/email-verification/verify",
            json={"token": sent[1][1]},
            headers={"Origin": "http://localhost:5173"},
        )
        assert new_token.status_code == 200
    finally:
        teardown(client, engine)


def test_registration_rejects_untrusted_origin(monkeypatch):
    client, engine, _ = build_client(monkeypatch)
    try:
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "person@example.com", "password": "a-long-test-password"},
            headers={"Origin": "https://attacker.example"},
        )
        assert response.status_code == 403
    finally:
        teardown(client, engine)
