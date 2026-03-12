import pytest
import json
from app.models import db, User, UserRole, ManagementInvitation, InvitationStatus


# ===================================================
# HELPERS
# ===================================================

REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"

SEARCH_URL = "/api/manager/tenants/search"
SEND_INV_URL = "/api/manager/invitations"
SENT_INV_URL = "/api/manager/invitations/sent"
RECV_INV_URL = "/api/tenant/invitations"
RESPOND_INV_URL = "/api/tenant/invitations"  # + /<id>


def post_json(client, url, data, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return client.post(url, data=json.dumps(data), headers=headers)


def get_json(client, url, token=None, params=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return client.get(url, headers=headers, query_string=params)


def patch_json(client, url, data, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return client.patch(url, data=json.dumps(data), headers=headers)


def _login(client, email, password="password123"):
    resp = post_json(client, LOGIN_URL, {"email": email, "password": password})
    return resp.get_json()["access_token"]


# ===================================================
# FIXTURES
# ===================================================

@pytest.fixture()
def manager_user(make_user):
    return make_user(name="Mgr", email="mgr@test.com", role=UserRole.MANAGER)


@pytest.fixture()
def free_tenant(make_user):
    """Tenant without a manager."""
    return make_user(name="Free Tenant", email="free@test.com", role=UserRole.TENANT)


@pytest.fixture()
def managed_tenant(make_user, manager_user):
    """Tenant already assigned to a manager."""
    return make_user(
        name="Managed Tenant", email="managed@test.com",
        role=UserRole.TENANT, manager_id=manager_user.id,
    )


@pytest.fixture()
def tech_user(make_user):
    return make_user(name="Tech", email="tech@test.com", role=UserRole.TECHNICIAN)


@pytest.fixture()
def mgr_token(client, manager_user):
    return _login(client, "mgr@test.com")


@pytest.fixture()
def tenant_token(client, free_tenant):
    return _login(client, "free@test.com")


@pytest.fixture()
def tech_token(client, tech_user):
    return _login(client, "tech@test.com")


# ===================================================
# TENANT SEARCH
# ===================================================

class TestTenantSearch:

    def test_search_returns_unmanaged_tenants(self, client, mgr_token, free_tenant):
        resp = get_json(client, SEARCH_URL, mgr_token, {"q": "Free"})
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert any(t["id"] == free_tenant.id for t in body["tenants"])

    def test_search_excludes_managed_tenants(self, client, mgr_token, managed_tenant):
        resp = get_json(client, SEARCH_URL, mgr_token, {"q": "Managed"})
        body = resp.get_json()
        assert not any(t["id"] == managed_tenant.id for t in body["tenants"])

    def test_search_query_too_short(self, client, mgr_token):
        resp = get_json(client, SEARCH_URL, mgr_token, {"q": "a"})
        assert resp.status_code == 400

    def test_search_by_email(self, client, mgr_token, free_tenant):
        resp = get_json(client, SEARCH_URL, mgr_token, {"q": "free@"})
        body = resp.get_json()
        assert any(t["id"] == free_tenant.id for t in body["tenants"])

    def test_search_requires_manager_role(self, client, tenant_token):
        resp = get_json(client, SEARCH_URL, tenant_token, {"q": "test"})
        assert resp.status_code == 403

    def test_search_requires_auth(self, client):
        resp = get_json(client, SEARCH_URL, params={"q": "test"})
        assert resp.status_code == 401


# ===================================================
# SEND INVITATION
# ===================================================

class TestSendInvitation:

    def test_send_invitation_success(self, client, mgr_token, free_tenant):
        resp = post_json(client, SEND_INV_URL, {"tenant_id": free_tenant.id}, mgr_token)
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["success"] is True
        assert body["invitation"]["tenant"]["id"] == free_tenant.id
        assert body["invitation"]["status"] == "pending"

    def test_send_duplicate_pending_returns_409(self, client, mgr_token, free_tenant):
        post_json(client, SEND_INV_URL, {"tenant_id": free_tenant.id}, mgr_token)
        resp = post_json(client, SEND_INV_URL, {"tenant_id": free_tenant.id}, mgr_token)
        assert resp.status_code == 409

    def test_send_to_managed_tenant_fails(self, client, mgr_token, managed_tenant):
        resp = post_json(client, SEND_INV_URL, {"tenant_id": managed_tenant.id}, mgr_token)
        assert resp.status_code == 400
        assert "errors" in resp.get_json()

    def test_send_to_nonexistent_tenant_fails(self, client, mgr_token):
        resp = post_json(client, SEND_INV_URL, {"tenant_id": "no-such-id"}, mgr_token)
        assert resp.status_code == 400

    def test_send_to_non_tenant_fails(self, client, mgr_token, tech_user):
        resp = post_json(client, SEND_INV_URL, {"tenant_id": tech_user.id}, mgr_token)
        assert resp.status_code == 400

    def test_send_requires_manager_role(self, client, tenant_token, free_tenant):
        resp = post_json(client, SEND_INV_URL, {"tenant_id": free_tenant.id}, tenant_token)
        assert resp.status_code == 403

    def test_send_missing_tenant_id(self, client, mgr_token):
        resp = post_json(client, SEND_INV_URL, {}, mgr_token)
        assert resp.status_code == 400


# ===================================================
# SENT INVITATIONS LIST
# ===================================================

class TestSentInvitations:

    @pytest.fixture(autouse=True)
    def _seed(self, db, manager_user, free_tenant):
        inv = ManagementInvitation(manager_id=manager_user.id, tenant_id=free_tenant.id)
        db.session.add(inv)
        db.session.commit()
        self.invitation = inv

    def test_list_sent(self, client, mgr_token):
        resp = get_json(client, SENT_INV_URL, mgr_token)
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert len(body["invitations"]) == 1

    def test_filter_by_status(self, client, mgr_token):
        resp = get_json(client, SENT_INV_URL, mgr_token, {"status": "pending"})
        assert resp.status_code == 200
        assert len(resp.get_json()["invitations"]) == 1

    def test_filter_by_accepted_returns_empty(self, client, mgr_token):
        resp = get_json(client, SENT_INV_URL, mgr_token, {"status": "accepted"})
        assert resp.status_code == 200
        assert len(resp.get_json()["invitations"]) == 0

    def test_invalid_status_filter(self, client, mgr_token):
        resp = get_json(client, SENT_INV_URL, mgr_token, {"status": "bogus"})
        assert resp.status_code == 400

    def test_requires_manager_role(self, client, tenant_token):
        resp = get_json(client, SENT_INV_URL, tenant_token)
        assert resp.status_code == 403


# ===================================================
# RECEIVED INVITATIONS LIST
# ===================================================

class TestReceivedInvitations:

    @pytest.fixture(autouse=True)
    def _seed(self, db, manager_user, free_tenant):
        inv = ManagementInvitation(manager_id=manager_user.id, tenant_id=free_tenant.id)
        db.session.add(inv)
        db.session.commit()
        self.invitation = inv

    def test_list_received(self, client, tenant_token):
        resp = get_json(client, RECV_INV_URL, tenant_token)
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert len(body["invitations"]) == 1

    def test_filter_by_pending(self, client, tenant_token):
        resp = get_json(client, RECV_INV_URL, tenant_token, {"status": "pending"})
        assert len(resp.get_json()["invitations"]) == 1

    def test_manager_cannot_access(self, client, mgr_token):
        resp = get_json(client, RECV_INV_URL, mgr_token)
        assert resp.status_code == 403

    def test_requires_auth(self, client):
        resp = get_json(client, RECV_INV_URL)
        assert resp.status_code == 401


# ===================================================
# RESPOND TO INVITATION
# ===================================================

class TestRespondInvitation:

    @pytest.fixture(autouse=True)
    def _seed(self, db, manager_user, free_tenant):
        inv = ManagementInvitation(manager_id=manager_user.id, tenant_id=free_tenant.id)
        db.session.add(inv)
        db.session.commit()
        self.invitation = inv

    def _url(self):
        return f"{RESPOND_INV_URL}/{self.invitation.id}"

    # --- accept ---

    def test_accept(self, client, tenant_token, free_tenant, manager_user):
        resp = patch_json(client, self._url(), {"action": "accept"}, tenant_token)
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert body["invitation"]["status"] == "accepted"
        # tenant's manager_id should be set
        db.session.refresh(free_tenant)
        assert free_tenant.manager_id == manager_user.id

    # --- reject ---

    def test_reject(self, client, tenant_token, free_tenant):
        resp = patch_json(client, self._url(), {"action": "reject"}, tenant_token)
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["invitation"]["status"] == "rejected"
        db.session.refresh(free_tenant)
        assert free_tenant.manager_id is None

    # --- validation ---

    def test_invalid_action(self, client, tenant_token):
        resp = patch_json(client, self._url(), {"action": "cancel"}, tenant_token)
        assert resp.status_code == 400

    def test_missing_action(self, client, tenant_token):
        resp = patch_json(client, self._url(), {}, tenant_token)
        assert resp.status_code == 400

    def test_not_found(self, client, tenant_token):
        resp = patch_json(client, f"{RESPOND_INV_URL}/nonexistent", {"action": "accept"}, tenant_token)
        assert resp.status_code == 404

    def test_cannot_respond_twice(self, client, tenant_token):
        patch_json(client, self._url(), {"action": "accept"}, tenant_token)
        resp = patch_json(client, self._url(), {"action": "reject"}, tenant_token)
        assert resp.status_code == 400

    # --- RBAC ---

    def test_manager_cannot_respond(self, client, mgr_token):
        resp = patch_json(client, self._url(), {"action": "accept"}, mgr_token)
        assert resp.status_code == 403

    def test_other_tenant_cannot_respond(self, client, make_user):
        other = make_user(name="Other T", email="other@test.com", role=UserRole.TENANT)
        token = _login(client, "other@test.com")
        resp = patch_json(client, self._url(), {"action": "accept"}, token)
        assert resp.status_code == 404

    def test_requires_auth(self, client):
        resp = patch_json(client, self._url(), {"action": "accept"})
        assert resp.status_code == 401
