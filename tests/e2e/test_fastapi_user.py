from uuid import uuid4
import pytest
import requests

# ---------------------------------------------------------------------------
# Helper Fixtures and Functions
# ---------------------------------------------------------------------------
@pytest.fixture
def base_url(fastapi_server: str) -> str:
    """
    Returns the FastAPI server base URL without a trailing slash.
    """
    return fastapi_server.rstrip("/")

def make_user_data(prefix: str) -> dict:
    """Build a unique registration payload for the given test prefix."""
    unique = uuid4()
    return {
        "first_name": "Test",
        "last_name": "User",
        "email": f"{prefix}.{unique}@example.com",
        "username": f"{prefix}_{unique.hex[:12]}",
        "password": "SecurePass123!",
        "confirm_password": "SecurePass123!"
    }

def register_and_login(base_url: str, user_data: dict) -> dict:
    """
    Registers a new user and logs in, returning the token response data
    (includes access_token and user_id).
    """
    reg_response = requests.post(f"{base_url}/auth/register", json=user_data)
    assert reg_response.status_code == 201, f"User registration failed: {reg_response.text}"

    login_response = requests.post(
        f"{base_url}/auth/login",
        json={"username": user_data["username"], "password": user_data["password"]}
    )
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    return login_response.json()

# ---------------------------------------------------------------------------
# PUT /users/{user_id} - Username/Email Update
# ---------------------------------------------------------------------------
def test_update_username_and_email_success(base_url: str):
    user_data = make_user_data("update_both")
    token_data = register_and_login(base_url, user_data)
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}

    new_username = f"updated_{uuid4().hex[:12]}"
    new_email = f"updated.{uuid4()}@example.com"
    response = requests.put(
        f"{base_url}/users/{token_data['user_id']}",
        json={"username": new_username, "email": new_email},
        headers=headers
    )
    assert response.status_code == 200, f"Update failed: {response.text}"
    data = response.json()
    assert data["username"] == new_username
    assert data["email"] == new_email

def test_update_username_only(base_url: str):
    user_data = make_user_data("update_username")
    token_data = register_and_login(base_url, user_data)
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}

    new_username = f"updated_{uuid4().hex[:12]}"
    response = requests.put(
        f"{base_url}/users/{token_data['user_id']}",
        json={"username": new_username},
        headers=headers
    )
    assert response.status_code == 200, f"Update failed: {response.text}"
    data = response.json()
    assert data["username"] == new_username
    assert data["email"] == user_data["email"], "Email should be unchanged"

def test_update_no_fields_returns_400(base_url: str):
    user_data = make_user_data("update_empty")
    token_data = register_and_login(base_url, user_data)
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}

    response = requests.put(
        f"{base_url}/users/{token_data['user_id']}",
        json={},
        headers=headers
    )
    assert response.status_code == 400
    assert "No fields to update" in response.text

def test_update_duplicate_username_returns_400(base_url: str):
    user_a = register_and_login(base_url, make_user_data("dup_user_a"))
    user_b_data = make_user_data("dup_user_b")
    register_and_login(base_url, user_b_data)
    headers = {"Authorization": f"Bearer {user_a['access_token']}"}

    response = requests.put(
        f"{base_url}/users/{user_a['user_id']}",
        json={"username": user_b_data["username"]},
        headers=headers
    )
    assert response.status_code == 400
    assert "already exists" in response.text

def test_update_duplicate_email_returns_400(base_url: str):
    user_a = register_and_login(base_url, make_user_data("dup_email_a"))
    user_b_data = make_user_data("dup_email_b")
    register_and_login(base_url, user_b_data)
    headers = {"Authorization": f"Bearer {user_a['access_token']}"}

    response = requests.put(
        f"{base_url}/users/{user_a['user_id']}",
        json={"email": user_b_data["email"]},
        headers=headers
    )
    assert response.status_code == 400
    assert "already exists" in response.text

def test_update_other_user_forbidden(base_url: str):
    user_a = register_and_login(base_url, make_user_data("forbid_a"))
    user_b = register_and_login(base_url, make_user_data("forbid_b"))
    headers = {"Authorization": f"Bearer {user_a['access_token']}"}

    response = requests.put(
        f"{base_url}/users/{user_b['user_id']}",
        json={"username": f"hijack_{uuid4().hex[:12]}"},
        headers=headers
    )
    assert response.status_code == 403

def test_update_unauthenticated_returns_401(base_url: str):
    user_data = make_user_data("update_unauth")
    token_data = register_and_login(base_url, user_data)

    response = requests.put(
        f"{base_url}/users/{token_data['user_id']}",
        json={"username": f"nope_{uuid4().hex[:12]}"}
    )
    assert response.status_code == 401

def test_update_invalid_user_id_format_returns_400(base_url: str):
    user_data = make_user_data("update_badid")
    token_data = register_and_login(base_url, user_data)
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}

    response = requests.put(
        f"{base_url}/users/not-a-valid-uuid",
        json={"username": f"nope_{uuid4().hex[:12]}"},
        headers=headers
    )
    assert response.status_code == 400
    assert "Invalid user id format" in response.text

# ---------------------------------------------------------------------------
# PUT /users/{user_id}/password - Password Update
# ---------------------------------------------------------------------------
def test_update_password_success(base_url: str):
    user_data = make_user_data("password_success")
    token_data = register_and_login(base_url, user_data)
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}

    new_password = "NewSecurePass456!"
    response = requests.put(
        f"{base_url}/users/{token_data['user_id']}/password",
        json={
            "current_password": user_data["password"],
            "new_password": new_password,
            "confirm_new_password": new_password
        },
        headers=headers
    )
    assert response.status_code == 200, f"Password update failed: {response.text}"

    # Old password should no longer work
    old_login = requests.post(
        f"{base_url}/auth/login",
        json={"username": user_data["username"], "password": user_data["password"]}
    )
    assert old_login.status_code == 401

    # New password should work
    new_login = requests.post(
        f"{base_url}/auth/login",
        json={"username": user_data["username"], "password": new_password}
    )
    assert new_login.status_code == 200

def test_update_password_wrong_current_returns_401(base_url: str):
    user_data = make_user_data("password_wrong")
    token_data = register_and_login(base_url, user_data)
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}

    response = requests.put(
        f"{base_url}/users/{token_data['user_id']}/password",
        json={
            "current_password": "WrongPassword123!",
            "new_password": "NewSecurePass456!",
            "confirm_new_password": "NewSecurePass456!"
        },
        headers=headers
    )
    assert response.status_code == 401
    assert "Current password is incorrect" in response.text

def test_update_password_same_as_current_returns_422(base_url: str):
    user_data = make_user_data("password_same")
    token_data = register_and_login(base_url, user_data)
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}

    response = requests.put(
        f"{base_url}/users/{token_data['user_id']}/password",
        json={
            "current_password": user_data["password"],
            "new_password": user_data["password"],
            "confirm_new_password": user_data["password"]
        },
        headers=headers
    )
    assert response.status_code == 422

def test_update_password_mismatched_confirmation_returns_422(base_url: str):
    user_data = make_user_data("password_mismatch")
    token_data = register_and_login(base_url, user_data)
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}

    response = requests.put(
        f"{base_url}/users/{token_data['user_id']}/password",
        json={
            "current_password": user_data["password"],
            "new_password": "NewSecurePass456!",
            "confirm_new_password": "SomethingElse789!"
        },
        headers=headers
    )
    assert response.status_code == 422

def test_update_password_other_user_forbidden(base_url: str):
    user_a = register_and_login(base_url, make_user_data("pw_forbid_a"))
    user_b_data = make_user_data("pw_forbid_b")
    user_b = register_and_login(base_url, user_b_data)
    headers = {"Authorization": f"Bearer {user_a['access_token']}"}

    response = requests.put(
        f"{base_url}/users/{user_b['user_id']}/password",
        json={
            "current_password": user_b_data["password"],
            "new_password": "NewSecurePass456!",
            "confirm_new_password": "NewSecurePass456!"
        },
        headers=headers
    )
    assert response.status_code == 403

def test_update_password_unauthenticated_returns_401(base_url: str):
    user_data = make_user_data("pw_unauth")
    token_data = register_and_login(base_url, user_data)

    response = requests.put(
        f"{base_url}/users/{token_data['user_id']}/password",
        json={
            "current_password": user_data["password"],
            "new_password": "NewSecurePass456!",
            "confirm_new_password": "NewSecurePass456!"
        }
    )
    assert response.status_code == 401
