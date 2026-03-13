import enum
from uuid import uuid4
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


technician_service_links = db.Table(
    "technician_service_links",
    db.Column("technician_id", db.String(36), db.ForeignKey("users.id"), primary_key=True),
    db.Column("service_id", db.String(36), db.ForeignKey("technician_services.id"), primary_key=True),
)


# ---------------------------------------------------
# ENUMS
# ---------------------------------------------------

class UserRole(enum.Enum):
    TENANT = "tenant"
    MANAGER = "manager"
    TECHNICIAN = "technician"


class TicketStatus(enum.Enum):
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    INVALID = "invalid"


class TicketPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class InvitationStatus(enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


# ---------------------------------------------------
# USERS
# ---------------------------------------------------

class Users(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole, name="user_roles"), nullable=False)
    profile_image_path = db.Column(db.String(500), nullable=True)
    phone = db.Column(db.String(40), nullable=True)
    pincode = db.Column(db.String(12), nullable=True)
    location = db.Column(db.String(120), nullable=True)
    bio = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant_profile = db.relationship(
        "TenantProfile",
        back_populates="user",
        foreign_keys="TenantProfile.user_id",
        uselist=False,
        lazy=True,
        cascade="all, delete-orphan",
    )
    manager_profile = db.relationship(
        "ManagerProfile",
        backref="user",
        uselist=False,
        lazy=True,
        cascade="all, delete-orphan",
    )
    technician_profile = db.relationship(
        "TechnicianProfile",
        backref="user",
        uselist=False,
        lazy=True,
        cascade="all, delete-orphan",
    )
    created_tickets = db.relationship(
        "Ticket", foreign_keys="Ticket.created_by", backref="creator", lazy=True
    )
    assigned_tickets = db.relationship(
        "Ticket", foreign_keys="Ticket.assigned_to", backref="technician", lazy=True
    )
    notifications = db.relationship("Notification", backref="user", lazy=True)
    services = db.relationship(
        "TechnicianService",
        secondary=technician_service_links,
        lazy="subquery",
        backref=db.backref("technicians", lazy=True),
    )
    received_reviews = db.relationship(
        "TechnicianReview",
        foreign_keys="TechnicianReview.technician_id",
        backref="technician_user",
        lazy=True,
        cascade="all, delete-orphan",
    )
    given_reviews = db.relationship(
        "TechnicianReview",
        foreign_keys="TechnicianReview.reviewer_id",
        backref="reviewer_user",
        lazy=True,
    )

    __table_args__ = (
        # email already has a unique index via unique=True — no need for ix_users_email
        db.Index("ix_users_role", "role"),
    )

    # ---------------------------------------------------
    # METHODS
    # ---------------------------------------------------

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def is_manager(self):
        return self.role == UserRole.MANAGER

    def is_tenant(self):
        return self.role == UserRole.TENANT

    def is_technician(self):
        return self.role == UserRole.TECHNICIAN

    def can_manage_tickets(self):
        return self.is_manager()

    def assignable(self):
        return self.is_technician()

    def get_managed_tickets(self):
        """Manager fetches tickets created by their tenants (derived, not stored)."""
        return (
            db.session.execute(
                db.select(Ticket)
                .join(Users, Ticket.created_by == Users.id)
                .join(TenantProfile, TenantProfile.user_id == Users.id)
                .filter(TenantProfile.manager_id == self.id)
                .order_by(Ticket.created_at.desc())
            )
            .scalars()
            .all()
        )

    def __repr__(self):
        return f"<User {self.email} ({self.role.value})>"

    @property
    def manager_id(self):
        return self.tenant_profile.manager_id if self.tenant_profile else None

    @manager_id.setter
    def manager_id(self, value):
        if self.tenant_profile is None:
            self.tenant_profile = TenantProfile(user_id=self.id)
        self.tenant_profile.manager_id = value

    @property
    def manager(self):
        return self.tenant_profile.manager_user if self.tenant_profile else None

    @property
    def managed_tenants(self):
        return (
            db.session.execute(
                db.select(Users)
                .join(TenantProfile, TenantProfile.user_id == Users.id)
                .filter(TenantProfile.manager_id == self.id)
                .order_by(Users.name)
            )
            .scalars()
            .all()
        )

    @property
    def years_experience(self):
        return self.technician_profile.years_experience if self.technician_profile else None

    @years_experience.setter
    def years_experience(self, value):
        if self.technician_profile is None:
            self.technician_profile = TechnicianProfile(user_id=self.id)
        self.technician_profile.years_experience = value

    @property
    def base_price(self):
        return self.technician_profile.base_price if self.technician_profile else None

    @base_price.setter
    def base_price(self, value):
        if self.technician_profile is None:
            self.technician_profile = TechnicianProfile(user_id=self.id)
        self.technician_profile.base_price = value

    @property
    def technician_headline(self):
        return self.technician_profile.technician_headline if self.technician_profile else None

    @technician_headline.setter
    def technician_headline(self, value):
        if self.technician_profile is None:
            self.technician_profile = TechnicianProfile(user_id=self.id)
        self.technician_profile.technician_headline = value

    @property
    def service_pincode(self):
        return self.technician_profile.service_pincode if self.technician_profile else None

    @service_pincode.setter
    def service_pincode(self, value):
        if self.technician_profile is None:
            self.technician_profile = TechnicianProfile(user_id=self.id)
        self.technician_profile.service_pincode = value

    @property
    def average_rating(self):
        if not self.received_reviews:
            return None
        total = sum(review.rating for review in self.received_reviews)
        return round(total / len(self.received_reviews), 2)

    @property
    def reviews_count(self):
        return len(self.received_reviews)


class TenantProfile(db.Model):
    __tablename__ = "tenant_profiles"

    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), primary_key=True)
    manager_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)

    user = db.relationship("Users", foreign_keys=[user_id], back_populates="tenant_profile")
    manager_user = db.relationship("Users", foreign_keys=[manager_id])

    __table_args__ = (
        db.Index("ix_tenant_profile_manager", "manager_id"),
    )


class ManagerProfile(db.Model):
    __tablename__ = "manager_profiles"

    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), primary_key=True)


class TechnicianProfile(db.Model):
    __tablename__ = "technician_profiles"

    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), primary_key=True)
    years_experience = db.Column(db.Integer, nullable=True)
    base_price = db.Column(db.Float, nullable=True)
    technician_headline = db.Column(db.String(180), nullable=True)
    service_pincode = db.Column(db.String(12), nullable=True)


# Backward compatibility alias for existing imports in APIs/tests.
User = Users


# ---------------------------------------------------
# TICKETS
# ---------------------------------------------------

class Ticket(db.Model):
    __tablename__ = "tickets"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)

    status = db.Column(
        db.Enum(TicketStatus, name="ticket_status"),
        default=TicketStatus.OPEN, nullable=False,
    )
    priority = db.Column(
        db.Enum(TicketPriority, name="ticket_priority"),
        default=TicketPriority.MEDIUM, nullable=False,
    )
    service_tag_id = db.Column(db.String(36), db.ForeignKey("technician_services.id"), nullable=True)

    # created_by = tenant,  assigned_to = technician
    # manager is derived: self.creator.manager
    created_by = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    assigned_to = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)
    technician_request_pending = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    images = db.relationship(
        "TicketImage", backref="ticket", cascade="all, delete-orphan", lazy=True
    )
    activity_logs = db.relationship(
        "ActivityLog", backref="ticket", cascade="all, delete-orphan", lazy=True
    )
    comments = db.relationship(
        "TicketComment", backref="ticket", cascade="all, delete-orphan", lazy=True
    )
    bids = db.relationship(
        "TicketBid", backref="ticket", cascade="all, delete-orphan", lazy=True
    )
    service_tag = db.relationship("TechnicianService")

    __table_args__ = (
        db.Index("ix_ticket_status", "status"),
        db.Index("ix_ticket_priority", "priority"),
        db.Index("ix_ticket_created_by", "created_by"),
        db.Index("ix_ticket_assigned_to", "assigned_to"),
    )

    # ---------------------------------------------------
    # WORKFLOW
    # ---------------------------------------------------

    VALID_TRANSITIONS = {
        TicketStatus.OPEN: [TicketStatus.ASSIGNED, TicketStatus.INVALID],
        TicketStatus.ASSIGNED: [TicketStatus.IN_PROGRESS, TicketStatus.INVALID],
        TicketStatus.IN_PROGRESS: [TicketStatus.DONE, TicketStatus.INVALID],
        TicketStatus.DONE: [],
        TicketStatus.INVALID: [],
    }

    def can_transition(self, new_status: TicketStatus) -> bool:
        return new_status in self.VALID_TRANSITIONS[self.status]

    def update_status(self, new_status: TicketStatus, user):
        if not self.can_transition(new_status):
            raise ValueError("Invalid ticket status transition")
        old = self.status
        self.status = new_status
        ActivityLog.create(
            ticket_id=self.id, user_id=user.id,
            action=f"Status changed from {old.value} → {new_status.value}",
        )

    def assign_technician(self, technician, manager):
        if not technician.is_technician():
            raise ValueError("User is not a technician")
        self.assigned_to = technician.id
        self.status = TicketStatus.ASSIGNED
        ActivityLog.create(
            ticket_id=self.id, user_id=manager.id,
            action=f"Assigned to technician {technician.name}",
        )
        Notification.create(
            user_id=technician.id,
            message=f"You were assigned ticket '{self.title}'",
        )

    def update_priority(self, new_priority, user):
        old = self.priority
        self.priority = new_priority
        ActivityLog.create(
            ticket_id=self.id, user_id=user.id,
            action=f"Priority changed from {old.value} → {new_priority.value}",
        )

    def add_image(self, path):
        image = TicketImage(ticket_id=self.id, file_path=path)
        db.session.add(image)

    def add_comment(self, user, body):
        comment = TicketComment(ticket_id=self.id, user_id=user.id, body=body)
        db.session.add(comment)
        return comment

    def request_technician(self, technician, manager):
        if not technician.is_technician():
            raise ValueError("User is not a technician")
        if self.status in [TicketStatus.DONE, TicketStatus.INVALID]:
            raise ValueError("Cannot request technician for completed or invalid tickets")
        self.assigned_to = technician.id
        self.technician_request_pending = True
        self.status = TicketStatus.OPEN
        ActivityLog.create(
            ticket_id=self.id,
            user_id=manager.id,
            action=f"Sent technician request to {technician.name}",
        )

    def mark_invalid(self, user):
        if self.status != TicketStatus.INVALID:
            old = self.status
            self.status = TicketStatus.INVALID
            ActivityLog.create(
                ticket_id=self.id,
                user_id=user.id,
                action=f"Status changed from {old.value} → invalid",
            )
        return self

    def __repr__(self):
        return f"<Ticket {self.id} {self.status.value}>"


# ---------------------------------------------------
# TICKET IMAGES
# ---------------------------------------------------

class TicketImage(db.Model):
    __tablename__ = "ticket_images"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    ticket_id = db.Column(db.String(36), db.ForeignKey("tickets.id"), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.Index("ix_ticket_image_ticket", "ticket_id"),
    )

    def __repr__(self):
        return f"<TicketImage {self.file_path}>"


# ---------------------------------------------------
# TECHNICIAN SERVICES
# ---------------------------------------------------

class TechnicianService(db.Model):
    __tablename__ = "technician_services"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    code = db.Column(db.String(80), nullable=False, unique=True)
    label = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(255), nullable=True)

    __table_args__ = (
        db.Index("ix_technician_service_code", "code"),
    )

    def __repr__(self):
        return f"<TechnicianService {self.code}>"


# ---------------------------------------------------
# TECHNICIAN REVIEWS
# ---------------------------------------------------

class TechnicianReview(db.Model):
    __tablename__ = "technician_reviews"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    technician_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    reviewer_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    ticket_id = db.Column(db.String(36), db.ForeignKey("tickets.id"), nullable=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ticket = db.relationship("Ticket")

    __table_args__ = (
        db.Index("ix_technician_review_technician", "technician_id"),
        db.Index("ix_technician_review_reviewer", "reviewer_id"),
        db.UniqueConstraint(
            "technician_id",
            "reviewer_id",
            name="uq_technician_review_once_per_reviewer",
        ),
    )

    def __repr__(self):
        return f"<TechnicianReview {self.technician_id} {self.rating}>"


class TicketBid(db.Model):
    __tablename__ = "ticket_bids"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    ticket_id = db.Column(db.String(36), db.ForeignKey("tickets.id"), nullable=False)
    technician_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    proposed_price = db.Column(db.Float, nullable=False)
    message = db.Column(db.String(500), nullable=True)
    is_selected_for_request = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    technician = db.relationship("Users", foreign_keys=[technician_id])

    __table_args__ = (
        db.UniqueConstraint("ticket_id", "technician_id", name="uq_ticket_bid_ticket_technician"),
        db.Index("ix_ticket_bid_ticket", "ticket_id"),
        db.Index("ix_ticket_bid_technician", "technician_id"),
    )

    def __repr__(self):
        return f"<TicketBid {self.ticket_id} {self.technician_id} {self.proposed_price}>"


# ---------------------------------------------------
# TICKET COMMENTS
# ---------------------------------------------------

class TicketComment(db.Model):
    __tablename__ = "ticket_comments"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    ticket_id = db.Column(db.String(36), db.ForeignKey("tickets.id"), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("Users")

    __table_args__ = (
        db.Index("ix_ticket_comment_ticket", "ticket_id"),
        db.Index("ix_ticket_comment_user", "user_id"),
    )

    def __repr__(self):
        return f"<TicketComment {self.ticket_id} {self.user_id}>"


# ---------------------------------------------------
# ACTIVITY LOG
# ---------------------------------------------------

class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    ticket_id = db.Column(db.String(36), db.ForeignKey("tickets.id"), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("Users")

    __table_args__ = (
        db.Index("ix_activity_ticket", "ticket_id"),
        db.Index("ix_activity_user", "user_id"),
    )

    @staticmethod
    def create(ticket_id, user_id, action):
        log = ActivityLog(ticket_id=ticket_id, user_id=user_id, action=action)
        db.session.add(log)
        return log


# ---------------------------------------------------
# NOTIFICATIONS
# ---------------------------------------------------

class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.Index("ix_notification_user", "user_id"),
        db.Index("ix_notification_read", "is_read"),
    )

    @staticmethod
    def create(user_id, message):
        notif = Notification(user_id=user_id, message=message)
        db.session.add(notif)
        return notif

    def mark_read(self):
        self.is_read = True


# ---------------------------------------------------
# MANAGER REQUESTS
# ---------------------------------------------------

class ManagementInvitation(db.Model):
    __tablename__ = "management_invitations"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))

    manager_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    tenant_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)

    status = db.Column(
        db.Enum(InvitationStatus, name="invitation_status"),
        default=InvitationStatus.PENDING, nullable=False,
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    manager_user = db.relationship("Users", foreign_keys=[manager_id], backref="sent_invitations")
    tenant_user = db.relationship("Users", foreign_keys=[tenant_id], backref="received_invitations")

    __table_args__ = (
        db.UniqueConstraint("manager_id", "tenant_id", name="uq_management_invitation"),
        db.Index("ix_mgmt_invitation_manager", "manager_id"),
        db.Index("ix_mgmt_invitation_tenant", "tenant_id"),
        db.Index("ix_mgmt_invitation_status", "status"),
    )

    def accept(self):
        if self.status != InvitationStatus.PENDING:
            raise ValueError("Can only accept a pending invitation.")
        self.status = InvitationStatus.ACCEPTED
        self.tenant_user.manager_id = self.manager_id
        Notification.create(
            user_id=self.manager_id,
            message=f"{self.tenant_user.name} accepted your management request.",
        )

    def reject(self):
        if self.status != InvitationStatus.PENDING:
            raise ValueError("Can only reject a pending invitation.")
        self.status = InvitationStatus.REJECTED
        Notification.create(
            user_id=self.manager_id,
            message=f"{self.tenant_user.name} rejected your management request.",
        )

    def __repr__(self):
        return f"<ManagementInvitation {self.manager_id} → {self.tenant_id} ({self.status.value})>"
