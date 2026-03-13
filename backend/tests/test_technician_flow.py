import json

import pytest

from app.models import Notification, TechnicianService, Ticket, TicketPriority, TicketStatus, UserRole, db


LOGIN_URL = "/api/auth/login"
MANAGER_ASSIGN_URL = "/api/manager/tickets"
TECHNICIAN_TICKETS_URL = "/api/technician/tickets"
MANAGER_BIDS_URL = "/api/manager/tickets"


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
    service = TechnicianService(code="flow_plumbing", label="Flow Plumbing")
    db.session.add(service)
    db.session.flush()

    ticket = Ticket(
        title="Water leak in ceiling",
        description="Water is leaking from the ceiling near the hallway light.",
        priority=TicketPriority.HIGH,
        service_tag_id=service.id,
        created_by=tenant_user.id,
    )
    db.session.add(ticket)
    db.session.commit()
    return ticket


@pytest.fixture()
def non_matching_ticket(db, tenant_user):
    service = TechnicianService(code="flow_hvac", label="Flow HVAC")
    db.session.add(service)
    db.session.flush()

    ticket = Ticket(
        title="AC issue",
        description="Cooling is inconsistent in the living room area.",
        priority=TicketPriority.MEDIUM,
        service_tag_id=service.id,
        created_by=tenant_user.id,
    )
    db.session.add(ticket)
    db.session.commit()
    return ticket


@pytest.fixture(autouse=True)
def _assign_technician_service(db, technician_user, manager_ticket):
    technician_user.services = [manager_ticket.service_tag]
    db.session.commit()


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
        assert body["ticket"]["status"] == "open"
        assert body["ticket"]["technician_request_pending"] is True

        db.session.refresh(manager_ticket)
        assert manager_ticket.assigned_to == technician_user.id
        assert manager_ticket.status == TicketStatus.OPEN
        assert manager_ticket.technician_request_pending is True

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

    def test_manager_cannot_request_non_matching_service_technician(
        self, client, manager_token, manager_ticket, make_user, db
    ):
        other_tech = make_user(name="Other Tech", email="other-tech@test.com", role=UserRole.TECHNICIAN)
        db.session.commit()

        resp = patch_json(
            client,
            f"{MANAGER_ASSIGN_URL}/{manager_ticket.id}/assign",
            {"technician_id": other_tech.id},
            manager_token,
        )
        assert resp.status_code == 400
        assert "service tag" in resp.get_json()["message"].lower()

    def test_manager_cannot_reassign_ticket_once_work_is_in_progress(
        self, client, manager_token, manager_ticket, technician_user, make_user, db
    ):
        second_technician = make_user(name="Second Tech", email="second-tech@test.com", role=UserRole.TECHNICIAN)
        second_technician.services = [manager_ticket.service_tag]
        db.session.commit()

        requested = patch_json(
            client,
            f"{MANAGER_ASSIGN_URL}/{manager_ticket.id}/assign",
            {"technician_id": technician_user.id},
            manager_token,
        )
        assert requested.status_code == 200

        accepted = patch_json(
            client,
            f"{TECHNICIAN_TICKETS_URL}/{manager_ticket.id}/accept",
            {},
            _login(client, technician_user.email),
        )
        assert accepted.status_code == 200

        started = patch_json(
            client,
            f"{TECHNICIAN_TICKETS_URL}/{manager_ticket.id}/status",
            {"status": "in_progress"},
            _login(client, technician_user.email),
        )
        assert started.status_code == 200

        reassigned = patch_json(
            client,
            f"{MANAGER_ASSIGN_URL}/{manager_ticket.id}/assign",
            {"technician_id": second_technician.id},
            manager_token,
        )
        assert reassigned.status_code == 400
        assert "in progress" in reassigned.get_json()["message"].lower()


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
        assert body["ticket"]["status"] == "assigned"
        assert body["ticket"]["technician_request_pending"] is False

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
        assert "already handled" in second.get_json()["message"].lower()

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
        assert requested_ticket.technician_request_pending is False


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


class TestTechnicianStatusProgression:

    @pytest.fixture()
    def accepted_ticket(self, client, manager_token, manager_ticket, technician_user):
        requested = patch_json(
            client,
            f"{MANAGER_ASSIGN_URL}/{manager_ticket.id}/assign",
            {"technician_id": technician_user.id},
            manager_token,
        )
        assert requested.status_code == 200

        accepted = patch_json(
            client,
            f"{TECHNICIAN_TICKETS_URL}/{manager_ticket.id}/accept",
            {},
            _login(client, technician_user.email),
        )
        assert accepted.status_code == 200
        return manager_ticket

    def test_technician_can_mark_ticket_in_progress(self, client, technician_token, accepted_ticket):
        resp = patch_json(
            client,
            f"{TECHNICIAN_TICKETS_URL}/{accepted_ticket.id}/status",
            {"status": "in_progress"},
            technician_token,
        )

        assert resp.status_code == 200
        assert resp.get_json()["ticket"]["status"] == "in_progress"

    def test_technician_can_mark_ticket_done_after_in_progress(self, client, technician_token, accepted_ticket):
        started = patch_json(
            client,
            f"{TECHNICIAN_TICKETS_URL}/{accepted_ticket.id}/status",
            {"status": "in_progress"},
            technician_token,
        )
        assert started.status_code == 200

        finished = patch_json(
            client,
            f"{TECHNICIAN_TICKETS_URL}/{accepted_ticket.id}/status",
            {"status": "done"},
            technician_token,
        )
        assert finished.status_code == 200
        assert finished.get_json()["ticket"]["status"] == "done"

    def test_technician_cannot_mark_ticket_done_before_in_progress(self, client, technician_token, accepted_ticket):
        resp = patch_json(
            client,
            f"{TECHNICIAN_TICKETS_URL}/{accepted_ticket.id}/status",
            {"status": "done"},
            technician_token,
        )

        assert resp.status_code == 400
        assert "invalid ticket status transition" in resp.get_json()["message"].lower()

    def test_technician_status_update_notifies_manager_and_tenant(
        self, client, technician_token, accepted_ticket, tenant_user, manager_user
    ):
        resp = patch_json(
            client,
            f"{TECHNICIAN_TICKETS_URL}/{accepted_ticket.id}/status",
            {"status": "in_progress"},
            technician_token,
        )
        assert resp.status_code == 200

        tenant_notifications = Notification.query.filter_by(user_id=tenant_user.id).all()
        manager_notifications = Notification.query.filter_by(user_id=manager_user.id).all()
        assert any("in progress" in notification.message.lower() for notification in tenant_notifications)
        assert any("in progress" in notification.message.lower() for notification in manager_notifications)

    def test_technician_status_update_returns_conflict_after_manager_invalidates(
        self, client, technician_token, manager_token, accepted_ticket
    ):
        started = patch_json(
            client,
            f"{TECHNICIAN_TICKETS_URL}/{accepted_ticket.id}/status",
            {"status": "in_progress"},
            technician_token,
        )
        assert started.status_code == 200

        invalidated = patch_json(
            client,
            f"{MANAGER_ASSIGN_URL}/{accepted_ticket.id}/invalid",
            {},
            manager_token,
        )
        assert invalidated.status_code == 200

        finished = patch_json(
            client,
            f"{TECHNICIAN_TICKETS_URL}/{accepted_ticket.id}/status",
            {"status": "done"},
            technician_token,
        )
        assert finished.status_code == 409
        assert "updated by another action" in finished.get_json()["message"].lower()


class TestTechnicianBiddingFlow:

    def test_technician_sees_only_matching_service_area_tickets(
        self, client, technician_token, manager_ticket, non_matching_ticket
    ):
        resp = client.get(
            "/api/technician/tickets/service-area",
            headers={"Authorization": f"Bearer {technician_token}"},
        )
        assert resp.status_code == 200
        ticket_ids = [item["id"] for item in resp.get_json()["tickets"]]
        assert manager_ticket.id in ticket_ids
        assert non_matching_ticket.id not in ticket_ids

    def test_service_area_list_supports_search_and_pagination(
        self, client, technician_token, manager_ticket, tenant_user
    ):
        for index in range(4):
            db.session.add(
                Ticket(
                    title=f"Water leak case {index}",
                    description="Leak in utility section",
                    priority=TicketPriority.MEDIUM,
                    created_by=tenant_user.id,
                    service_tag_id=manager_ticket.service_tag_id,
                )
            )
        db.session.commit()

        resp = client.get(
            "/api/technician/tickets/service-area",
            headers={"Authorization": f"Bearer {technician_token}"},
            query_string={"q": "water leak", "page": 1, "page_size": 2},
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert len(body["tickets"]) == 2
        assert body["pagination"]["total"] >= 4

    def test_technician_can_submit_bid_for_matching_ticket(
        self, client, technician_token, manager_ticket
    ):
        resp = post_json(
            client,
            f"{TECHNICIAN_TICKETS_URL}/{manager_ticket.id}/bids",
            {"proposed_price": 240.5, "message": "Can complete in one visit."},
            technician_token,
        )
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["success"] is True
        assert body["bid"]["proposed_price"] == 240.5

    def test_technician_can_preview_service_area_ticket_without_comments(
        self, client, technician_token, manager_token, manager_ticket
    ):
        # Seed at least one manager comment; preview must still hide comments.
        comment_resp = post_json(
            client,
            f"{MANAGER_BIDS_URL}/{manager_ticket.id}/comments",
            {"body": "Internal manager note before assignment."},
            manager_token,
        )
        assert comment_resp.status_code == 201

        resp = client.get(
            f"/api/technician/tickets/service-area/{manager_ticket.id}",
            headers={"Authorization": f"Bearer {technician_token}"},
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["ticket"]["id"] == manager_ticket.id
        assert "comments" not in body["ticket"]

    def test_technician_cannot_preview_service_area_ticket_after_assignment(
        self, client, technician_token, manager_token, manager_ticket, technician_user
    ):
        assigned = patch_json(
            client,
            f"{MANAGER_ASSIGN_URL}/{manager_ticket.id}/assign",
            {"technician_id": technician_user.id},
            manager_token,
        )
        assert assigned.status_code == 200

        resp = client.get(
            f"/api/technician/tickets/service-area/{manager_ticket.id}",
            headers={"Authorization": f"Bearer {technician_token}"},
        )
        assert resp.status_code == 400
        assert "open unassigned" in resp.get_json()["message"].lower()

    def test_manager_can_view_ticket_bids_with_technician_profile(
        self, client, technician_token, manager_token, manager_ticket
    ):
        bid_resp = post_json(
            client,
            f"{TECHNICIAN_TICKETS_URL}/{manager_ticket.id}/bids",
            {"proposed_price": 180, "message": "Available tomorrow morning."},
            technician_token,
        )
        assert bid_resp.status_code == 201

        resp = client.get(
            f"{MANAGER_BIDS_URL}/{manager_ticket.id}/bids",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert len(body["bids"]) == 1
        assert body["bids"][0]["technician"]["name"] == "Tech"
