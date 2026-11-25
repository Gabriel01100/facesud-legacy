from app.identity.security import hash_password, new_session_secrets, token_digest, verify_password


def test_password_hash_is_not_plaintext_and_verifies():
    password = "correct-horse-battery-staple"
    password_hash = hash_password(password)

    assert password_hash != password
    assert verify_password(password_hash, password)
    assert not verify_password(password_hash, "incorrect-password")


def test_password_policy_rejects_short_password():
    try:
        hash_password("short")
    except ValueError as exc:
        assert "12 characters" in str(exc)
    else:
        raise AssertionError("Expected short password to be rejected")


def test_session_secrets_are_random_and_only_digest_is_persisted():
    session_token, csrf_token = new_session_secrets()

    assert session_token != csrf_token
    assert len(token_digest(session_token)) == 64
    assert token_digest(session_token) != session_token
