import pytest
from backend.app.auth import hash_password, verify_password, create_access_token, decode_access_token

def test_password_hashing_and_verification():
    pw = "SuperSecureFarmPass123"
    hashed = hash_password(pw)
    assert hashed != pw
    assert verify_password(pw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_jwt_token_generation_and_decoding():
    user_id = "test-user-uuid-123"
    email = "farmer@test.com"
    token = create_access_token(user_id, email)
    assert token is not None

    payload = decode_access_token(token)
    assert payload["sub"] == user_id
    assert payload["email"] == email
