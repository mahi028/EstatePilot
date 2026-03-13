from flask_restful import Resource
from flask import request, current_app
from flask_jwt_extended import jwt_required, current_user, get_jwt
import re

from app.models import (
    db,
    User,
    UserRole,
    TenantProfile,
    ManagerProfile,
    TechnicianProfile,
    Ticket,
    TicketStatus,
    TechnicianService,
    TechnicianReview,
)
from app.forms import RegisterForm, LoginForm
from app.jwt_config import generate_tokens
from app.utils.upload import get_uploader


PREDEFINED_TECHNICIAN_SERVICES = [
    {
        "code": "electrical",
        "label": "Electrical Repairs",
        "description": "Wiring, outlets, breaker troubleshooting, and fixture installs.",
    },
    {
        "code": "plumbing",
        "label": "Plumbing",
        "description": "Leak fixes, pipe repairs, fittings, and water pressure issues.",
    },
    {
        "code": "hvac",
        "label": "HVAC",
        "description": "Heating and cooling diagnostics, servicing, and maintenance.",
    },
    {
        "code": "carpentry",
        "label": "Carpentry",
        "description": "Doors, cabinets, trim, and structural woodwork.",
    },
    {
        "code": "painting",
        "label": "Painting",
        "description": "Interior and exterior painting with surface prep.",
    },
    {
        "code": "appliance_repair",
        "label": "Appliance Repair",
        "description": "Diagnosis and repair of common household appliances.",
    },
    {
        "code": "general_maintenance",
        "label": "General Maintenance",
        "description": "Routine inspections, fixes, and upkeep work.",
    },
]


def _serialize_service(service):
    return {
        "id": service.id,
        "code": service.code,
        "label": service.label,
        "description": service.description,
    }


def _serialize_review(review):
    return {
        "id": review.id,
        "rating": review.rating,
        "comment": review.comment,
        "created_at": review.created_at.isoformat() if review.created_at else None,
        "reviewer": {
            "id": review.reviewer_user.id,
            "name": review.reviewer_user.name,
            "role": review.reviewer_user.role.value,
        },
    }


def _reviewer_has_existing_review(reviewer, technician):
    if not reviewer or not technician:
        return False
    existing = db.session.execute(
        db.select(TechnicianReview.id).filter_by(
            technician_id=technician.id,
            reviewer_id=reviewer.id,
        )
    ).first()
    return existing is not None


def _serialize_user(user, include_profile=False, include_reviews=False, reviewer=None):
    data = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role.value,
        "manager_id": user.manager_id,
        "profile_image_path": user.profile_image_path,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }

    if include_profile:
        data.update(
            {
                "phone": user.phone,
                "pincode": user.pincode,
                "location": user.location,
                "bio": user.bio,
                "years_experience": user.years_experience,
                "base_price": user.base_price,
                "technician_headline": user.technician_headline,
                "service_pincode": user.service_pincode,
                "services": [_serialize_service(service) for service in user.services],
                "average_rating": user.average_rating,
                "reviews_count": user.reviews_count,
            }
        )
        if user.is_technician():
            data["can_review"] = bool(
                reviewer
                and reviewer.id != user.id
                and _reviewer_can_review_technician(reviewer, user)
                and not _reviewer_has_existing_review(reviewer, user)
            )

    if include_reviews and user.is_technician():
        data["reviews"] = [
            _serialize_review(review)
            for review in sorted(user.received_reviews, key=lambda item: item.created_at or 0, reverse=True)
        ]

    return data


def _ensure_predefined_services():
    existing_codes = {
        item[0]
        for item in db.session.execute(db.select(TechnicianService.code)).all()
    }
    created = False
    for service in PREDEFINED_TECHNICIAN_SERVICES:
        if service["code"] in existing_codes:
            continue
        db.session.add(TechnicianService(**service))
        created = True
    if created:
        db.session.commit()


def _reviewer_can_review_technician(reviewer, technician):
    if reviewer.role not in {UserRole.TENANT, UserRole.MANAGER}:
        return False
    if not technician.is_technician():
        return False

    if reviewer.is_tenant():
        query = db.select(Ticket.id).filter(
            Ticket.assigned_to == technician.id,
            Ticket.created_by == reviewer.id,
            Ticket.status == TicketStatus.DONE,
        )
        return db.session.execute(query).first() is not None

    query = (
        db.select(Ticket.id)
        .join(User, Ticket.created_by == User.id)
        .join(TenantProfile, TenantProfile.user_id == User.id)
        .filter(
            Ticket.assigned_to == technician.id,
            TenantProfile.manager_id == reviewer.id,
            Ticket.status == TicketStatus.DONE,
        )
    )
    return db.session.execute(query).first() is not None


_PHONE_ALLOWED_RE = re.compile(r"^[0-9+()\-\s]+$")
_PINCODE_RE = re.compile(r"^[0-9]{4,10}$")


def _normalize_phone(value):
    phone = (value or "").strip()
    if not phone:
        return None
    if not _PHONE_ALLOWED_RE.fullmatch(phone):
        raise ValueError("Phone number can contain only digits, spaces, +, -, and parentheses")
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 7 or len(digits) > 15:
        raise ValueError("Phone number must contain between 7 and 15 digits")
    return phone


def _normalize_pincode(value, field_name="Pincode"):
    pincode = (value or "").strip()
    if not pincode:
        return None
    if not _PINCODE_RE.fullmatch(pincode):
        raise ValueError(f"{field_name} must be numeric and 4 to 10 digits long")
    return pincode


# --------------------------------------------------
# REGISTER
# --------------------------------------------------

class RegisterAPI(Resource):

    def post(self):

        form = RegisterForm(data=request.json)

        if not form.validate():
            return {
                "success": False,
                "errors": form.errors
            }, 400

        user = User(
            name=form.name.data,
            email=form.email.data,
            role=UserRole(form.role.data),
        )

        user.set_password(form.password.data)

        db.session.add(user)
        db.session.flush()

        if user.role == UserRole.TENANT:
            db.session.add(TenantProfile(user_id=user.id, manager_id=form.manager_id.data or None))
        elif user.role == UserRole.MANAGER:
            db.session.add(ManagerProfile(user_id=user.id))
        elif user.role == UserRole.TECHNICIAN:
            db.session.add(TechnicianProfile(user_id=user.id))

        db.session.commit()

        tokens = generate_tokens(user)

        return {
            "success": True,
            "message": "User registered successfully",
            "user": _serialize_user(user),
            **tokens
        }, 201


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

class LoginAPI(Resource):

    def post(self):

        form = LoginForm(data=request.json)

        if not form.validate():
            return {
                "success": False,
                "errors": form.errors
            }, 400

        user = db.session.execute(
            db.select(User).filter_by(email=form.email.data)
        ).scalar_one_or_none()

        if not user or not user.check_password(form.password.data):
            return {
                "success": False,
                "message": "Invalid email or password"
            }, 401

        tokens = generate_tokens(user)

        return {
            "success": True,
            "message": "Login successful",
            "user": _serialize_user(user),
            **tokens
        }, 200


# --------------------------------------------------
# TOKEN REFRESH
# --------------------------------------------------

class RefreshAPI(Resource):

    @jwt_required(refresh=True)
    def post(self):
        tokens = generate_tokens(current_user)
        return {
            "success": True,
            **tokens
        }, 200


# --------------------------------------------------
# CURRENT USER PROFILE
# --------------------------------------------------

class ProfileAPI(Resource):

    @jwt_required()
    def get(self):
        return {
            "success": True,
            "user": _serialize_user(current_user, include_profile=True, include_reviews=True, reviewer=current_user),
        }, 200

    @jwt_required()
    def patch(self):
        payload = request.json or {}

        for field in ["name", "location", "bio"]:
            if field in payload:
                setattr(current_user, field, (payload.get(field) or "").strip() or None)

        try:
            if "phone" in payload:
                current_user.phone = _normalize_phone(payload.get("phone"))
            if "pincode" in payload:
                current_user.pincode = _normalize_pincode(payload.get("pincode"), "Pincode")
        except ValueError as error:
            return {"success": False, "message": str(error)}, 400

        if "technician_headline" in payload:
            if not current_user.is_technician():
                return {"success": False, "message": "Only technicians can update technician headline"}, 403
            current_user.technician_headline = (payload.get("technician_headline") or "").strip() or None

        if "base_price" in payload:
            if not current_user.is_technician():
                return {"success": False, "message": "Only technicians can update base price"}, 403
            value = payload.get("base_price")
            current_user.base_price = float(value) if value not in (None, "") else None

        if "years_experience" in payload:
            if not current_user.is_technician():
                return {"success": False, "message": "Only technicians can update experience"}, 403
            value = payload.get("years_experience")
            years = int(value) if value not in (None, "") else None
            if years is not None and years < 0:
                return {"success": False, "message": "Experience cannot be negative"}, 400
            current_user.years_experience = years

        if "service_ids" in payload:
            if not current_user.is_technician():
                return {"success": False, "message": "Only technicians can select services"}, 403
            service_ids = payload.get("service_ids") or []
            services = db.session.execute(
                db.select(TechnicianService).filter(TechnicianService.id.in_(service_ids))
            ).scalars().all()
            if len(services) != len(service_ids):
                return {"success": False, "message": "Some services are invalid"}, 400
            current_user.services = services

        if "service_pincode" in payload:
            if not current_user.is_technician():
                return {"success": False, "message": "Only technicians can update service pincode"}, 403
            try:
                current_user.service_pincode = _normalize_pincode(payload.get("service_pincode"), "Service pincode")
            except ValueError as error:
                return {"success": False, "message": str(error)}, 400

        db.session.commit()

        return {
            "success": True,
            "message": "Profile updated",
            "user": _serialize_user(current_user, include_profile=True, include_reviews=True, reviewer=current_user),
        }, 200


class ProfileImageAPI(Resource):

    @jwt_required()
    def post(self):
        if "image" not in request.files:
            return {"success": False, "message": "No image provided"}, 400

        file = request.files["image"]
        if file.filename == "":
            return {"success": False, "message": "No image selected"}, 400

        try:
            uploader = get_uploader(
                current_app.config["UPLOAD_FOLDER"],
                current_app.config["ALLOWED_IMAGE_EXTENSIONS"],
            )
            path = uploader.save(file)
            if current_user.profile_image_path:
                uploader.delete(current_user.profile_image_path)
            current_user.profile_image_path = path
            db.session.commit()
            return {
                "success": True,
                "message": "Profile image updated",
                "user": _serialize_user(current_user, include_profile=True, include_reviews=True, reviewer=current_user),
            }, 200
        except ValueError as error:
            return {"success": False, "message": str(error)}, 400


class TechnicianServicesAPI(Resource):

    @jwt_required()
    def get(self):
        _ensure_predefined_services()
        services = db.session.execute(
            db.select(TechnicianService).order_by(TechnicianService.label)
        ).scalars().all()
        return {
            "success": True,
            "services": [_serialize_service(service) for service in services],
        }, 200


class UserProfileAPI(Resource):

    @jwt_required()
    def get(self, user_id):
        user = db.session.get(User, user_id)
        if not user:
            return {"success": False, "message": "User not found"}, 404

        include_reviews = user.is_technician()
        return {
            "success": True,
            "user": _serialize_user(user, include_profile=True, include_reviews=include_reviews, reviewer=current_user),
        }, 200


class TechnicianReviewsAPI(Resource):

    @jwt_required()
    def post(self, technician_id):
        technician = db.session.get(User, technician_id)
        if not technician or not technician.is_technician():
            return {"success": False, "message": "Technician not found"}, 404

        if not _reviewer_can_review_technician(current_user, technician):
            return {
                "success": False,
                "message": "You can only review technicians you have worked with",
            }, 403

        payload = request.json or {}
        rating = payload.get("rating")
        comment = (payload.get("comment") or "").strip()

        if not isinstance(rating, int) or rating < 0 or rating > 5:
            return {"success": False, "message": "Rating must be an integer between 0 and 5"}, 400
        if len(comment) < 5:
            return {"success": False, "message": "Comment must be at least 5 characters"}, 400

        existing = db.session.execute(
            db.select(TechnicianReview).filter_by(
                technician_id=technician.id,
                reviewer_id=current_user.id,
            )
        ).scalar_one_or_none()
        if existing:
            return {"success": False, "message": "You already reviewed this technician"}, 409

        review = TechnicianReview(
            technician_id=technician.id,
            reviewer_id=current_user.id,
            rating=rating,
            comment=comment,
        )
        db.session.add(review)
        db.session.commit()

        return {
            "success": True,
            "message": "Review added",
            "review": _serialize_review(review),
            "technician": _serialize_user(technician, include_profile=True, include_reviews=True, reviewer=current_user),
        }, 201