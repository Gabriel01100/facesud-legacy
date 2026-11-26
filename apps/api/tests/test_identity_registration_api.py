import os
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
    monkeypatch.setattr("app.api.auth.settings", SimpleNamespace(email_delivery_configured=True, session_cookie_name="facesud_session", secure_cookies=False))
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



def test_registration_rolls_back_pending_account_when_email_delivery_fails(monkeypatch):
    client, engine, _ = build_client(monkeypatch)

    def fail_delivery(recipient, token):
        from app.identity.email import EmailDeliveryError

        raise EmailDeliveryError("SMTP unavailable")

    monkeypatch.setattr("app.api.auth.send_verification_email", fail_delivery)
    try:
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "person@example.com", "password": "a-long-test-password"},
            headers={"Origin": "http://localhost:5173"},
        )
        assert response.status_code == 503
        with Session(engine) as db:
            assert db.scalar(select(Account)) is None
            assert db.scalar(select(EmailVerificationToken)) is None
    finally:
        teardown(client, engine)


def test_failed_resend_keeps_the_previous_verification_token_valid(monkeypatch):
    client, engine, sent = build_client(monkeypatch)
    try:
        headers = {"Origin": "http://localhost:5173"}
        registered = client.post(
            "/api/v1/auth/register",
            json={"email": "person@example.com", "password": "a-long-test-password"},
            headers=headers,
        )
        assert registered.status_code == 202
        original_token = sent[0][1]

        def fail_delivery(recipient, token):
            from app.identity.email import EmailDeliveryError

            raise EmailDeliveryError("SMTP unavailable")

        monkeypatch.setattr("app.api.auth.send_verification_email", fail_delivery)
        resent = client.post(
            "/api/v1/auth/email-verification/resend",
            json={"email": "person@example.com"},
            headers=headers,
        )
        assert resent.status_code == 202

        still_valid = client.post(
            "/api/v1/auth/email-verification/verify",
            json={"token": original_token},
            headers=headers,
        )
        assert still_valid.status_code == 200
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


def test_registration_is_rate_limited_without_disclosing_account_state(monkeypatch):
    client, engine, _ = build_client(monkeypatch)
    try:
        headers = {"Origin": "http://localhost:5173"}
        payload = {"email": "person@example.com", "password": "a-long-test-password"}
        first = client.post("/api/v1/auth/register", json=payload, headers=headers)
        second = client.post("/api/v1/auth/register", json=payload, headers=headers)
        limited = client.post("/api/v1/auth/register", json=payload, headers=headers)

        assert first.status_code == 202
        assert second.status_code == 202
        assert first.json() == second.json()
        assert limited.status_code == 429
        assert int(limited.headers["Retry-After"]) > 0
    finally:
        teardown(client, engine)


def test_verification_resend_is_rate_limited(monkeypatch):
    client, engine, _ = build_client(monkeypatch)
    try:
        headers = {"Origin": "http://localhost:5173"}
        payload = {"email": "person@example.com"}
        responses = [
            client.post("/api/v1/auth/email-verification/resend", json=payload, headers=headers)
            for _ in range(4)
        ]

        assert [response.status_code for response in responses[:3]] == [202, 202, 202]
        assert responses[0].json() == responses[1].json() == responses[2].json()
        assert responses[3].status_code == 429
        assert int(responses[3].headers["Retry-After"]) > 0
    finally:
        teardown(client, engine)


def test_password_reset_is_generic_single_use_and_revokes_existing_sessions(monkeypatch):
    client, engine, verification_emails = build_client(monkeypatch)
    reset_emails = []
    monkeypatch.setattr("app.api.auth.send_password_reset_email", lambda recipient, token: reset_emails.append((recipient, token)))
    try:
        headers = {"Origin": "http://localhost:5173"}
        registered = client.post(
            "/api/v1/auth/register",
            json={"email": "person@example.com", "password": "a-long-test-password"},
            headers=headers,
        )
        assert registered.status_code == 202
        verified = client.post(
            "/api/v1/auth/email-verification/verify",
            json={"token": verification_emails[0][1]},
            headers=headers,
        )
        assert verified.status_code == 200
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "person@example.com", "password": "a-long-test-password"},
            headers=headers,
        )
        assert login.status_code == 200

        request_reset = client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": "person@example.com"},
            headers=headers,
        )
        unknown_reset = client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": "missing@example.com"},
            headers=headers,
        )
        assert request_reset.status_code == unknown_reset.status_code == 202
        assert request_reset.json() == unknown_reset.json()
        assert len(reset_emails) == 1

        reset = client.post(
            "/api/v1/auth/password-reset/confirm",
            json={"token": reset_emails[0][1], "new_password": "a-new-long-password"},
            headers=headers,
        )
        assert reset.status_code == 200
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

        reused = client.post(
            "/api/v1/auth/password-reset/confirm",
            json={"token": reset_emails[0][1], "new_password": "another-new-password"},
            headers=headers,
        )
        assert reused.status_code == 400
    finally:
        teardown(client, engine)


def test_password_reset_requests_are_rate_limited(monkeypatch):
    client, engine, _ = build_client(monkeypatch)
    try:
        headers = {"Origin": "http://localhost:5173"}
        payload = {"email": "unknown@example.com"}
        responses = [
            client.post("/api/v1/auth/password-reset/request", json=payload, headers=headers)
            for _ in range(4)
        ]
        assert [response.status_code for response in responses[:3]] == [202, 202, 202]
        assert responses[0].json() == responses[1].json() == responses[2].json()
        assert responses[3].status_code == 429
        assert int(responses[3].headers["Retry-After"]) > 0
    finally:
        teardown(client, engine)
