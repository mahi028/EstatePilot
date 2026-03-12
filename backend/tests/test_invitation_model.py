import pytest
from app.models import (
    db, User, UserRole, ManagementInvitation, InvitationStatus, Notification,
)


@pytest.fixture()
def free_tenant(make_user):
    """A tenant with no manager."""
    return make_user(name="Free Tenant", email="free@example.com", role=UserRole.TENANT)


@pytest.fixture()
def invitation(db, manager, free_tenant):
    inv = ManagementInvitation(manager_id=manager.id, tenant_id=free_tenant.id)
    db.session.add(inv)
    db.session.commit()
    return inv


# ===================================================
# INVITATION CREATION
# ===================================================

class TestInvitationCreation:

    def test_defaults_to_pending(self, invitation):
        assert invitation.status == InvitationStatus.PENDING

    def test_relationships_populated(self, invitation, manager, free_tenant):
        assert invitation.manager_user.id == manager.id
        assert invitation.tenant_user.id == free_tenant.id

    def test_manager_sees_sent_invitations(self, invitation, manager):
        assert invitation in manager.sent_invitations

    def test_tenant_sees_received_invitations(self, invitation, free_tenant):
        assert invitation in free_tenant.received_invitations

    def test_repr(self, invitation):
        r = repr(invitation)
        assert "ManagementInvitation" in r
        assert "pending" in r


# ===================================================
# ACCEPT
# ===================================================

class TestAcceptInvitation:

    def test_accept_sets_status(self, invitation):
        invitation.accept()
        db.session.commit()
        assert invitation.status == InvitationStatus.ACCEPTED

    def test_accept_assigns_manager_to_tenant(self, invitation, manager, free_tenant):
        assert free_tenant.manager_id is None
        invitation.accept()
        db.session.commit()
        assert free_tenant.manager_id == manager.id

    def test_accept_creates_notification_for_manager(self, invitation, manager):
        invitation.accept()
        db.session.commit()
        notifs = Notification.query.filter_by(user_id=manager.id).all()
        assert len(notifs) == 1
        assert "accepted" in notifs[0].message.lower()

    def test_accept_already_accepted_raises(self, invitation):
        invitation.accept()
        db.session.commit()
        with pytest.raises(ValueError, match="pending"):
            invitation.accept()

    def test_accept_rejected_invitation_raises(self, invitation):
        invitation.reject()
        db.session.commit()
        with pytest.raises(ValueError, match="pending"):
            invitation.accept()


# ===================================================
# REJECT
# ===================================================

class TestRejectInvitation:

    def test_reject_sets_status(self, invitation):
        invitation.reject()
        db.session.commit()
        assert invitation.status == InvitationStatus.REJECTED

    def test_reject_does_not_assign_manager(self, invitation, free_tenant):
        invitation.reject()
        db.session.commit()
        assert free_tenant.manager_id is None

    def test_reject_creates_notification_for_manager(self, invitation, manager):
        invitation.reject()
        db.session.commit()
        notifs = Notification.query.filter_by(user_id=manager.id).all()
        assert len(notifs) == 1
        assert "rejected" in notifs[0].message.lower()

    def test_reject_already_rejected_raises(self, invitation):
        invitation.reject()
        db.session.commit()
        with pytest.raises(ValueError, match="pending"):
            invitation.reject()

    def test_reject_accepted_invitation_raises(self, invitation):
        invitation.accept()
        db.session.commit()
        with pytest.raises(ValueError, match="pending"):
            invitation.reject()


# ===================================================
# INVITATION STATUS ENUM
# ===================================================

class TestInvitationStatusEnum:

    def test_values(self):
        assert InvitationStatus.PENDING.value == "pending"
        assert InvitationStatus.ACCEPTED.value == "accepted"
        assert InvitationStatus.REJECTED.value == "rejected"

    def test_member_count(self):
        assert len(InvitationStatus) == 3
