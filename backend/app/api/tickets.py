from flask_restful import Resource
from flask import request, current_app
from flask_jwt_extended import current_user
from sqlalchemy import func

from app.models import (
    db, User, TenantProfile, Ticket, TicketBid, TicketImage, TicketComment, TicketStatus, TicketPriority,
    ActivityLog, Notification, TechnicianService, UserRole, ManagementInvitation, InvitationStatus,
)
from app.api.auth import _ensure_predefined_services
from app.forms import CreateTicketForm
from app.utils.RBAC import roles_required
from app.utils.upload import get_uploader


def _serialize_comment(comment):
    return {
        "id": comment.id,
        "body": comment.body,
        "created_at": comment.created_at.isoformat() if comment.created_at else None,
        "user": {
            "id": comment.user.id,
            "name": comment.user.name,
            "email": comment.user.email,
            "role": comment.user.role.value,
        },
    }


def _serialize_ticket(ticket, with_images=False, with_comments=False, with_activity_logs=False):
    data = {
        "id": ticket.id,
        "title": ticket.title,
        "description": ticket.description,
        "status": ticket.status.value,
        "priority": ticket.priority.value,
        "service_tag": (
            {
                "id": ticket.service_tag.id,
                "code": ticket.service_tag.code,
                "label": ticket.service_tag.label,
            }
            if ticket.service_tag
            else None
        ),
        "technician_request_pending": ticket.technician_request_pending,
        "created_by": {
            "id": ticket.creator.id,
            "name": ticket.creator.name,
            "email": ticket.creator.email,
        },
        "assigned_to": (
            {
                "id": ticket.technician.id,
                "name": ticket.technician.name,
                "email": ticket.technician.email,
            }
            if ticket.technician
            else None
        ),
        "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
        "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
    }
    if with_images:
        data["images"] = [
            {
                "id": img.id,
                "file_path": img.file_path,
                "uploaded_at": img.uploaded_at.isoformat() if img.uploaded_at else None,
            }
            for img in ticket.images
        ]
    if with_comments:
        data["comments"] = [
            _serialize_comment(comment)
            for comment in sorted(ticket.comments, key=lambda item: item.created_at or 0)
        ]
    if with_activity_logs:
        data["activity_logs"] = [
            {
                "id": log.id,
                "action": log.action,
                "user_id": log.user_id,
                "user": {
                    "id": log.user.id,
                    "name": log.user.name,
                    "role": log.user.role.value,
                } if log.user else None,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in sorted(ticket.activity_logs, key=lambda item: item.created_at or 0, reverse=True)
        ]
    return data


def _normalized_issue_text(value):
    return " ".join((value or "").strip().lower().split())


def _pagination_args(default_size=10, max_size=50):
    try:
        page = max(int(request.args.get("page", 1)), 1)
    except (TypeError, ValueError):
        page = 1

    try:
        page_size = int(request.args.get("page_size", default_size))
    except (TypeError, ValueError):
        page_size = default_size
    page_size = max(1, min(page_size, max_size))
    return page, page_size


def _paginate_query(base_query, page, page_size):
    total = db.session.execute(
        db.select(func.count()).select_from(base_query.subquery())
    ).scalar_one()

    rows = db.session.execute(
        base_query.offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()

    return rows, {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": (total + page_size - 1) // page_size,
    }


def _ticket_conflict_response():
    return {
        "success": False,
        "message": "Ticket was updated by another action. Refresh and try again",
    }, 409


def _serialize_ticket_detail(ticket):
    return _serialize_ticket(
        ticket,
        with_images=True,
        with_comments=True,
        with_activity_logs=True,
    )


def _serialize_bid(bid):
    return {
        "id": bid.id,
        "ticket_id": bid.ticket_id,
        "proposed_price": bid.proposed_price,
        "message": bid.message,
        "is_selected_for_request": bid.is_selected_for_request,
        "created_at": bid.created_at.isoformat() if bid.created_at else None,
        "updated_at": bid.updated_at.isoformat() if bid.updated_at else None,
        "technician": {
            "id": bid.technician.id,
            "name": bid.technician.name,
            "email": bid.technician.email,
            "phone": bid.technician.phone,
            "location": bid.technician.location,
            "technician_headline": bid.technician.technician_headline,
            "base_price": bid.technician.base_price,
            "years_experience": bid.technician.years_experience,
            "average_rating": bid.technician.average_rating,
            "reviews_count": bid.technician.reviews_count,
            "services": [
                {
                    "id": service.id,
                    "code": service.code,
                    "label": service.label,
                }
                for service in bid.technician.services
            ],
        },
    }


def _get_ticket_for_manager(ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    creator = db.session.get(User, ticket.created_by) if ticket else None
    if not ticket or not creator or creator.manager_id != current_user.id:
        return None

    # If the manager-tenant relationship was established via invitation,
    # restrict visibility to tickets created after that acceptance time.
    accepted_since = db.session.execute(
        db.select(func.max(ManagementInvitation.updated_at)).filter(
            ManagementInvitation.manager_id == current_user.id,
            ManagementInvitation.tenant_id == creator.id,
            ManagementInvitation.status == InvitationStatus.ACCEPTED,
        )
    ).scalar_one()
    if accepted_since and ticket.created_at and ticket.created_at < accepted_since:
        return None

    return ticket


def _delete_ticket_images(ticket):
    uploader = get_uploader(
        current_app.config["UPLOAD_FOLDER"],
        current_app.config["ALLOWED_IMAGE_EXTENSIONS"],
    )
    for image in list(ticket.images):
        uploader.delete(image.file_path)


def _create_comment(ticket, user, body, notify_user_id=None):
    comment = ticket.add_comment(user, body)
    ActivityLog.create(
        ticket_id=ticket.id,
        user_id=user.id,
        action="Added comment",
    )
    if notify_user_id and notify_user_id != user.id:
        Notification.create(
            user_id=notify_user_id,
            message=f"New comment on ticket '{ticket.title}' from {user.name}",
        )
    db.session.commit()
    return comment


# --------------------------------------------------
# CREATE / LIST TICKETS (Tenant only)
# --------------------------------------------------

class TenantTicketsAPI(Resource):

    method_decorators = [roles_required(UserRole.TENANT)]

    def post(self):
        if not current_user.manager_id:
            return {
                "success": False,
                "message": "You must be assigned to a manager before creating tickets",
            }, 403

        _ensure_predefined_services()

        payload = request.get_json(silent=True) if request.is_json else request.form
        form = CreateTicketForm(data=payload)

        if not form.validate():
            return {"success": False, "errors": form.errors}, 400

        ticket = Ticket(
            title=form.title.data,
            description=form.description.data,
            priority=TicketPriority(form.priority.data),
            created_by=current_user.id,
        )

        service_tag = db.session.get(TechnicianService, form.service_tag_id.data)
        if not service_tag:
            return {"success": False, "message": "Invalid service tag"}, 400

        duplicate_ticket = db.session.execute(
            db.select(Ticket).filter(
                Ticket.created_by == current_user.id,
                Ticket.service_tag_id == service_tag.id,
                Ticket.status.in_([
                    TicketStatus.OPEN,
                    TicketStatus.ASSIGNED,
                    TicketStatus.IN_PROGRESS,
                ]),
            )
        ).scalars().all()

        new_title = _normalized_issue_text(form.title.data)
        if any(_normalized_issue_text(existing.title) == new_title for existing in duplicate_ticket):
            return {
                "success": False,
                "message": "You already have an active ticket for this issue and service tag",
            }, 409

        ticket.service_tag_id = service_tag.id

        db.session.add(ticket)
        db.session.flush()

        uploaded_count = 0
        files = request.files.getlist("images")
        if not files and "image" in request.files:
            files = [request.files["image"]]

        if files:
            uploader = get_uploader(
                current_app.config["UPLOAD_FOLDER"],
                current_app.config["ALLOWED_IMAGE_EXTENSIONS"],
            )
            for file in files:
                if not file or not getattr(file, "filename", ""):
                    continue
                file_path = uploader.save(file)
                db.session.add(TicketImage(ticket=ticket, file_path=file_path))
                uploaded_count += 1
            if uploaded_count:
                ActivityLog.create(
                    ticket_id=ticket.id,
                    user_id=current_user.id,
                    action=f"Uploaded {uploaded_count} image(s) on ticket creation",
                )

        # Notify the tenant's manager
        Notification.create(
            user_id=current_user.manager_id,
            message=f"New ticket '{ticket.title}' created by {current_user.name}",
        )

        try:
            db.session.commit()
        except ValueError as e:
            db.session.rollback()
            return {"success": False, "message": str(e)}, 400
        except Exception as e:
            db.session.rollback()
            return {
                "success": False,
                "message": f"Failed to create ticket: {str(e)}",
            }, 500

        return {
            "success": True,
            "message": "Ticket created",
            "ticket": _serialize_ticket(ticket),
        }, 201

    def get(self):
        status_filter = request.args.get("status")
        priority_filter = request.args.get("priority")
        q = request.args.get("q", "").strip()
        service_tag_id = request.args.get("service_tag_id", "").strip() or None
        page, page_size = _pagination_args(default_size=10)

        query = db.select(Ticket).filter_by(created_by=current_user.id)

        if status_filter:
            try:
                query = query.filter_by(status=TicketStatus(status_filter))
            except ValueError:
                return {"success": False, "message": "Invalid status filter"}, 400

        if priority_filter:
            try:
                query = query.filter_by(priority=TicketPriority(priority_filter))
            except ValueError:
                return {"success": False, "message": "Invalid priority filter"}, 400

        if service_tag_id:
            query = query.filter(Ticket.service_tag_id == service_tag_id)

        if q:
            query = query.filter(
                db.or_(
                    Ticket.title.ilike(f"%{q}%"),
                    Ticket.description.ilike(f"%{q}%"),
                )
            )

        query = query.order_by(Ticket.created_at.desc())
        tickets, pagination = _paginate_query(query, page, page_size)

        return {
            "success": True,
            "tickets": [_serialize_ticket(t) for t in tickets],
            "pagination": pagination,
        }, 200


# --------------------------------------------------
# SINGLE TICKET DETAIL (Tenant only — own tickets)
# --------------------------------------------------

class TenantTicketDetailAPI(Resource):

    method_decorators = [roles_required(UserRole.TENANT)]

    def get(self, ticket_id):
        ticket = db.session.get(Ticket, ticket_id)

        if not ticket or ticket.created_by != current_user.id:
            return {"success": False, "message": "Ticket not found"}, 404

        return {"success": True, "ticket": _serialize_ticket_detail(ticket)}, 200

    def patch(self, ticket_id):
        ticket = db.session.get(Ticket, ticket_id)

        if not ticket or ticket.created_by != current_user.id:
            return {"success": False, "message": "Ticket not found"}, 404

        data = request.json or {}
        updated = False

        if "description" in data:
            desc = data["description"].strip()
            if len(desc) < 10:
                return {"success": False, "message": "Description must be at least 10 characters"}, 400
            old = ticket.description
            ticket.description = desc
            if old != desc:
                ActivityLog.create(
                    ticket_id=ticket.id,
                    user_id=current_user.id,
                    action="Updated description",
                )
                updated = True

        if "priority" in data:
            try:
                new_priority = TicketPriority(data["priority"])
                if new_priority != ticket.priority:
                    ticket.update_priority(new_priority, current_user)
                    updated = True
            except ValueError:
                return {"success": False, "message": "Invalid priority"}, 400

        if updated:
            db.session.commit()

        return {"success": True, "ticket": _serialize_ticket_detail(ticket)}, 200

    def delete(self, ticket_id):
        ticket = db.session.get(Ticket, ticket_id)

        if not ticket or ticket.created_by != current_user.id:
            return {"success": False, "message": "Ticket not found"}, 404

        manager_id = ticket.creator.manager_id
        assigned_technician_id = ticket.assigned_to
        _delete_ticket_images(ticket)
        db.session.delete(ticket)

        if manager_id:
            Notification.create(
                user_id=manager_id,
                message=f"Ticket '{ticket.title}' was deleted by {current_user.name}",
            )

        if assigned_technician_id:
            Notification.create(
                user_id=assigned_technician_id,
                message=f"Ticket '{ticket.title}' was deleted by tenant {current_user.name}",
            )

        db.session.commit()
        return {"success": True, "message": "Ticket deleted"}, 200


# --------------------------------------------------
# MANAGED TENANTS LIST (Manager only)
# --------------------------------------------------

class ManagedTenantsAPI(Resource):

    method_decorators = [roles_required(UserRole.MANAGER)]

    def get(self):
        tenants = db.session.execute(
            db.select(User)
            .join(TenantProfile, TenantProfile.user_id == User.id)
            .filter(TenantProfile.manager_id == current_user.id)
            .order_by(User.name)
        ).scalars().all()

        return {
            "success": True,
            "tenants": [
                {
                    "id": t.id,
                    "name": t.name,
                    "email": t.email,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                }
                for t in tenants
            ],
        }, 200


# --------------------------------------------------
# MANAGED TICKETS LIST (Manager only — tickets from their tenants)
# --------------------------------------------------

class ManagedTicketsAPI(Resource):

    method_decorators = [roles_required(UserRole.MANAGER)]

    def get(self):
        status_filter = request.args.get("status")
        priority_filter = request.args.get("priority")
        q = request.args.get("q", "").strip()
        service_tag_id = request.args.get("service_tag_id", "").strip() or None
        page, page_size = _pagination_args(default_size=10)

        accepted_since_subquery = (
            db.select(func.max(ManagementInvitation.updated_at))
            .filter(
                ManagementInvitation.manager_id == current_user.id,
                ManagementInvitation.tenant_id == User.id,
                ManagementInvitation.status == InvitationStatus.ACCEPTED,
            )
            .correlate(User)
            .scalar_subquery()
        )

        query = (
            db.select(Ticket)
            .join(User, Ticket.created_by == User.id)
            .join(TenantProfile, TenantProfile.user_id == User.id)
            .filter(TenantProfile.manager_id == current_user.id)
            .filter(
                db.or_(
                    accepted_since_subquery.is_(None),
                    Ticket.created_at >= accepted_since_subquery,
                )
            )
        )

        if status_filter:
            try:
                query = query.filter(Ticket.status == TicketStatus(status_filter))
            except ValueError:
                return {"success": False, "message": "Invalid status filter"}, 400

        if priority_filter:
            try:
                query = query.filter(Ticket.priority == TicketPriority(priority_filter))
            except ValueError:
                return {"success": False, "message": "Invalid priority filter"}, 400

        if service_tag_id:
            query = query.filter(Ticket.service_tag_id == service_tag_id)

        if q:
            query = query.filter(
                db.or_(
                    Ticket.title.ilike(f"%{q}%"),
                    Ticket.description.ilike(f"%{q}%"),
                    User.name.ilike(f"%{q}%"),
                )
            )

        query = query.order_by(Ticket.created_at.desc())
        tickets, pagination = _paginate_query(query, page, page_size)

        return {
            "success": True,
            "tickets": [_serialize_ticket(t) for t in tickets],
            "pagination": pagination,
        }, 200


class ManagedTicketDetailAPI(Resource):

    method_decorators = [roles_required(UserRole.MANAGER)]

    def get(self, ticket_id):
        ticket = _get_ticket_for_manager(ticket_id)

        if not ticket:
            return {"success": False, "message": "Ticket not found"}, 404

        return {"success": True, "ticket": _serialize_ticket_detail(ticket)}, 200


class TenantTicketCommentsAPI(Resource):

    method_decorators = [roles_required(UserRole.TENANT)]

    def post(self, ticket_id):
        ticket = db.session.get(Ticket, ticket_id)

        if not ticket or ticket.created_by != current_user.id:
            return {"success": False, "message": "Ticket not found"}, 404

        body = (request.json or {}).get("body", "").strip()
        if not body:
            return {"success": False, "message": "Comment is required"}, 400

        comment = _create_comment(ticket, current_user, body, notify_user_id=ticket.creator.manager_id)
        return {
            "success": True,
            "message": "Comment added",
            "comment": _serialize_comment(comment),
            "ticket": _serialize_ticket_detail(ticket),
        }, 201


class ManagedTicketCommentsAPI(Resource):

    method_decorators = [roles_required(UserRole.MANAGER)]

    def post(self, ticket_id):
        ticket = _get_ticket_for_manager(ticket_id)

        if not ticket:
            return {"success": False, "message": "Ticket not found"}, 404

        body = (request.json or {}).get("body", "").strip()
        if not body:
            return {"success": False, "message": "Comment is required"}, 400

        comment = _create_comment(ticket, current_user, body, notify_user_id=ticket.created_by)
        return {
            "success": True,
            "message": "Comment added",
            "comment": _serialize_comment(comment),
            "ticket": _serialize_ticket_detail(ticket),
        }, 201


class ManagedTicketInvalidAPI(Resource):

    method_decorators = [roles_required(UserRole.MANAGER)]

    def patch(self, ticket_id):
        ticket = _get_ticket_for_manager(ticket_id)

        if not ticket:
            return {"success": False, "message": "Ticket not found"}, 404

        ticket.mark_invalid(current_user)
        Notification.create(
            user_id=ticket.created_by,
            message=f"Your ticket '{ticket.title}' was marked invalid by {current_user.name}",
        )
        if ticket.assigned_to:
            Notification.create(
                user_id=ticket.assigned_to,
                message=f"Ticket '{ticket.title}' was marked invalid by manager {current_user.name}",
            )
        db.session.commit()

        return {
            "success": True,
            "message": "Ticket marked invalid",
            "ticket": _serialize_ticket_detail(ticket),
        }, 200


# --------------------------------------------------
# UPLOAD TICKET IMAGE (Tenant only — own tickets)
# --------------------------------------------------


# --------------------------------------------------
# UPLOAD TICKET IMAGE (Tenant only — own tickets)
# --------------------------------------------------

class TicketImageUploadAPI(Resource):

    method_decorators = [roles_required(UserRole.TENANT)]

    def post(self, ticket_id):
        # Verify ticket exists and belongs to current user
        ticket = db.session.get(Ticket, ticket_id)
        if not ticket or ticket.created_by != current_user.id:
            return {"success": False, "message": "Ticket not found"}, 404

        # Check for file in request
        if "image" not in request.files:
            return {"success": False, "message": "No image provided"}, 400

        file = request.files["image"]
        if file.filename == "":
            return {"success": False, "message": "No image selected"}, 400

        try:
            # Use the upload utility to save the file
            uploader = get_uploader(
                current_app.config["UPLOAD_FOLDER"],
                current_app.config["ALLOWED_IMAGE_EXTENSIONS"],
            )
            file_path = uploader.save(file)

            # Create TicketImage record
            image = TicketImage(ticket_id=ticket.id, file_path=file_path)
            db.session.add(image)

            # Log activity
            ActivityLog.create(
                ticket_id=ticket.id,
                user_id=current_user.id,
                action="Uploaded image",
            )

            db.session.commit()

            return {
                "success": True,
                "message": "Image uploaded",
                "image": {
                    "id": image.id,
                    "ticket_id": image.ticket_id,
                    "file_path": image.file_path,
                    "uploaded_at": image.uploaded_at.isoformat() if image.uploaded_at else None,
                },
            }, 201

        except ValueError as e:
            return {"success": False, "message": str(e)}, 400
        except Exception as e:
            return {
                "success": False,
                "message": f"Upload failed: {str(e)}",
            }, 500


# --------------------------------------------------
# DELETE TICKET IMAGE (Tenant only — own tickets)
# --------------------------------------------------

class TicketImageDeleteAPI(Resource):

    method_decorators = [roles_required(UserRole.TENANT)]

    def delete(self, ticket_id, image_id):
        ticket = db.session.get(Ticket, ticket_id)
        if not ticket or ticket.created_by != current_user.id:
            return {"success": False, "message": "Ticket not found"}, 404

        image = db.session.get(TicketImage, image_id)
        if not image or image.ticket_id != ticket.id:
            return {"success": False, "message": "Image not found"}, 404

        # Delete file from storage
        uploader = get_uploader(
            current_app.config["UPLOAD_FOLDER"],
            current_app.config["ALLOWED_IMAGE_EXTENSIONS"],
        )
        uploader.delete(image.file_path)

        db.session.delete(image)
        ActivityLog.create(
            ticket_id=ticket.id,
            user_id=current_user.id,
            action="Deleted image",
        )
        db.session.commit()

        return {"success": True, "message": "Image deleted"}, 200


# --------------------------------------------------
# TECHNICIAN TICKETS (Technician only)
# --------------------------------------------------

class TechnicianTicketsAPI(Resource):

    method_decorators = [roles_required(UserRole.TECHNICIAN)]

    def get(self):
        """Get all tickets assigned to or requested for current technician"""
        status_filter = request.args.get("status")
        q = request.args.get("q", "").strip()
        page, page_size = _pagination_args(default_size=10)

        # Get tickets assigned to this technician
        query = db.select(Ticket).filter_by(assigned_to=current_user.id)

        if status_filter:
            try:
                query = query.filter_by(status=TicketStatus(status_filter))
            except ValueError:
                return {"success": False, "message": "Invalid status filter"}, 400

        if q:
            query = query.filter(
                db.or_(
                    Ticket.title.ilike(f"%{q}%"),
                    Ticket.description.ilike(f"%{q}%"),
                )
            )

        query = query.order_by(Ticket.created_at.desc())
        tickets, pagination = _paginate_query(query, page, page_size)

        return {
            "success": True,
            "tickets": [_serialize_ticket(t) for t in tickets],
            "pagination": pagination,
        }, 200


class TechnicianServiceAreaTicketsAPI(Resource):

    method_decorators = [roles_required(UserRole.TECHNICIAN)]

    def get(self):
        """Get open tickets matching technician service areas for bidding."""
        service_ids = [service.id for service in current_user.services]
        if not service_ids:
            return {
                "success": True,
                "tickets": [],
                "pagination": {"page": 1, "page_size": 10, "total": 0, "total_pages": 0},
            }, 200

        q = request.args.get("q", "").strip()
        page, page_size = _pagination_args(default_size=10)

        query = (
            db.select(Ticket)
            .filter(
                Ticket.status == TicketStatus.OPEN,
                Ticket.assigned_to.is_(None),
                Ticket.service_tag_id.in_(service_ids),
            )
            .order_by(Ticket.created_at.desc())
        )

        if q:
            query = query.filter(
                db.or_(
                    Ticket.title.ilike(f"%{q}%"),
                    Ticket.description.ilike(f"%{q}%"),
                )
            )

        tickets, pagination = _paginate_query(query, page, page_size)
        return {
            "success": True,
            "tickets": [_serialize_ticket(ticket) for ticket in tickets],
            "pagination": pagination,
        }, 200


class TechnicianServiceAreaTicketDetailAPI(Resource):

    method_decorators = [roles_required(UserRole.TECHNICIAN)]

    def get(self, ticket_id):
        """Read-only preview for open service-area tickets before assignment."""
        ticket = db.session.get(Ticket, ticket_id)
        if not ticket:
            return {"success": False, "message": "Ticket not found"}, 404

        service_ids = {service.id for service in current_user.services}
        if not ticket.service_tag_id or ticket.service_tag_id not in service_ids:
            return {"success": False, "message": "Ticket is outside your service areas"}, 403

        if ticket.status != TicketStatus.OPEN or ticket.assigned_to is not None:
            return {"success": False, "message": "Ticket preview is only available for open unassigned tickets"}, 400

        return {
            "success": True,
            "ticket": _serialize_ticket(
                ticket,
                with_images=True,
                with_comments=False,
                with_activity_logs=False,
            ),
        }, 200


class TechnicianTicketBidsAPI(Resource):

    method_decorators = [roles_required(UserRole.TECHNICIAN)]

    def post(self, ticket_id):
        ticket = db.session.get(Ticket, ticket_id)
        if not ticket:
            return {"success": False, "message": "Ticket not found"}, 404

        service_ids = {service.id for service in current_user.services}
        if not ticket.service_tag_id or ticket.service_tag_id not in service_ids:
            return {"success": False, "message": "Ticket is outside your service areas"}, 403

        if ticket.status != TicketStatus.OPEN or ticket.assigned_to is not None:
            return {"success": False, "message": "Bids are only allowed for open tickets"}, 400

        payload = request.json or {}
        raw_price = payload.get("proposed_price")
        message = (payload.get("message") or "").strip() or None

        try:
            proposed_price = float(raw_price)
            if proposed_price <= 0:
                raise ValueError()
        except (TypeError, ValueError):
            return {"success": False, "message": "proposed_price must be a positive number"}, 400

        bid = db.session.execute(
            db.select(TicketBid).filter_by(ticket_id=ticket.id, technician_id=current_user.id)
        ).scalar_one_or_none()

        created = False
        if bid is None:
            bid = TicketBid(
                ticket_id=ticket.id,
                technician_id=current_user.id,
                proposed_price=proposed_price,
                message=message,
            )
            db.session.add(bid)
            created = True
        else:
            bid.proposed_price = proposed_price
            bid.message = message

        ActivityLog.create(
            ticket_id=ticket.id,
            user_id=current_user.id,
            action="Submitted technician bid" if created else "Updated technician bid",
        )
        if ticket.creator and ticket.creator.manager_id:
            Notification.create(
                user_id=ticket.creator.manager_id,
                message=f"Technician {current_user.name} submitted a bid for '{ticket.title}'",
            )

        db.session.commit()
        return {
            "success": True,
            "message": "Bid submitted" if created else "Bid updated",
            "bid": _serialize_bid(bid),
        }, 201 if created else 200


class TechnicianTicketDetailAPI(Resource):

    method_decorators = [roles_required(UserRole.TECHNICIAN)]

    def get(self, ticket_id):
        """Get ticket details if assigned to current technician"""
        ticket = db.session.get(Ticket, ticket_id)

        if not ticket or ticket.assigned_to != current_user.id:
            return {"success": False, "message": "Ticket not found"}, 404

        return {"success": True, "ticket": _serialize_ticket_detail(ticket)}, 200


class TechnicianTicketAcceptAPI(Resource):

    method_decorators = [roles_required(UserRole.TECHNICIAN)]

    def patch(self, ticket_id):
        """Technician accepts a pending manager request and marks ticket assigned."""
        ticket = db.session.get(Ticket, ticket_id)

        if not ticket or ticket.assigned_to != current_user.id:
            return {"success": False, "message": "Ticket not found"}, 404

        if ticket.status in [TicketStatus.DONE, TicketStatus.INVALID]:
            return {"success": False, "message": "Cannot accept completed or invalid tickets"}, 400

        if not ticket.technician_request_pending:
            return {"success": False, "message": "This ticket request was already handled"}, 400

        updated = db.session.execute(
            db.update(Ticket)
            .where(
                Ticket.id == ticket.id,
                Ticket.assigned_to == current_user.id,
                Ticket.technician_request_pending.is_(True),
                Ticket.status.notin_([TicketStatus.DONE, TicketStatus.INVALID]),
            )
            .values(
                status=TicketStatus.ASSIGNED,
                technician_request_pending=False,
            )
        )
        if updated.rowcount != 1:
            db.session.rollback()
            return _ticket_conflict_response()

        ticket = db.session.get(Ticket, ticket_id)
        
        ActivityLog.create(
            ticket_id=ticket.id,
            user_id=current_user.id,
            action="Accepted technician request",
        )
        
        # Notify the tenant's manager
        if ticket.creator and ticket.creator.manager_id:
            Notification.create(
                user_id=ticket.creator.manager_id,
                message=f"Technician {current_user.name} accepted request for '{ticket.title}'",
            )

        db.session.commit()

        return {
            "success": True,
            "message": "Ticket accepted",
            "ticket": _serialize_ticket_detail(ticket),
        }, 200


class TechnicianTicketStatusAPI(Resource):

    method_decorators = [roles_required(UserRole.TECHNICIAN)]

    def patch(self, ticket_id):
        ticket = db.session.get(Ticket, ticket_id)

        if not ticket or ticket.assigned_to != current_user.id:
            return {"success": False, "message": "Ticket not found"}, 404

        if ticket.technician_request_pending:
            return {"success": False, "message": "Accept the ticket request before updating status"}, 400

        raw_status = ((request.json or {}).get("status") or "").strip()
        if not raw_status:
            return {"success": False, "message": "Status is required"}, 400

        try:
            new_status = TicketStatus(raw_status)
        except ValueError:
            return {"success": False, "message": "Invalid status"}, 400

        if new_status not in [TicketStatus.IN_PROGRESS, TicketStatus.DONE]:
            return {"success": False, "message": "Technicians can only mark tickets in progress or done"}, 400

        expected_from = TicketStatus.ASSIGNED if new_status == TicketStatus.IN_PROGRESS else TicketStatus.IN_PROGRESS

        updated = db.session.execute(
            db.update(Ticket)
            .where(
                Ticket.id == ticket.id,
                Ticket.assigned_to == current_user.id,
                Ticket.technician_request_pending.is_(False),
                Ticket.status == expected_from,
            )
            .values(status=new_status)
        )
        if updated.rowcount != 1:
            db.session.rollback()
            fresh = db.session.get(Ticket, ticket_id)
            if not fresh or fresh.assigned_to != current_user.id:
                return {"success": False, "message": "Ticket not found"}, 404
            if fresh.technician_request_pending:
                return {"success": False, "message": "Accept the ticket request before updating status"}, 400
            if fresh.status in [TicketStatus.DONE, TicketStatus.INVALID]:
                return _ticket_conflict_response()
            return {"success": False, "message": "Invalid ticket status transition"}, 400

        ticket = db.session.get(Ticket, ticket_id)
        ActivityLog.create(
            ticket_id=ticket.id,
            user_id=current_user.id,
            action=f"Status changed from {expected_from.value} -> {new_status.value}",
        )

        recipients = {ticket.created_by}
        if ticket.creator and ticket.creator.manager_id:
            recipients.add(ticket.creator.manager_id)

        for user_id in recipients:
            if user_id == current_user.id:
                continue
            Notification.create(
                user_id=user_id,
                message=f"Ticket '{ticket.title}' is now {new_status.value.replace('_', ' ')}",
            )

        db.session.commit()

        return {
            "success": True,
            "message": f"Ticket marked {new_status.value.replace('_', ' ')}",
            "ticket": _serialize_ticket_detail(ticket),
        }, 200


class TechnicianTicketRejectAPI(Resource):

    method_decorators = [roles_required(UserRole.TECHNICIAN)]

    def patch(self, ticket_id):
        """Technician declines a pending request and releases ticket back to open queue"""
        ticket = db.session.get(Ticket, ticket_id)

        if not ticket or ticket.assigned_to != current_user.id:
            return {"success": False, "message": "Ticket not found"}, 404

        if ticket.status in [TicketStatus.DONE, TicketStatus.INVALID]:
            return {"success": False, "message": "Cannot decline completed or invalid tickets"}, 400

        if not ticket.technician_request_pending:
            return {"success": False, "message": "Only pending requests can be declined"}, 400

        # Revert status and clear assignment
        old_technician = current_user.name
        old_status = ticket.status
        ticket.status = TicketStatus.OPEN
        ticket.assigned_to = None
        ticket.technician_request_pending = False

        ActivityLog.create(
            ticket_id=ticket.id,
            user_id=current_user.id,
            action=f"Declined technician request (was {old_status.value}, assigned to {old_technician})",
        )

        # Notify the tenant's manager
        if ticket.creator and ticket.creator.manager_id:
            Notification.create(
                user_id=ticket.creator.manager_id,
                message=f"Technician {current_user.name} declined request for '{ticket.title}'",
            )

        db.session.commit()

        return {
            "success": True,
            "message": "Request declined",
            "ticket": _serialize_ticket_detail(ticket),
        }, 200


class TechnicianTicketCommentsAPI(Resource):

    method_decorators = [roles_required(UserRole.TECHNICIAN)]

    def post(self, ticket_id):
        """Technician adds a comment to assigned ticket"""
        ticket = db.session.get(Ticket, ticket_id)

        if not ticket or ticket.assigned_to != current_user.id:
            return {"success": False, "message": "Ticket not found"}, 404

        if ticket.technician_request_pending or ticket.status not in [TicketStatus.ASSIGNED, TicketStatus.IN_PROGRESS]:
            return {"success": False, "message": "Accept the ticket request before commenting"}, 400

        body = (request.json or {}).get("body", "").strip()
        if not body:
            return {"success": False, "message": "Comment is required"}, 400

        comment = _create_comment(ticket, current_user, body, notify_user_id=ticket.created_by)
        return {
            "success": True,
            "message": "Comment added",
            "comment": _serialize_comment(comment),
            "ticket": _serialize_ticket_detail(ticket),
        }, 201


# --------------------------------------------------
# SEARCH TECHNICIANS (Manager only)
# --------------------------------------------------

class TechnicianSearchAPI(Resource):

    method_decorators = [roles_required(UserRole.MANAGER)]

    def get(self):
        """Search for technicians by name or service"""
        q = request.args.get("q", "").strip()
        service_id = request.args.get("service_id")
        
        query = db.select(User).filter(User.role == UserRole.TECHNICIAN)

        if q and len(q) >= 2:
            query = query.filter(
                db.or_(
                    User.name.ilike(f"%{q}%"),
                    User.email.ilike(f"%{q}%"),
                )
            )

        if service_id:
            query = query.join(User.services).filter_by(id=service_id)

        technicians = db.session.execute(query.limit(20)).scalars().all()

        return {
            "success": True,
            "technicians": [
                {
                    "id": t.id,
                    "name": t.name,
                    "email": t.email,
                    "technician_headline": t.technician_headline,
                    "phone": t.phone,
                    "pincode": t.pincode,
                    "location": t.location,
                    "service_pincode": t.service_pincode,
                    "average_rating": t.average_rating,
                    "reviews_count": t.reviews_count,
                    "services": [
                        {"id": s.id, "label": s.label}
                        for s in t.services
                    ],
                }
                for t in technicians
            ],
        }, 200


# --------------------------------------------------
# ASSIGN TECHNICIAN TO TICKET (Manager only)
# --------------------------------------------------

class AssignTechnicianAPI(Resource):

    method_decorators = [roles_required(UserRole.MANAGER)]

    def patch(self, ticket_id):
        """Send a technician request for a ticket."""
        ticket = _get_ticket_for_manager(ticket_id)

        if not ticket:
            return {"success": False, "message": "Ticket not found"}, 404

        technician_id = (request.json or {}).get("technician_id", "").strip()
        if not technician_id:
            return {"success": False, "message": "Technician ID is required"}, 400

        technician = db.session.get(User, technician_id)
        if not technician or technician.role != UserRole.TECHNICIAN:
            return {"success": False, "message": "Technician not found"}, 404

        if ticket.service_tag_id:
            technician_service_ids = {service.id for service in technician.services}
            if ticket.service_tag_id not in technician_service_ids:
                return {"success": False, "message": "Technician does not cover this service tag"}, 400

        if ticket.status in [TicketStatus.DONE, TicketStatus.INVALID]:
            return {"success": False, "message": "Cannot request technician for completed or invalid tickets"}, 400

        if ticket.status == TicketStatus.IN_PROGRESS:
            return {"success": False, "message": "Cannot change technician after work is in progress"}, 400

        if ticket.technician_request_pending and ticket.assigned_to == technician.id:
            return {"success": False, "message": "A pending request already exists for this technician"}, 400

        if ticket.assigned_to == technician.id and not ticket.technician_request_pending:
            return {"success": False, "message": "This technician is already assigned to the ticket"}, 400

        previous_technician_id = ticket.assigned_to
        previous_pending = ticket.technician_request_pending
        previous_status = ticket.status

        expected_previous_assignment = (
            Ticket.assigned_to.is_(None) if previous_technician_id is None else Ticket.assigned_to == previous_technician_id
        )

        updated = db.session.execute(
            db.update(Ticket)
            .where(
                Ticket.id == ticket.id,
                expected_previous_assignment,
                Ticket.technician_request_pending == previous_pending,
                Ticket.status == previous_status,
                Ticket.status.notin_([TicketStatus.DONE, TicketStatus.INVALID, TicketStatus.IN_PROGRESS]),
            )
            .values(
                assigned_to=technician.id,
                technician_request_pending=True,
                status=TicketStatus.OPEN,
            )
        )
        if updated.rowcount != 1:
            db.session.rollback()
            return _ticket_conflict_response()

        ticket = db.session.get(Ticket, ticket_id)
        previous_technician = db.session.get(User, previous_technician_id) if previous_technician_id else None
        old_technician = previous_technician.name if previous_technician else None

        for bid in ticket.bids:
            bid.is_selected_for_request = bid.technician_id == technician.id

        existing_bid = db.session.execute(
            db.select(TicketBid).filter_by(ticket_id=ticket.id, technician_id=technician.id)
        ).scalar_one_or_none()
        if existing_bid:
            existing_bid.is_selected_for_request = True

        if previous_technician and previous_technician.id != technician.id:
            Notification.create(
                user_id=previous_technician.id,
                message=f"Your assignment/request for '{ticket.title}' was withdrawn by manager {current_user.name}",
            )

        ActivityLog.create(
            ticket_id=ticket.id,
            user_id=current_user.id,
            action=f"Sent technician request to {technician.name}" + (f" (was {old_technician})" if old_technician else ""),
        )

        # Notify the technician
        Notification.create(
            user_id=technician.id,
            message=f"New technician request: '{ticket.title}' from manager {current_user.name}",
        )

        # Notify the tenant
        Notification.create(
            user_id=ticket.created_by,
            message=f"A technician request was sent for your ticket '{ticket.title}'",
        )

        db.session.commit()

        return {
            "success": True,
            "message": f"Request sent to {technician.name}",
            "ticket": _serialize_ticket_detail(ticket),
        }, 200


class ManagerTicketBidsAPI(Resource):

    method_decorators = [roles_required(UserRole.MANAGER)]

    def get(self, ticket_id):
        ticket = _get_ticket_for_manager(ticket_id)
        if not ticket:
            return {"success": False, "message": "Ticket not found"}, 404

        q = request.args.get("q", "").strip()
        page, page_size = _pagination_args(default_size=10)

        query = (
            db.select(TicketBid)
            .filter(TicketBid.ticket_id == ticket.id)
            .order_by(TicketBid.proposed_price.asc(), TicketBid.created_at.asc())
        )

        if q:
            query = query.join(User, TicketBid.technician_id == User.id).filter(
                db.or_(
                    User.name.ilike(f"%{q}%"),
                    User.email.ilike(f"%{q}%"),
                )
            )

        bids, pagination = _paginate_query(query, page, page_size)

        return {
            "success": True,
            "ticket": _serialize_ticket(ticket),
            "bids": [_serialize_bid(bid) for bid in bids],
            "pagination": pagination,
        }, 200
