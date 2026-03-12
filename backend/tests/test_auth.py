import json
import pytest
from app.models import db, User, UserRole, Ticket, TicketPriority


# ===================================================
# HELPERS
# ===================================================

def post_json(client, url, data):
    return client.post(url, data=json.dumps(data), content_type="application/json")


def patch_json(client, url, data, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return client.patch(url, data=json.dumps(data), headers=headers)


REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"
REFRESH_URL = "/api/auth/refresh"
PROFILE_URL = "/api/auth/profile"
TECH_SERVICES_URL = "/api/technician/services"

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

    def test_profile_update_common_fields(self, client, make_user):
        make_user(name="P2", email="p2@example.com", password="password123", role=UserRole.TENANT)
        login = post_json(client, LOGIN_URL, {"email": "p2@example.com", "password": "password123"})
        token = login.get_json()["access_token"]

        resp = patch_json(client, PROFILE_URL, {
            "phone": "123-456-7890",
            "location": "Downtown",
            "bio": "Tenant who files clear issue reports.",
        }, token)
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["user"]["phone"] == "123-456-7890"
        assert body["user"]["location"] == "Downtown"

    def test_technician_services_catalog(self, client, make_user):
        make_user(name="TechSrv", email="techsrv@example.com", password="password123", role=UserRole.TECHNICIAN)
        login = post_json(client, LOGIN_URL, {"email": "techsrv@example.com", "password": "password123"})
        token = login.get_json()["access_token"]

        resp = client.get(TECH_SERVICES_URL, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert len(body["services"]) >= 3


class TestTechnicianReviews:

    @pytest.fixture(autouse=True)
    def _seed(self, make_user):
        self.manager = make_user(name="Manager", email="manager.review@example.com", password="password123", role=UserRole.MANAGER)
        self.tenant = make_user(
            name="Tenant",
            email="tenant.review@example.com",
            password="password123",
            role=UserRole.TENANT,
            manager_id=self.manager.id,
        )
        self.tech = make_user(name="Tech", email="tech.review@example.com", password="password123", role=UserRole.TECHNICIAN)
        self.other_tenant = make_user(name="OtherTenant", email="other.tenant@example.com", password="password123", role=UserRole.TENANT)

        ticket = Ticket(
            title="Reviewable ticket",
            description="Issue worked on by technician",
            priority=TicketPriority.MEDIUM,
            created_by=self.tenant.id,
            assigned_to=self.tech.id,
        )
        db.session.add(ticket)
        db.session.commit()

    def _login(self, client, email):
        return post_json(client, LOGIN_URL, {"email": email, "password": "password123"}).get_json()["access_token"]

    def test_tenant_can_review_worked_with_technician(self, client):
        token = self._login(client, "tenant.review@example.com")
        resp = client.post(
            f"/api/technicians/{self.tech.id}/reviews",
            data=json.dumps({"rating": 5, "comment": "Fast and professional service."}),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        assert resp.get_json()["technician"]["average_rating"] == 5.0

    def test_manager_can_review_worked_with_technician(self, client):
        token = self._login(client, "manager.review@example.com")
        resp = client.post(
            f"/api/technicians/{self.tech.id}/reviews",
            data=json.dumps({"rating": 4, "comment": "Good communication and on-time."}),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201

    def test_unrelated_user_cannot_review(self, client):
        token = self._login(client, "other.tenant@example.com")
        resp = client.post(
            f"/api/technicians/{self.tech.id}/reviews",
            data=json.dumps({"rating": 4, "comment": "Trying to review without shared ticket."}),
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403
