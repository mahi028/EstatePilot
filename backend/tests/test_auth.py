import pytest
import json
from app.models import db, User, UserRole


# ===================================================
# HELPERS
# ===================================================

def post_json(client, url, data):
    return client.post(url, data=json.dumps(data), content_type="application/json")


REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"
REFRESH_URL = "/api/auth/refresh"
PROFILE_URL = "/api/auth/profile"

VALID_REGISTER = {
    "name": "Alice",
    "email": "alice@example.com",
    "password": "strongpass1",
    "confirm_password": "strongpass1",
    "role": "tenant",
}


# ===================================================
# REGISTRATION
# ===================================================

class TestRegister:

    def test_register_tenant(self, client):
        resp = post_json(client, REGISTER_URL, VALID_REGISTER)
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["success"] is True
        assert body["user"]["email"] == "alice@example.com"
        assert body["user"]["role"] == "tenant"
        assert "access_token" in body
        assert "refresh_token" in body

    def test_register_manager(self, client):
        data = {**VALID_REGISTER, "email": "mgr@example.com", "role": "manager"}
        resp = post_json(client, REGISTER_URL, data)
        assert resp.status_code == 201
        assert resp.get_json()["user"]["role"] == "manager"

    def test_register_technician(self, client):
        data = {**VALID_REGISTER, "email": "tech@example.com", "role": "technician"}
        resp = post_json(client, REGISTER_URL, data)
        assert resp.status_code == 201
        assert resp.get_json()["user"]["role"] == "technician"

    def test_register_tenant_with_manager(self, client, manager):
        data = {**VALID_REGISTER, "email": "t2@example.com", "manager_id": manager.id}
        resp = post_json(client, REGISTER_URL, data)
        assert resp.status_code == 201
        assert resp.get_json()["user"]["manager_id"] == manager.id

    def test_register_duplicate_email_fails(self, client):
        post_json(client, REGISTER_URL, VALID_REGISTER)
        resp = post_json(client, REGISTER_URL, VALID_REGISTER)
        assert resp.status_code == 400
        assert "email" in resp.get_json()["errors"]

    def test_register_missing_fields(self, client):
        resp = post_json(client, REGISTER_URL, {})
        assert resp.status_code == 400
        errors = resp.get_json()["errors"]
        assert "name" in errors
        assert "email" in errors
        assert "password" in errors

    def test_register_password_mismatch(self, client):
        data = {**VALID_REGISTER, "email": "mm@example.com", "confirm_password": "different1"}
        resp = post_json(client, REGISTER_URL, data)
        assert resp.status_code == 400
        assert "confirm_password" in resp.get_json()["errors"]

    def test_register_short_password(self, client):
        data = {**VALID_REGISTER, "email": "sp@example.com", "password": "short", "confirm_password": "short"}
        resp = post_json(client, REGISTER_URL, data)
        assert resp.status_code == 400
        assert "password" in resp.get_json()["errors"]

    def test_register_invalid_email(self, client):
        data = {**VALID_REGISTER, "email": "not-an-email"}
        resp = post_json(client, REGISTER_URL, data)
        assert resp.status_code == 400
        assert "email" in resp.get_json()["errors"]

    def test_register_manager_id_for_non_tenant_fails(self, client, manager):
        data = {
            **VALID_REGISTER,
            "email": "tech2@example.com",
            "role": "technician",
            "manager_id": manager.id,
        }
        resp = post_json(client, REGISTER_URL, data)
        assert resp.status_code == 400
        assert "manager_id" in resp.get_json()["errors"]

    def test_register_invalid_manager_id_fails(self, client):
        data = {**VALID_REGISTER, "email": "t3@example.com", "manager_id": "nonexistent-id"}
        resp = post_json(client, REGISTER_URL, data)
        assert resp.status_code == 400
        assert "manager_id" in resp.get_json()["errors"]


# ===================================================
# LOGIN
# ===================================================

class TestLogin:

    @pytest.fixture(autouse=True)
    def _seed_user(self, make_user):
        self.user = make_user(
            name="Bob", email="bob@example.com", password="password123",
            role=UserRole.TENANT,
        )

    def test_login_success(self, client):
        resp = post_json(client, LOGIN_URL, {
            "email": "bob@example.com", "password": "password123",
        })
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert body["user"]["email"] == "bob@example.com"
        assert "access_token" in body
        assert "refresh_token" in body

    def test_login_wrong_password(self, client):
        resp = post_json(client, LOGIN_URL, {
            "email": "bob@example.com", "password": "wrong",
        })
        assert resp.status_code == 401
        assert resp.get_json()["success"] is False

    def test_login_nonexistent_email(self, client):
        resp = post_json(client, LOGIN_URL, {
            "email": "nobody@example.com", "password": "password123",
        })
        assert resp.status_code == 401

    def test_login_missing_fields(self, client):
        resp = post_json(client, LOGIN_URL, {})
        assert resp.status_code == 400


# ===================================================
# TOKEN REFRESH
# ===================================================

class TestRefresh:

    def test_refresh_returns_new_tokens(self, client, make_user):
        make_user(name="R", email="r@example.com", password="password123", role=UserRole.TENANT)
        login = post_json(client, LOGIN_URL, {"email": "r@example.com", "password": "password123"})
        refresh_token = login.get_json()["refresh_token"]

        resp = client.post(REFRESH_URL, headers={
            "Authorization": f"Bearer {refresh_token}",
            "Content-Type": "application/json",
        })
        assert resp.status_code == 200
        body = resp.get_json()
        assert "access_token" in body
        assert "refresh_token" in body

    def test_refresh_without_token_fails(self, client):
        resp = client.post(REFRESH_URL, content_type="application/json")
        assert resp.status_code == 401


# ===================================================
# PROFILE
# ===================================================

class TestProfile:

    def test_profile_returns_current_user(self, client, make_user):
        make_user(name="P", email="p@example.com", password="password123", role=UserRole.MANAGER)
        login = post_json(client, LOGIN_URL, {"email": "p@example.com", "password": "password123"})
        token = login.get_json()["access_token"]

        resp = client.get(PROFILE_URL, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["user"]["email"] == "p@example.com"
        assert body["user"]["role"] == "manager"

    def test_profile_without_token_fails(self, client):
        resp = client.get(PROFILE_URL)
        assert resp.status_code == 401
