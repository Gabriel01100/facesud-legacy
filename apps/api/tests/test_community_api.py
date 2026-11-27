import os

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import get_db
from app.identity.security import hash_password
from app.main import app
from app.models.base import Base
from app.models.community import UnitMembership
from app.models.identity import Account, AccountStatus, PasswordCredential


def build_clients():
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
    return TestClient(app), TestClient(app), engine


def seed_account(engine, email: str):
    with Session(engine) as db:
        account = Account(email_normalized=email, status=AccountStatus.ACTIVE)
        db.add(account)
        db.flush()
        db.add(PasswordCredential(account_id=account.id, password_hash=hash_password("a-long-test-password")))
        db.commit()
        return account.id


def login(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "a-long-test-password"},
        headers={"Origin": "http://localhost:5173"},
    )
    assert response.status_code == 200
    return response.json()["csrf_token"]


def cleanup(*clients, engine):
    app.dependency_overrides.clear()
    for client in clients:
        client.close()
    engine.dispose()


def test_community_requires_authentication_and_supports_request_review(monkeypatch):
    member, reviewer, engine = build_clients()
    try:
        member_id = seed_account(engine, "member@example.com")
        reviewer_id = seed_account(engine, "reviewer@example.com")
        monkeypatch.setattr(settings, "community_reviewer_emails", "reviewer@example.com")

        unauthenticated = member.get("/api/v1/community/membership/me")
        assert unauthenticated.status_code == 401
        assert unauthenticated.headers["cache-control"] == "no-store"

        reviewer_csrf = login(reviewer, "reviewer@example.com")
        unit_response = reviewer.post(
            "/api/v1/community/units",
            json={
                "name": "Rama Centro",
                "unit_type": "branch",
                "country_code": "AR",
                "locality": "San Juan Bautista",
                "administrative_area": "Buenos Aires",
            },
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": reviewer_csrf},
        )
        assert unit_response.status_code == 201
        unit_id = unit_response.json()["id"]

        member_csrf = login(member, "member@example.com")
        unauthorized_unit = member.post(
            "/api/v1/community/units",
            json={"name": "No autorizada", "unit_type": "branch", "country_code": "AR"},
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": member_csrf},
        )
        assert unauthorized_unit.status_code == 403

        request_response = member.post(
            "/api/v1/community/membership-requests",
            json={"unit_id": unit_id},
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": member_csrf},
        )
        assert request_response.status_code == 201
        assert request_response.json()["status"] == "pending"
        assert request_response.json()["provisional"] is True

        duplicate = member.post(
            "/api/v1/community/membership-requests",
            json={"unit_id": unit_id},
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": member_csrf},
        )
        assert duplicate.status_code == 409

        forbidden = member.get("/api/v1/community/review/requests")
        assert forbidden.status_code == 403

        queue = reviewer.get("/api/v1/community/review/requests")
        assert queue.status_code == 200
        assert len(queue.json()) == 1
        assert queue.json()[0]["account_reference"] == "member@example.com"

        decision = reviewer.post(
            f"/api/v1/community/review/requests/{request_response.json()['id']}",
            json={"decision": "approved", "note": "Vinculación revisada localmente."},
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": reviewer_csrf},
        )
        assert decision.status_code == 200
        assert decision.json()["status"] == "approved"
        assert decision.json()["provisional"] is True

        own = member.get("/api/v1/community/membership/me")
        assert own.status_code == 200
        assert own.json()[0]["status"] == "approved"

        profile = member.get("/api/v1/profile/me")
        assert profile.status_code == 200
        assert profile.json()["community_unit"] == {"name": "Rama Centro", "kind": "branch"}

        with Session(engine) as db:
            record = db.scalar(select(UnitMembership).where(UnitMembership.account_id == member_id))
            assert record is not None
            assert record.reviewer_account_id == reviewer_id
            assert record.review_note == "Vinculación revisada localmente."
    finally:
        cleanup(member, reviewer, engine=engine)


def test_community_rejects_requests_without_csrf():
    member, reviewer, engine = build_clients()
    try:
        seed_account(engine, "member@example.com")
        csrf = login(member, "member@example.com")
        response = member.post(
            "/api/v1/community/membership-requests",
            json={"unit_id": "00000000-0000-0000-0000-000000000000"},
            headers={"Origin": "http://localhost:5173"},
        )
        assert response.status_code == 403
        assert csrf
    finally:
        cleanup(member, reviewer, engine=engine)
