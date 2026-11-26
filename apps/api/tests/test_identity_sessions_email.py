import pytest

from app.identity.sessions import normalize_email


def test_email_normalization_trims_casefolds_and_normalizes_unicode():
    assert normalize_email(" Person@EXAMPLE.COM ") == "person@example.com"
    assert normalize_email("Cafe\u0301@example.com") == "café@example.com"


@pytest.mark.parametrize("email", ["", "a@@b", "not-an-email", "@example.com", "a@"])
def test_email_normalization_rejects_malformed_addresses(email):
    with pytest.raises(ValueError):
        normalize_email(email)
