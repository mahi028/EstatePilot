import json
import pytest
from app.models import db, User, UserRole, Ticket, TicketComment, TicketStatus, TicketPriority, Notification, TechnicianService


# ===================================================
# HELPERS
# ===================================================

LOGIN_URL = "/api/auth/login"
TICKETS_URL = "/api/tenant/tickets"
MANAGED_TICKETS_URL = "/api/manager/tickets"
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


def delete_json(client, url, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return client.delete(url, headers=headers)


def _login(client, email, password="password123"):
    resp = post_json(client, LOGIN_URL, {"email": email, "password": password})
    return resp.get_json()["access_token"]


def _valid_ticket(service_id):
    return {
        "title": "Leaking faucet in kitchen",
        "description": "The kitchen faucet has been dripping steadily since last week.",
        "priority": "high",
        "service_tag_id": service_id,
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


@pytest.fixture()
def service_tag(db):
    service = TechnicianService(code="test_plumbing", label="Test Plumbing")
    db.session.add(service)
    db.session.commit()
    return service


# ===================================================
# CREATE TICKET
# ===================================================

class TestCreateTicket:

    def test_create_success(self, client, mt_token, mgr, service_tag):
        resp = post_json(client, TICKETS_URL, _valid_ticket(service_tag.id), mt_token)
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["success"] is True
        assert body["ticket"]["title"] == _valid_ticket(service_tag.id)["title"]
        assert body["ticket"]["status"] == "open"
        assert body["ticket"]["priority"] == "high"
        assert body["ticket"]["service_tag"]["id"] == service_tag.id

    def test_create_defaults_priority_to_medium(self, client, mt_token, service_tag):
        data = {
            "title": "Broken lamp post",
            "description": "The lamp near the entrance is broken.",
            "service_tag_id": service_tag.id,
        }
        resp = post_json(client, TICKETS_URL, data, mt_token)
        assert resp.status_code == 201
        assert resp.get_json()["ticket"]["priority"] == "medium"

    def test_create_notifies_manager(self, client, mt_token, mgr, service_tag):
        post_json(client, TICKETS_URL, _valid_ticket(service_tag.id), mt_token)
        notifs = Notification.query.filter_by(user_id=mgr.id).all()
        assert len(notifs) == 1
        assert "Leaking faucet" in notifs[0].message

    def test_create_without_manager_forbidden(self, client, ft_token, service_tag):
        resp = post_json(client, TICKETS_URL, _valid_ticket(service_tag.id), ft_token)
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

    def test_create_short_title(self, client, mt_token, service_tag):
        data = {**_valid_ticket(service_tag.id), "title": "Hi"}
        resp = post_json(client, TICKETS_URL, data, mt_token)
        assert resp.status_code == 400
        assert "title" in resp.get_json()["errors"]

    def test_create_short_description(self, client, mt_token, service_tag):
        data = {**_valid_ticket(service_tag.id), "description": "Short"}
        resp = post_json(client, TICKETS_URL, data, mt_token)
        assert resp.status_code == 400
        assert "description" in resp.get_json()["errors"]

    def test_create_requires_tenant_role(self, client, mgr_token, service_tag):
        resp = post_json(client, TICKETS_URL, _valid_ticket(service_tag.id), mgr_token)
        assert resp.status_code == 403

    def test_create_requires_auth(self, client):
        resp = post_json(client, TICKETS_URL, {"title": "x", "description": "y", "service_tag_id": "z"})
        assert resp.status_code == 401

    def test_create_requires_service_tag(self, client, mt_token):
        data = {
            "title": "Door lock issue",
            "description": "Main entrance lock has become difficult to turn.",
            "priority": "medium",
        }
        resp = post_json(client, TICKETS_URL, data, mt_token)
        assert resp.status_code == 400
        assert "service_tag_id" in resp.get_json()["errors"]

    def test_create_prevents_duplicate_active_ticket(self, client, mt_token, service_tag):
        first = post_json(client, TICKETS_URL, _valid_ticket(service_tag.id), mt_token)
        assert first.status_code == 201

        second = post_json(client, TICKETS_URL, _valid_ticket(service_tag.id), mt_token)
        assert second.status_code == 409
        assert "already have an active ticket" in second.get_json()["message"].lower()

    def test_create_allows_repeat_after_previous_ticket_done(self, client, mt_token, managed_tenant, service_tag):
        ticket = Ticket(
            title="Leaking faucet in kitchen",
            description="The kitchen faucet has been dripping steadily since last week.",
            priority=TicketPriority.HIGH,
            status=TicketStatus.DONE,
            service_tag_id=service_tag.id,
            created_by=managed_tenant.id,
        )
        db.session.add(ticket)
        db.session.commit()

        resp = post_json(client, TICKETS_URL, _valid_ticket(service_tag.id), mt_token)
        assert resp.status_code == 201


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

    def test_list_supports_search_and_pagination(self, client, mt_token, managed_tenant, service_tag):
        for index in range(5):
            db.session.add(
                Ticket(
                    title=f"Kitchen issue {index}",
                    description="The kitchen sink line appears blocked and needs service.",
                    priority=TicketPriority.MEDIUM,
                    created_by=managed_tenant.id,
                    service_tag_id=service_tag.id,
                )
            )
        db.session.commit()

        resp = get_json(client, TICKETS_URL, mt_token, {"q": "kitchen issue", "page": 1, "page_size": 2})
        assert resp.status_code == 200
        body = resp.get_json()
        assert len(body["tickets"]) == 2
        assert body["pagination"]["total"] >= 5
        assert body["pagination"]["page"] == 1


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


class TestTenantTicketActions:

    def test_add_comment(self, client, mt_token, sample_ticket):
        resp = post_json(
            client,
            f"{TICKETS_URL}/{sample_ticket.id}/comments",
            {"body": "The leak is getting worse after the weekend."},
            mt_token,
        )
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["comment"]["body"].startswith("The leak")
        assert len(body["ticket"]["comments"]) == 1
        assert TicketComment.query.filter_by(ticket_id=sample_ticket.id).count() == 1

    def test_delete_ticket(self, client, mt_token, sample_ticket):
        resp = delete_json(client, f"{TICKETS_URL}/{sample_ticket.id}", mt_token)
        assert resp.status_code == 200
        assert db.session.get(Ticket, sample_ticket.id) is None

    def test_delete_ticket_notifies_assigned_technician(self, client, mt_token, sample_ticket, tech):
        sample_ticket.assigned_to = tech.id
        db.session.commit()

        resp = delete_json(client, f"{TICKETS_URL}/{sample_ticket.id}", mt_token)
        assert resp.status_code == 200

        tech_notifications = Notification.query.filter_by(user_id=tech.id).all()
        assert any("deleted by tenant" in notification.message.lower() for notification in tech_notifications)


class TestManagerTicketActions:

    def test_manager_get_detail(self, client, mgr_token, sample_ticket):
        resp = get_json(client, f"{MANAGED_TICKETS_URL}/{sample_ticket.id}", mgr_token)
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["ticket"]["id"] == sample_ticket.id
        assert "comments" in body["ticket"]

    def test_manager_add_comment(self, client, mgr_token, sample_ticket, managed_tenant):
        resp = post_json(
            client,
            f"{MANAGED_TICKETS_URL}/{sample_ticket.id}/comments",
            {"body": "Please confirm whether access is available this afternoon."},
            mgr_token,
        )
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["comment"]["user"]["role"] == "manager"
        tenant_notifications = Notification.query.filter_by(user_id=managed_tenant.id).all()
        assert any("New comment on ticket" in notification.message for notification in tenant_notifications)

    def test_manager_mark_invalid(self, client, mgr_token, sample_ticket, managed_tenant):
        resp = patch_json(client, f"{MANAGED_TICKETS_URL}/{sample_ticket.id}/invalid", {}, mgr_token)
        assert resp.status_code == 200
        db.session.refresh(sample_ticket)
        assert sample_ticket.status == TicketStatus.INVALID
        tenant_notifications = Notification.query.filter_by(user_id=managed_tenant.id).all()
        assert any("marked invalid" in notification.message for notification in tenant_notifications)

    def test_manager_mark_invalid_notifies_assigned_technician(self, client, mgr_token, sample_ticket, tech):
        sample_ticket.assigned_to = tech.id
        db.session.commit()

        resp = patch_json(client, f"{MANAGED_TICKETS_URL}/{sample_ticket.id}/invalid", {}, mgr_token)
        assert resp.status_code == 200

        tech_notifications = Notification.query.filter_by(user_id=tech.id).all()
        assert any("marked invalid" in notification.message.lower() for notification in tech_notifications)


class TestUserNotificationsAPI:

    def test_user_notifications_support_search_unread_and_pagination(self, client, mgr, mgr_token):
        for index in range(5):
            notification = Notification(user_id=mgr.id, message=f"Ticket update {index}")
            if index % 2 == 0:
                notification.is_read = True
            db.session.add(notification)
        db.session.commit()

        resp = get_json(
            client,
            "/api/notifications",
            mgr_token,
            {"q": "ticket update", "unread": "true", "page": 1, "page_size": 2},
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert len(body["notifications"]) == 2
        assert all(item["is_read"] is False for item in body["notifications"])
        assert body["pagination"]["total"] == 2


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
