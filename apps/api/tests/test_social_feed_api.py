import os
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.identity.security import hash_password
from app.main import app
from app.models.base import Base
from app.models.community import MembershipStatus, OrganizationUnit, UnitMembership, UnitStatus, UnitType
from app.models.identity import Account, AccountStatus, PasswordCredential
from app.models.post import Post


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
    return [TestClient(app) for _ in range(3)], engine


def seed_account(engine, email: str, unit_id=None):
    with Session(engine) as db:
        account = Account(email_normalized=email, status=AccountStatus.ACTIVE)
        db.add(account)
        db.flush()
        db.add(PasswordCredential(account_id=account.id, password_hash=hash_password("a-long-test-password")))
        if unit_id:
            db.add(UnitMembership(account_id=account.id, unit_id=unit_id, status=MembershipStatus.APPROVED))
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


def cleanup(clients, engine):
    app.dependency_overrides.clear()
    for client in clients:
        client.close()
    engine.dispose()


def test_feed_is_scoped_to_approved_members_of_the_same_unit():
    clients, engine = build_clients()
    member, same_unit_member, other_unit_member = clients
    try:
        with Session(engine) as db:
            unit_a = OrganizationUnit(
                name="Rama Centro", unit_type=UnitType.BRANCH, country_code="AR", status=UnitStatus.ACTIVE
            )
            unit_b = OrganizationUnit(
                name="Rama Norte", unit_type=UnitType.BRANCH, country_code="AR", status=UnitStatus.ACTIVE
            )
            db.add_all([unit_a, unit_b])
            db.commit()
            unit_a_id, unit_b_id = unit_a.id, unit_b.id

        member_id = seed_account(engine, "member@example.com", unit_a_id)
        seed_account(engine, "same@example.com", unit_a_id)
        seed_account(engine, "other@example.com", unit_b_id)

        member_csrf = login(member, "member@example.com")
        same_csrf = login(same_unit_member, "same@example.com")
        login(other_unit_member, "other@example.com")

        created = member.post(
            "/api/v1/social/posts",
            json={"body": "  Hola, comunidad.  "},
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": member_csrf},
        )
        assert created.status_code == 201
        assert created.json()["body"] == "Hola, comunidad."
        assert created.json()["author"] == {"display_name": None, "username": None}
        post_id = created.json()["id"]

        same_feed = same_unit_member.get("/api/v1/social/feed")
        assert same_feed.status_code == 200
        assert same_feed.headers["cache-control"] == "no-store"
        assert same_feed.headers["vary"] == "Cookie"
        assert [item["id"] for item in same_feed.json()["items"]] == [post_id]

        other_feed = other_unit_member.get("/api/v1/social/feed")
        assert other_feed.status_code == 200
        assert other_feed.json()["items"] == []

        forbidden_delete = same_unit_member.delete(
            f"/api/v1/social/posts/{post_id}",
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": same_csrf},
        )
        assert forbidden_delete.status_code == 404

        deleted = member.delete(
            f"/api/v1/social/posts/{post_id}",
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": member_csrf},
        )
        assert deleted.status_code == 204
        assert member.get("/api/v1/social/feed").json()["items"] == []

        with Session(engine) as db:
            assert db.get(Post, uuid.UUID(post_id)) is None
    finally:
        cleanup(clients, engine)


def test_feed_and_post_creation_require_approved_membership():
    clients, engine = build_clients()
    client = clients[0]
    try:
        seed_account(engine, "pending@example.com")
        csrf = login(client, "pending@example.com")

        feed = client.get("/api/v1/social/feed")
        assert feed.status_code == 403

        created = client.post(
            "/api/v1/social/posts",
            json={"body": "No debería publicarse"},
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": csrf},
        )
        assert created.status_code == 403

        missing_csrf = client.post(
            "/api/v1/social/posts",
            json={"body": "Sin CSRF"},
            headers={"Origin": "http://localhost:5173"},
        )
        assert missing_csrf.status_code == 403
    finally:
        cleanup(clients, engine)
