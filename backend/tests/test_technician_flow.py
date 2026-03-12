import json

import pytest

from app.models import Notification, Ticket, TicketPriority, TicketStatus, UserRole, db


LOGIN_URL = "/api/auth/login"
MANAGER_ASSIGN_URL = "/api/manager/tickets"
TECHNICIAN_TICKETS_URL = "/api/technician/tickets"


def post_json(client, url, data, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return client.post(url, data=json.dumps(data), headers=headers)


def patch_json(client, url, data, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return client.patch(url, data=json.dumps(data), headers=headers)


def _login(client, email, password="password123"):
    resp = post_json(client, LOGIN_URL, {"email": email, "password": password})
    return resp.get_json()["access_token"]


@pytest.fixture()
def manager_user(make_user):
    return make_user(name="Mgr", email="mgr-tech@test.com", role=UserRole.MANAGER)


@pytest.fixture()
def tenant_user(make_user, manager_user):
    return make_user(
        name="Tenant", email="tenant-tech@test.com", role=UserRole.TENANT, manager_id=manager_user.id
    )


@pytest.fixture()
def technician_user(make_user):
    return make_user(name="Tech", email="tech-flow@test.com", role=UserRole.TECHNICIAN)


@pytest.fixture()
def manager_token(client, manager_user):
    return _login(client, manager_user.email)


@pytest.fixture()
def technician_token(client, technician_user):
    return _login(client, technician_user.email)


@pytest.fixture()
def manager_ticket(db, tenant_user):
    ticket = Ticket(
        title="Water leak in ceiling",
        description="Water is leaking from the ceiling near the hallway light.",
        priority=TicketPriority.HIGH,
        created_by=tenant_user.id,
    )
    db.session.add(ticket)
    db.session.commit()
    return ticket


class TestManagerTechnicianRequest:

    def test_manager_sends_request_sets_assigned_status(
        self, client, manager_token, manager_ticket, technician_user
    ):
        resp = patch_json(
            client,
            f"{MANAGER_ASSIGN_URL}/{manager_ticket.id}/assign",
            {"technician_id": technician_user.id},
            manager_token,
        )

        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert "Request sent" in body["message"]
        assert body["ticket"]["status"] == "assigned"

        db.session.refresh(manager_ticket)
        assert manager_ticket.assigned_to == technician_user.id
        assert manager_ticket.status == TicketStatus.ASSIGNED

    def test_manager_cannot_request_technician_for_done_ticket(
        self, client, manager_token, manager_ticket, technician_user
    ):
        manager_ticket.status = TicketStatus.DONE
        db.session.commit()

        resp = patch_json(
            client,
            f"{MANAGER_ASSIGN_URL}/{manager_ticket.id}/assign",
            {"technician_id": technician_user.id},
            manager_token,
        )

        assert resp.status_code == 400
        assert "Cannot request technician" in resp.get_json()["message"]

    def test_request_notifies_technician_and_tenant(
        self, client, manager_token, manager_ticket, technician_user, tenant_user
    ):
        patch_json(
            client,
            f"{MANAGER_ASSIGN_URL}/{manager_ticket.id}/assign",
            {"technician_id": technician_user.id},
            manager_token,
        )

        tech_notifications = Notification.query.filter_by(user_id=technician_user.id).all()
        tenant_notifications = Notification.query.filter_by(user_id=tenant_user.id).all()
        assert any("technician request" in n.message.lower() for n in tech_notifications)
        assert any("technician request" in n.message.lower() for n in tenant_notifications)


class TestTechnicianRequestLifecycle:

    @pytest.fixture()
    def requested_ticket(self, client, manager_token, manager_ticket, technician_user):
        resp = patch_json(
            client,
            f"{MANAGER_ASSIGN_URL}/{manager_ticket.id}/assign",
            {"technician_id": technician_user.id},
            manager_token,
        )
        assert resp.status_code == 200
        return manager_ticket

    def test_technician_accepts_pending_request(
        self, client, technician_token, requested_ticket
    ):
        resp = patch_json(
            client,
            f"{TECHNICIAN_TICKETS_URL}/{requested_ticket.id}/accept",
            {},
            technician_token,
        )

        assert resp.status_code == 200
        body = resp.get_json()
        assert body["ticket"]["status"] == "in_progress"

    def test_technician_cannot_accept_twice(
        self, client, technician_token, requested_ticket
    ):
        first = patch_json(
            client,
            f"{TECHNICIAN_TICKETS_URL}/{requested_ticket.id}/accept",
            {},
            technician_token,
        )
        assert first.status_code == 200

        second = patch_json(
            client,
            f"{TECHNICIAN_TICKETS_URL}/{requested_ticket.id}/accept",
            {},
            technician_token,
        )
        assert second.status_code == 400
        assert "already accepted" in second.get_json()["message"].lower()

    def test_technician_can_decline_only_when_pending(
        self, client, technician_token, requested_ticket
    ):
        accepted = patch_json(
            client,
            f"{TECHNICIAN_TICKETS_URL}/{requested_ticket.id}/accept",
            {},
            technician_token,
        )
        assert accepted.status_code == 200

        decline = patch_json(
            client,
            f"{TECHNICIAN_TICKETS_URL}/{requested_ticket.id}/reject",
            {},
            technician_token,
        )
        assert decline.status_code == 400
        assert "pending requests" in decline.get_json()["message"].lower()

    def test_technician_decline_pending_request_reopens_ticket(
        self, client, technician_token, requested_ticket
    ):
        resp = patch_json(
            client,
            f"{TECHNICIAN_TICKETS_URL}/{requested_ticket.id}/reject",
            {},
            technician_token,
        )

        assert resp.status_code == 200
        body = resp.get_json()
        assert body["ticket"]["status"] == "open"

        db.session.refresh(requested_ticket)
        assert requested_ticket.assigned_to is None
        assert requested_ticket.status == TicketStatus.OPEN


class TestTechnicianCommentPermission:

    @pytest.fixture()
    def requested_ticket(self, client, manager_token, manager_ticket, technician_user):
        resp = patch_json(
            client,
            f"{MANAGER_ASSIGN_URL}/{manager_ticket.id}/assign",
            {"technician_id": technician_user.id},
            manager_token,
        )
        assert resp.status_code == 200
        return manager_ticket

    def test_technician_cannot_comment_before_accept(
        self, client, technician_token, requested_ticket
    ):
        resp = post_json(
            client,
            f"{TECHNICIAN_TICKETS_URL}/{requested_ticket.id}/comments",
            {"body": "I will handle this shortly."},
            technician_token,
        )
        assert resp.status_code == 400
        assert "accept the ticket request" in resp.get_json()["message"].lower()

    def test_technician_can_comment_after_accept(
        self, client, technician_token, requested_ticket
    ):
        accept = patch_json(
            client,
            f"{TECHNICIAN_TICKETS_URL}/{requested_ticket.id}/accept",
            {},
            technician_token,
        )
        assert accept.status_code == 200

        comment = post_json(
            client,
            f"{TECHNICIAN_TICKETS_URL}/{requested_ticket.id}/comments",
            {"body": "Started diagnosis and ordered replacement parts."},
            technician_token,
        )
        assert comment.status_code == 201
        assert comment.get_json()["comment"]["body"].startswith("Started diagnosis")
