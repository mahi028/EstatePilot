import pytest
import json
from app.models import db, User, UserRole, Ticket, TicketStatus, TicketPriority, Notification


# ===================================================
# HELPERS
# ===================================================

LOGIN_URL = "/api/auth/login"
TICKETS_URL = "/api/tenant/tickets"
NOTIFICATIONS_URL = "/api/tenant/notifications"


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


VALID_TICKET = {
    "title": "Leaking faucet in kitchen",
    "description": "The kitchen faucet has been dripping steadily since last week.",
    "priority": "high",
}


# ===================================================
# FIXTURES
# ===================================================

@pytest.fixture()
def mgr(make_user):
    return make_user(name="Mgr", email="mgr@test.com", role=UserRole.MANAGER)


@pytest.fixture()
def managed_tenant(make_user, mgr):
    """Tenant assigned to a manager — can create tickets."""
    return make_user(
        name="Managed Tenant", email="mt@test.com",
        role=UserRole.TENANT, manager_id=mgr.id,
    )


@pytest.fixture()
def free_tenant(make_user):
    """Tenant without a manager — cannot create tickets."""
    return make_user(name="Free Tenant", email="ft@test.com", role=UserRole.TENANT)


@pytest.fixture()
def tech(make_user):
    return make_user(name="Tech", email="tech@test.com", role=UserRole.TECHNICIAN)


@pytest.fixture()
def mt_token(client, managed_tenant):
    return _login(client, "mt@test.com")


@pytest.fixture()
def ft_token(client, free_tenant):
    return _login(client, "ft@test.com")


@pytest.fixture()
def mgr_token(client, mgr):
    return _login(client, "mgr@test.com")


@pytest.fixture()
def tech_token(client, tech):
    return _login(client, "tech@test.com")


@pytest.fixture()
def sample_ticket(db, managed_tenant):
    """Pre-existing ticket for list/detail tests."""
    t = Ticket(
        title="Broken window",
        description="The bedroom window is cracked and needs replacement.",
        priority=TicketPriority.MEDIUM,
        created_by=managed_tenant.id,
    )
    db.session.add(t)
    db.session.commit()
    return t


# ===================================================
# CREATE TICKET
# ===================================================

class TestCreateTicket:

    def test_create_success(self, client, mt_token, mgr):
        resp = post_json(client, TICKETS_URL, VALID_TICKET, mt_token)
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["success"] is True
        assert body["ticket"]["title"] == VALID_TICKET["title"]
        assert body["ticket"]["status"] == "open"
        assert body["ticket"]["priority"] == "high"

    def test_create_defaults_priority_to_medium(self, client, mt_token):
        data = {"title": "Broken lamp post", "description": "The lamp near the entrance is broken."}
        resp = post_json(client, TICKETS_URL, data, mt_token)
        assert resp.status_code == 201
        assert resp.get_json()["ticket"]["priority"] == "medium"

    def test_create_notifies_manager(self, client, mt_token, mgr):
        post_json(client, TICKETS_URL, VALID_TICKET, mt_token)
        notifs = Notification.query.filter_by(user_id=mgr.id).all()
        assert len(notifs) == 1
        assert "Leaking faucet" in notifs[0].message

    def test_create_without_manager_forbidden(self, client, ft_token):
        resp = post_json(client, TICKETS_URL, VALID_TICKET, ft_token)
        assert resp.status_code == 403
        assert "manager" in resp.get_json()["message"].lower()

    def test_create_missing_title(self, client, mt_token):
        data = {"description": "Some description here for testing."}
        resp = post_json(client, TICKETS_URL, data, mt_token)
        assert resp.status_code == 400
        assert "title" in resp.get_json()["errors"]

    def test_create_missing_description(self, client, mt_token):
        data = {"title": "Valid title here"}
        resp = post_json(client, TICKETS_URL, data, mt_token)
        assert resp.status_code == 400
        assert "description" in resp.get_json()["errors"]

    def test_create_short_title(self, client, mt_token):
        data = {**VALID_TICKET, "title": "Hi"}
        resp = post_json(client, TICKETS_URL, data, mt_token)
        assert resp.status_code == 400
        assert "title" in resp.get_json()["errors"]

    def test_create_short_description(self, client, mt_token):
        data = {**VALID_TICKET, "description": "Short"}
        resp = post_json(client, TICKETS_URL, data, mt_token)
        assert resp.status_code == 400
        assert "description" in resp.get_json()["errors"]

    def test_create_requires_tenant_role(self, client, mgr_token):
        resp = post_json(client, TICKETS_URL, VALID_TICKET, mgr_token)
        assert resp.status_code == 403

    def test_create_requires_auth(self, client):
        resp = post_json(client, TICKETS_URL, VALID_TICKET)
        assert resp.status_code == 401


# ===================================================
# LIST TICKETS
# ===================================================

class TestListTickets:

    def test_list_own_tickets(self, client, mt_token, sample_ticket):
        resp = get_json(client, TICKETS_URL, mt_token)
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert len(body["tickets"]) == 1
        assert body["tickets"][0]["id"] == sample_ticket.id

    def test_list_empty_when_no_tickets(self, client, mt_token):
        resp = get_json(client, TICKETS_URL, mt_token)
        assert resp.status_code == 200
        assert len(resp.get_json()["tickets"]) == 0

    def test_does_not_show_other_tenants_tickets(self, client, ft_token, sample_ticket):
        resp = get_json(client, TICKETS_URL, ft_token)
        assert resp.status_code == 200
        assert len(resp.get_json()["tickets"]) == 0

    def test_filter_by_status(self, client, mt_token, sample_ticket):
        resp = get_json(client, TICKETS_URL, mt_token, {"status": "open"})
        assert len(resp.get_json()["tickets"]) == 1

        resp = get_json(client, TICKETS_URL, mt_token, {"status": "done"})
        assert len(resp.get_json()["tickets"]) == 0

    def test_filter_by_priority(self, client, mt_token, sample_ticket):
        resp = get_json(client, TICKETS_URL, mt_token, {"priority": "medium"})
        assert len(resp.get_json()["tickets"]) == 1

        resp = get_json(client, TICKETS_URL, mt_token, {"priority": "high"})
        assert len(resp.get_json()["tickets"]) == 0

    def test_invalid_status_filter(self, client, mt_token):
        resp = get_json(client, TICKETS_URL, mt_token, {"status": "bogus"})
        assert resp.status_code == 400

    def test_invalid_priority_filter(self, client, mt_token):
        resp = get_json(client, TICKETS_URL, mt_token, {"priority": "bogus"})
        assert resp.status_code == 400

    def test_requires_tenant_role(self, client, mgr_token):
        resp = get_json(client, TICKETS_URL, mgr_token)
        assert resp.status_code == 403

    def test_requires_auth(self, client):
        resp = get_json(client, TICKETS_URL)
        assert resp.status_code == 401


# ===================================================
# TICKET DETAIL
# ===================================================

class TestTicketDetail:

    def test_get_detail(self, client, mt_token, sample_ticket):
        resp = get_json(client, f"{TICKETS_URL}/{sample_ticket.id}", mt_token)
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["ticket"]["id"] == sample_ticket.id
        assert "activity_logs" in body["ticket"]

    def test_not_found(self, client, mt_token):
        resp = get_json(client, f"{TICKETS_URL}/nonexistent", mt_token)
        assert resp.status_code == 404

    def test_cannot_view_other_tenants_ticket(self, client, ft_token, sample_ticket):
        resp = get_json(client, f"{TICKETS_URL}/{sample_ticket.id}", ft_token)
        assert resp.status_code == 404

    def test_requires_auth(self, client, sample_ticket):
        resp = get_json(client, f"{TICKETS_URL}/{sample_ticket.id}")
        assert resp.status_code == 401


# ===================================================
# NOTIFICATIONS
# ===================================================

class TestTenantNotifications:

    @pytest.fixture(autouse=True)
    def _seed(self, db, managed_tenant):
        Notification.create(user_id=managed_tenant.id, message="Test notification")
        db.session.commit()

    def test_list_notifications(self, client, mt_token):
        resp = get_json(client, NOTIFICATIONS_URL, mt_token)
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert len(body["notifications"]) == 1
        assert body["notifications"][0]["is_read"] is False

    def test_empty_for_other_tenant(self, client, ft_token):
        resp = get_json(client, NOTIFICATIONS_URL, ft_token)
        assert len(resp.get_json()["notifications"]) == 0

    def test_requires_auth(self, client):
        resp = get_json(client, NOTIFICATIONS_URL)
        assert resp.status_code == 401

    def test_requires_tenant_role(self, client, mgr_token):
        resp = get_json(client, NOTIFICATIONS_URL, mgr_token)
        assert resp.status_code == 403


class TestMarkNotificationRead:

    @pytest.fixture(autouse=True)
    def _seed(self, db, managed_tenant):
        n = Notification.create(user_id=managed_tenant.id, message="Read me")
        db.session.commit()
        self.notif_id = n.id

    def test_mark_read(self, client, mt_token):
        resp = patch_json(client, f"{NOTIFICATIONS_URL}/{self.notif_id}", {}, mt_token)
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    def test_not_found(self, client, mt_token):
        resp = patch_json(client, f"{NOTIFICATIONS_URL}/nonexistent", {}, mt_token)
        assert resp.status_code == 404

    def test_cannot_mark_other_tenants_notification(self, client, ft_token):
        resp = patch_json(client, f"{NOTIFICATIONS_URL}/{self.notif_id}", {}, ft_token)
        assert resp.status_code == 404

    def test_requires_auth(self, client):
        resp = patch_json(client, f"{NOTIFICATIONS_URL}/{self.notif_id}", {})
        assert resp.status_code == 401
