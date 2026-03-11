import pytest
from app.models import (
    db, User, UserRole, Ticket, TicketStatus, TicketPriority,
    TicketImage, ActivityLog, Notification,
)


# ===================================================
# USER MODEL
# ===================================================

class TestUserPassword:

    def test_set_and_check_password(self, make_user):
        user = make_user(password="s3cureP@ss")
        assert user.check_password("s3cureP@ss")
        assert not user.check_password("wrongpassword")

    def test_password_hash_is_not_plaintext(self, make_user):
        user = make_user(password="s3cureP@ss")
        assert user.password_hash != "s3cureP@ss"


class TestUserRoles:

    def test_is_manager(self, manager):
        assert manager.is_manager()
        assert not manager.is_tenant()
        assert not manager.is_technician()

    def test_is_tenant(self, tenant):
        assert tenant.is_tenant()
        assert not tenant.is_manager()

    def test_is_technician(self, technician):
        assert technician.is_technician()
        assert not technician.is_manager()

    def test_can_manage_tickets(self, manager, tenant):
        assert manager.can_manage_tickets()
        assert not tenant.can_manage_tickets()

    def test_assignable(self, technician, tenant):
        assert technician.assignable()
        assert not tenant.assignable()


class TestManagerTenantRelationship:

    def test_tenant_points_to_manager(self, manager, tenant):
        assert tenant.manager_id == manager.id
        assert tenant.manager.id == manager.id

    def test_manager_sees_tenants(self, manager, tenant):
        assert tenant in manager.managed_tenants

    def test_manager_has_no_manager(self, manager):
        assert manager.manager_id is None


class TestUserRepr:

    def test_repr(self, tenant):
        assert "tenant@example.com" in repr(tenant)
        assert "tenant" in repr(tenant)


# ===================================================
# TICKET MODEL
# ===================================================

@pytest.fixture()
def ticket(db, tenant):
    t = Ticket(
        title="Leaking faucet",
        description="Kitchen faucet leaks when turned on",
        created_by=tenant.id,
    )
    db.session.add(t)
    db.session.commit()
    return t


class TestTicketDefaults:

    def test_default_status_is_open(self, ticket):
        assert ticket.status == TicketStatus.OPEN

    def test_default_priority_is_medium(self, ticket):
        assert ticket.priority == TicketPriority.MEDIUM

    def test_assigned_to_is_none(self, ticket):
        assert ticket.assigned_to is None


class TestTicketTransitions:

    def test_open_to_assigned_is_valid(self, ticket):
        assert ticket.can_transition(TicketStatus.ASSIGNED)

    def test_open_to_in_progress_is_invalid(self, ticket):
        assert not ticket.can_transition(TicketStatus.IN_PROGRESS)

    def test_open_to_done_is_invalid(self, ticket):
        assert not ticket.can_transition(TicketStatus.DONE)

    def test_full_lifecycle(self, ticket, tenant, technician, manager):
        # OPEN → ASSIGNED
        ticket.assign_technician(technician, manager)
        db.session.commit()
        assert ticket.status == TicketStatus.ASSIGNED
        assert ticket.assigned_to == technician.id

        # ASSIGNED → IN_PROGRESS
        ticket.update_status(TicketStatus.IN_PROGRESS, technician)
        db.session.commit()
        assert ticket.status == TicketStatus.IN_PROGRESS

        # IN_PROGRESS → DONE
        ticket.update_status(TicketStatus.DONE, technician)
        db.session.commit()
        assert ticket.status == TicketStatus.DONE

    def test_invalid_transition_raises(self, ticket, tenant):
        with pytest.raises(ValueError, match="Invalid ticket status transition"):
            ticket.update_status(TicketStatus.DONE, tenant)


class TestTicketAssignment:

    def test_assign_non_technician_raises(self, ticket, tenant, manager):
        with pytest.raises(ValueError, match="User is not a technician"):
            ticket.assign_technician(tenant, manager)

    def test_assign_creates_activity_log(self, ticket, technician, manager):
        ticket.assign_technician(technician, manager)
        db.session.commit()
        logs = ActivityLog.query.filter_by(ticket_id=ticket.id).all()
        assert any("Assigned to technician" in log.action for log in logs)

    def test_assign_creates_notification(self, ticket, technician, manager):
        ticket.assign_technician(technician, manager)
        db.session.commit()
        notifs = Notification.query.filter_by(user_id=technician.id).all()
        assert len(notifs) == 1
        assert "assigned" in notifs[0].message.lower()


class TestTicketPriority:

    def test_update_priority_logs_change(self, ticket, manager):
        ticket.update_priority(TicketPriority.HIGH, manager)
        db.session.commit()
        assert ticket.priority == TicketPriority.HIGH
        logs = ActivityLog.query.filter_by(ticket_id=ticket.id).all()
        assert any("Priority changed" in log.action for log in logs)


class TestTicketImage:

    def test_add_image(self, ticket):
        ticket.add_image("/uploads/leak.jpg")
        db.session.commit()
        assert len(ticket.images) == 1
        assert ticket.images[0].file_path == "/uploads/leak.jpg"


class TestGetManagedTickets:

    def test_manager_gets_tenant_tickets(self, manager, tenant, ticket):
        tickets = manager.get_managed_tickets()
        assert ticket in tickets

    def test_other_manager_gets_nothing(self, make_user, ticket):
        other = make_user(name="Other Mgr", email="other@mgr.com", role=UserRole.MANAGER)
        assert other.get_managed_tickets() == []


# ===================================================
# ACTIVITY LOG
# ===================================================

class TestActivityLog:

    def test_create_static(self, ticket, tenant):
        log = ActivityLog.create(
            ticket_id=ticket.id,
            user_id=tenant.id,
            action="Test action",
        )
        db.session.commit()
        assert log.action == "Test action"
        assert log.ticket_id == ticket.id


# ===================================================
# NOTIFICATION
# ===================================================

class TestNotification:

    def test_create_and_mark_read(self, tenant):
        notif = Notification.create(user_id=tenant.id, message="Hello")
        db.session.commit()
        assert notif.is_read is False
        notif.mark_read()
        assert notif.is_read is True
