"""Unit tests for password/JWT utilities and AuthService (UT36–UT43).

UserRepository is mocked; no database is used.
"""
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

import jwt
import pytest

from app.config import get_settings
from app.services.auth_service import AuthService
from app.utilities.security import (
    create_access_token,
    encrypt_password,
    verify_password,
)

pytestmark = pytest.mark.unit


def decode(token):
    settings = get_settings()
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])


# ------------------------------------------------------------------ security utilities
def test_password_is_hashed_and_verified():  # UT36
    hashed = encrypt_password("mypassword")
    assert hashed != "mypassword"
    assert "mypassword" not in hashed
    assert verify_password("mypassword", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_access_token_contains_user_id_and_role():  # UT37
    payload = decode(create_access_token({"sub": "4", "role": "advisor"}))
    assert payload["sub"] == "4"
    assert payload["role"] == "advisor"
    assert "exp" in payload


def test_expired_token_is_rejected():  # UT38
    token = create_access_token({"sub": "4"}, expires_delta=timedelta(seconds=-5))
    with pytest.raises(jwt.ExpiredSignatureError):
        decode(token)


# ------------------------------------------------------------------ AuthService.authenticate_user
@pytest.fixture(scope="module")
def bob():
    return SimpleNamespace(id=1, username="bob", role="regular_user",
                           password=encrypt_password("bobpass"))


def test_authenticate_valid_credentials_returns_token(bob):  # UT39
    repo = MagicMock()
    repo.get_by_username.return_value = bob
    token = AuthService(repo).authenticate_user("bob", "bobpass")
    assert token is not None
    assert decode(token)["sub"] == "1"
    assert decode(token)["role"] == "regular_user"


def test_authenticate_wrong_password_returns_none(bob):  # UT40
    repo = MagicMock()
    repo.get_by_username.return_value = bob
    assert AuthService(repo).authenticate_user("bob", "nope") is None


def test_authenticate_unknown_user_returns_none():  # UT41
    repo = MagicMock()
    repo.get_by_username.return_value = None
    assert AuthService(repo).authenticate_user("ghost", "whatever") is None


# ------------------------------------------------------------------ AuthService.register_user
def test_register_hashes_password_and_trims_names():  # UT42
    repo = MagicMock()
    AuthService(repo).register_user(
        "amy", "amy@example.com", "secret1",
        student_id=" 816 ", first_name=" Amy ", last_name=" Ng ", degree_program_id=1,
    )
    new_user = repo.create_student_account.call_args.args[0]
    kwargs = repo.create_student_account.call_args.kwargs
    assert new_user.username == "amy"
    assert new_user.role == "regular_user"
    assert new_user.password != "secret1"
    assert verify_password("secret1", new_user.password)
    assert (kwargs["student_id"], kwargs["first_name"], kwargs["last_name"]) == ("816", "Amy", "Ng")


@pytest.mark.parametrize(
    "student_id, first_name, last_name",
    [("", "Amy", "Ng"), ("816", "  ", "Ng"), ("816", "Amy", "")],
)
def test_register_requires_student_details(student_id, first_name, last_name):  # UT43
    repo = MagicMock()
    with pytest.raises(ValueError, match="required"):
        AuthService(repo).register_user(
            "amy", "amy@example.com", "secret1",
            student_id=student_id, first_name=first_name,
            last_name=last_name, degree_program_id=1,
        )
    repo.create_student_account.assert_not_called()
