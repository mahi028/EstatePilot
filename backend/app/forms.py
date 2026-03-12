from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, SelectField
from wtforms.validators import (
    DataRequired,
    Email,
    Length,
    EqualTo,
    ValidationError,
    Optional
)

from flask_wtf.file import FileField, FileAllowed

from app.models import db, User, UserRole, TicketStatus, TicketPriority, ManagementInvitation, InvitationStatus


# ----------------------------------------------------
# AUTH FORMS
# ----------------------------------------------------

class RegisterForm(FlaskForm):

    name = StringField(
        "name",
        validators=[
            DataRequired(),
            Length(min=2, max=120)
        ]
    )

    email = StringField(
        "email",
        validators=[
            DataRequired(),
            Email(),
            Length(max=255)
        ]
    )

    password = PasswordField(
        "password",
        validators=[
            DataRequired(),
            Length(min=8, max=128)
        ]
    )

    confirm_password = PasswordField(
        "confirm_password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match")
        ]
    )

    role = SelectField(
        "role",
        choices=[
            ("tenant", "Tenant"),
            ("manager", "Manager"),
            ("technician", "Technician")
        ],
        validators=[DataRequired()]
    )

    manager_id = StringField(
        "manager_id",
        validators=[Optional()]
    )

    def validate_email(self, field):
        user = db.session.execute(
            db.select(User).filter_by(email=field.data)
        ).scalar_one_or_none()
        if user:
            raise ValidationError("Email already registered.")

    def validate_manager_id(self, field):
        if not field.data:
            return
        if self.role.data != UserRole.TENANT.value:
            raise ValidationError("Only tenants can be assigned to a manager.")
        manager = db.session.get(User, field.data)
        if not manager:
            raise ValidationError("Manager not found.")
        if not manager.is_manager():
            raise ValidationError("Specified user is not a manager.")


class LoginForm(FlaskForm):

    email = StringField(
        "email",
        validators=[
            DataRequired(),
            Email()
        ]
    )

    password = PasswordField(
        "password",
        validators=[DataRequired()]
    )


# ----------------------------------------------------
# TICKET CREATION
# ----------------------------------------------------

class CreateTicketForm(FlaskForm):

    title = StringField(
        "title",
        validators=[
            DataRequired(),
            Length(min=5, max=200)
        ]
    )

    description = TextAreaField(
        "description",
        validators=[
            DataRequired(),
            Length(min=10)
        ]
    )

    priority = SelectField(
        "priority",
        choices=[
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High")
        ],
        default="medium"
    )

    image = FileField(
        "image",
        validators=[
            Optional(),
            FileAllowed(
                ["jpg", "jpeg", "png", "webp"],
                "Only image files allowed."
            )
        ]
    )


# ----------------------------------------------------
# ASSIGN TECHNICIAN
# ----------------------------------------------------

class AssignTechnicianForm(FlaskForm):

    technician_id = StringField(
        "technician_id",
        validators=[DataRequired()]
    )


# ----------------------------------------------------
# MANAGER REQUEST
# ----------------------------------------------------

class SendInvitationForm(FlaskForm):

    tenant_id = StringField(
        "tenant_id",
        validators=[DataRequired()]
    )

    def validate_tenant_id(self, field):
        tenant = db.session.get(User, field.data)
        if not tenant:
            raise ValidationError("Tenant not found.")
        if not tenant.is_tenant():
            raise ValidationError("Target user is not a tenant.")
        if tenant.manager_id:
            raise ValidationError("Tenant already has a manager.")

    def validate_technician_id(self, field):

        technician = db.session.get(User, field.data)

        if not technician:
            raise ValidationError("Technician not found.")

        if not technician.is_technician():
            raise ValidationError("User is not a technician.")


# ----------------------------------------------------
# UPDATE PRIORITY
# ----------------------------------------------------

class UpdatePriorityForm(FlaskForm):

    priority = SelectField(
        "priority",
        choices=[
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High")
        ],
        validators=[DataRequired()]
    )


# ----------------------------------------------------
# UPDATE STATUS
# ----------------------------------------------------

class UpdateStatusForm(FlaskForm):

    status = SelectField(
        "status",
        choices=[
            ("open", "Open"),
            ("assigned", "Assigned"),
            ("in_progress", "In Progress"),
            ("done", "Done")
        ],
        validators=[DataRequired()]
    )

    def validate_status(self, field):

        if field.data not in [
            status.value for status in TicketStatus
        ]:
            raise ValidationError("Invalid status value.")


# ----------------------------------------------------
# IMAGE UPLOAD
# ----------------------------------------------------

class UploadImageForm(FlaskForm):

    image = FileField(
        "image",
        validators=[
            DataRequired(),
            FileAllowed(
                ["jpg", "jpeg", "png", "webp"],
                "Invalid file type"
            )
        ]
    )