import os
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
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

        seed_account(engine, "member@example.com", unit_a_id)
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


def test_comments_and_reactions_are_restricted_to_the_post_unit_and_author_controls():
    clients, engine = build_clients()
    author, same_unit_member, other_unit_member = clients
    try:
        with Session(engine) as db:
            unit_a = OrganizationUnit(
                name="Rama Sur", unit_type=UnitType.BRANCH, country_code="AR", status=UnitStatus.ACTIVE
            )
            unit_b = OrganizationUnit(
                name="Rama Este", unit_type=UnitType.BRANCH, country_code="AR", status=UnitStatus.ACTIVE
            )
            db.add_all([unit_a, unit_b])
            db.commit()
            unit_a_id, unit_b_id = unit_a.id, unit_b.id

        author_id = seed_account(engine, "interaction-author@example.com", unit_a_id)
        seed_account(engine, "interaction-member@example.com", unit_a_id)
        seed_account(engine, "interaction-outsider@example.com", unit_b_id)
        author_csrf = login(author, "interaction-author@example.com")
        member_csrf = login(same_unit_member, "interaction-member@example.com")
        outsider_csrf = login(other_unit_member, "interaction-outsider@example.com")

        created = author.post(
            "/api/v1/social/posts",
            json={"body": "Publicación para interactuar"},
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": author_csrf},
        )
        assert created.status_code == 201
        post_id = created.json()["id"]

        comment_response = same_unit_member.post(
            f"/api/v1/social/posts/{post_id}/comments",
            json={"body": "Comentario de la misma unidad"},
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": member_csrf},
        )
        assert comment_response.status_code == 201
        comment_id = comment_response.json()["id"]
        assert comment_response.json()["body"] == "Comentario de la misma unidad"
        assert "email" not in comment_response.json()
        assert "account_id" not in comment_response.json()

        comments = author.get(f"/api/v1/social/posts/{post_id}/comments")
        assert comments.status_code == 200
        assert [item["id"] for item in comments.json()["items"]] == [comment_id]

        cannot_delete_another_comment = author.delete(
            f"/api/v1/social/comments/{comment_id}",
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": author_csrf},
        )
        assert cannot_delete_another_comment.status_code == 404

        outsider_comment = other_unit_member.post(
            f"/api/v1/social/posts/{post_id}/comments",
            json={"body": "No debería entrar"},
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": outsider_csrf},
        )
        assert outsider_comment.status_code == 404
        outsider_reaction = other_unit_member.put(
            f"/api/v1/social/posts/{post_id}/reaction",
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": outsider_csrf},
        )
        assert outsider_reaction.status_code == 404

        first_reaction = same_unit_member.put(
            f"/api/v1/social/posts/{post_id}/reaction",
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": member_csrf},
        )
        second_reaction = same_unit_member.put(
            f"/api/v1/social/posts/{post_id}/reaction",
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": member_csrf},
        )
        assert first_reaction.status_code == 200
        assert second_reaction.status_code == 200
        assert second_reaction.json() == {
            "comment_count": 1, "reaction_count": 1, "is_reacted": True
        }

        feed = author.get("/api/v1/social/feed")
        assert feed.status_code == 200
        assert feed.json()["items"][0]["comment_count"] == 1
        assert feed.json()["items"][0]["reaction_count"] == 1
        assert feed.json()["items"][0]["is_reacted"] is False

        removed_reaction = same_unit_member.delete(
            f"/api/v1/social/posts/{post_id}/reaction",
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": member_csrf},
        )
        assert removed_reaction.status_code == 200
        assert removed_reaction.json()["reaction_count"] == 0
        assert removed_reaction.json()["is_reacted"] is False

        removed_comment = same_unit_member.delete(
            f"/api/v1/social/comments/{comment_id}",
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": member_csrf},
        )
        assert removed_comment.status_code == 204

        with Session(engine) as db:
            author_membership = db.scalar(
                select(UnitMembership).where(UnitMembership.account_id == author_id)
            )
            author_membership.status = MembershipStatus.REVOKED
            db.commit()
        revoked_author_comments = same_unit_member.get(f"/api/v1/social/posts/{post_id}/comments")
        assert revoked_author_comments.status_code == 404

        missing_csrf = same_unit_member.post(
            f"/api/v1/social/posts/{post_id}/comments",
            json={"body": "Sin token"},
            headers={"Origin": "http://localhost:5173"},
        )
        assert missing_csrf.status_code == 403
    finally:
        cleanup(clients, engine)


def test_post_images_are_normalized_private_and_unit_scoped(monkeypatch):
    from io import BytesIO

    from PIL import Image

    from app.core.config import settings
    from app.media.storage import get_media_storage

    class MemoryStorage:
        def __init__(self):
            self.objects = {}

        def put(self, key, content, content_type):
            self.objects[key] = (content, content_type)

        def get(self, key):
            return self.objects[key][0]

        def delete(self, key):
            self.objects.pop(key, None)

    clients, engine = build_clients()
    author, same_unit_member, other_unit_member = clients
    storage = MemoryStorage()
    app.dependency_overrides[get_media_storage] = lambda: storage
    try:
        with Session(engine) as db:
            unit_a = OrganizationUnit(
                name="Rama Imagen", unit_type=UnitType.BRANCH, country_code="AR", status=UnitStatus.ACTIVE
            )
            unit_b = OrganizationUnit(
                name="Rama Privada", unit_type=UnitType.BRANCH, country_code="AR", status=UnitStatus.ACTIVE
            )
            db.add_all([unit_a, unit_b])
            db.commit()
            unit_a_id, unit_b_id = unit_a.id, unit_b.id

        seed_account(engine, "media-author@example.com", unit_a_id)
        seed_account(engine, "media-member@example.com", unit_a_id)
        seed_account(engine, "media-outsider@example.com", unit_b_id)
        author_csrf = login(author, "media-author@example.com")
        member_csrf = login(same_unit_member, "media-member@example.com")
        login(other_unit_member, "media-outsider@example.com")

        post = author.post(
            "/api/v1/social/posts",
            json={"body": "Publicación con imagen"},
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": author_csrf},
        )
        assert post.status_code == 201
        post_id = post.json()["id"]

        image_buffer = BytesIO()
        Image.new("RGB", (32, 24), (22, 122, 153)).save(image_buffer, format="PNG")
        image_bytes = image_buffer.getvalue()

        uploaded = author.post(
            f"/api/v1/social/posts/{post_id}/media",
            files={"file": ("imagen.png", image_bytes, "image/png")},
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": author_csrf},
        )
        assert uploaded.status_code == 201
        media = uploaded.json()
        assert media["content_type"] == "image/webp"
        assert media["width"] == 32
        assert media["height"] == 24
        assert len(storage.objects) == 1

        monkeypatch.setattr(settings, "media_max_post_images", 1)
        too_many_images = author.post(
            f"/api/v1/social/posts/{post_id}/media",
            files={"file": ("imagen.png", image_bytes, "image/png")},
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": author_csrf},
        )
        assert too_many_images.status_code == 409

        feed = same_unit_member.get("/api/v1/social/feed")
        assert feed.status_code == 200
        assert feed.json()["items"][0]["images"][0]["id"] == media["id"]

        visible_image = same_unit_member.get(media["url"])
        assert visible_image.status_code == 200
        assert visible_image.headers["content-type"] == "image/webp"
        assert visible_image.headers["cache-control"] == "private, no-store"
        assert visible_image.headers["x-content-type-options"] == "nosniff"
        assert Image.open(BytesIO(visible_image.content)).format == "WEBP"

        hidden_image = other_unit_member.get(media["url"])
        assert hidden_image.status_code == 404

        cannot_attach = same_unit_member.post(
            f"/api/v1/social/posts/{post_id}/media",
            files={"file": ("imagen.png", image_bytes, "image/png")},
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": member_csrf},
        )
        assert cannot_attach.status_code == 404

        missing_csrf = author.post(
            f"/api/v1/social/posts/{post_id}/media",
            files={"file": ("imagen.png", image_bytes, "image/png")},
            headers={"Origin": "http://localhost:5173"},
        )
        assert missing_csrf.status_code == 403

        invalid_image = author.post(
            f"/api/v1/social/posts/{post_id}/media",
            files={"file": ("archivo.png", b"not an image", "image/png")},
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": author_csrf},
        )
        assert invalid_image.status_code == 422

        deleted = author.delete(
            f"/api/v1/social/posts/{post_id}",
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": author_csrf},
        )
        assert deleted.status_code == 204
        assert storage.objects == {}
    finally:
        cleanup(clients, engine)
