
import enum
from uuid import uuid4
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


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


class TicketPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ---------------------------------------------------
# USERS
# ---------------------------------------------------

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole, name="user_roles"), nullable=False)

    # Self-referential FK: tenants point to their manager
    manager_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    managed_tenants = db.relationship(
        "User",
        backref=db.backref("manager", remote_side="User.id"),
        lazy=True,
    )
    created_tickets = db.relationship(
        "Ticket", foreign_keys="Ticket.created_by", backref="creator", lazy=True
    )
    assigned_tickets = db.relationship(
        "Ticket", foreign_keys="Ticket.assigned_to", backref="technician", lazy=True
    )
    notifications = db.relationship("Notification", backref="user", lazy=True)

    __table_args__ = (
        # email already has a unique index via unique=True — no need for ix_users_email
        db.Index("ix_users_role", "role"),
        db.Index("ix_users_manager", "manager_id"),
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
            Ticket.query
            .join(User, Ticket.created_by == User.id)
            .filter(User.manager_id == self.id)
            .all()
        )

    def __repr__(self):
        return f"<User {self.email} ({self.role.value})>"


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

    # created_by = tenant,  assigned_to = technician
    # manager is derived: self.creator.manager
    created_by = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    assigned_to = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    images = db.relationship(
        "TicketImage", backref="ticket", cascade="all, delete-orphan", lazy=True
    )
    activity_logs = db.relationship(
        "ActivityLog", backref="ticket", cascade="all, delete-orphan", lazy=True
    )

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
        TicketStatus.OPEN: [TicketStatus.ASSIGNED],
        TicketStatus.ASSIGNED: [TicketStatus.IN_PROGRESS],
        TicketStatus.IN_PROGRESS: [TicketStatus.DONE],
        TicketStatus.DONE: [],
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
# ACTIVITY LOG
# ---------------------------------------------------

class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    ticket_id = db.Column(db.String(36), db.ForeignKey("tickets.id"), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User")

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
