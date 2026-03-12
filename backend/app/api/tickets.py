from flask_restful import Resource
from flask import request, current_app
from flask_jwt_extended import current_user

from app.models import (
    db, User, Ticket, TicketImage, TicketComment, TicketStatus, TicketPriority,
    ActivityLog, Notification, UserRole,
)
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
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in sorted(ticket.activity_logs, key=lambda item: item.created_at or 0, reverse=True)
        ]
    return data


def _serialize_ticket_detail(ticket):
    return _serialize_ticket(
        ticket,
        with_images=True,
        with_comments=True,
        with_activity_logs=True,
    )


def _get_ticket_for_manager(ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    creator = db.session.get(User, ticket.created_by) if ticket else None
    if not ticket or not creator or creator.manager_id != current_user.id:
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

        form = CreateTicketForm(data=request.json)

        if not form.validate():
            return {"success": False, "errors": form.errors}, 400

        ticket = Ticket(
            title=form.title.data,
            description=form.description.data,
            priority=TicketPriority(form.priority.data),
            created_by=current_user.id,
        )
        db.session.add(ticket)

        # Notify the tenant's manager
        Notification.create(
            user_id=current_user.manager_id,
            message=f"New ticket '{ticket.title}' created by {current_user.name}",
        )

        db.session.commit()

        return {
            "success": True,
            "message": "Ticket created",
            "ticket": _serialize_ticket(ticket),
        }, 201

    def get(self):
        status_filter = request.args.get("status")
        priority_filter = request.args.get("priority")

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

        query = query.order_by(Ticket.created_at.desc())
        tickets = db.session.execute(query).scalars().all()

        return {
            "success": True,
            "tickets": [_serialize_ticket(t) for t in tickets],
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
        _delete_ticket_images(ticket)
        db.session.delete(ticket)

        if manager_id:
            Notification.create(
                user_id=manager_id,
                message=f"Ticket '{ticket.title}' was deleted by {current_user.name}",
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
            .filter_by(manager_id=current_user.id)
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

        query = (
            db.select(Ticket)
            .join(User, Ticket.created_by == User.id)
            .filter(User.manager_id == current_user.id)
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

        query = query.order_by(Ticket.created_at.desc())
        tickets = db.session.execute(query).scalars().all()

        return {
            "success": True,
            "tickets": [_serialize_ticket(t) for t in tickets],
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

        # Get tickets assigned to this technician
        query = db.select(Ticket).filter_by(assigned_to=current_user.id)

        if status_filter:
            try:
                query = query.filter_by(status=TicketStatus(status_filter))
            except ValueError:
                return {"success": False, "message": "Invalid status filter"}, 400

        query = query.order_by(Ticket.created_at.desc())
        tickets = db.session.execute(query).scalars().all()

        return {
            "success": True,
            "tickets": [_serialize_ticket(t) for t in tickets],
        }, 200


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
        """Technician accepts a pending request and starts working on the ticket"""
        ticket = db.session.get(Ticket, ticket_id)

        if not ticket or ticket.assigned_to != current_user.id:
            return {"success": False, "message": "Ticket not found"}, 404

        if ticket.status == TicketStatus.IN_PROGRESS:
            return {"success": False, "message": "This ticket was already accepted"}, 400

        if ticket.status in [TicketStatus.DONE, TicketStatus.INVALID]:
            return {"success": False, "message": "Cannot accept completed or invalid tickets"}, 400

        if ticket.status != TicketStatus.ASSIGNED:
            return {"success": False, "message": "This request is no longer available"}, 400

        # Request accepted: move to active work state.
        old_status = ticket.status
        ticket.status = TicketStatus.IN_PROGRESS
        
        ActivityLog.create(
            ticket_id=ticket.id,
            user_id=current_user.id,
            action=f"Accepted technician request (from {old_status.value})",
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


class TechnicianTicketRejectAPI(Resource):

    method_decorators = [roles_required(UserRole.TECHNICIAN)]

    def patch(self, ticket_id):
        """Technician declines a pending request and releases ticket back to open queue"""
        ticket = db.session.get(Ticket, ticket_id)

        if not ticket or ticket.assigned_to != current_user.id:
            return {"success": False, "message": "Ticket not found"}, 404

        if ticket.status in [TicketStatus.DONE, TicketStatus.INVALID]:
            return {"success": False, "message": "Cannot decline completed or invalid tickets"}, 400

        if ticket.status != TicketStatus.ASSIGNED:
            return {"success": False, "message": "Only pending requests can be declined"}, 400

        # Revert status and clear assignment
        old_technician = current_user.name
        old_status = ticket.status
        ticket.status = TicketStatus.OPEN
        ticket.assigned_to = None

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

        if ticket.status != TicketStatus.IN_PROGRESS:
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
                    "location": t.location,
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
        """Send a technician request for a ticket"""
        ticket = _get_ticket_for_manager(ticket_id)

        if not ticket:
            return {"success": False, "message": "Ticket not found"}, 404

        technician_id = (request.json or {}).get("technician_id", "").strip()
        if not technician_id:
            return {"success": False, "message": "Technician ID is required"}, 400

        technician = db.session.get(User, technician_id)
        if not technician or technician.role != UserRole.TECHNICIAN:
            return {"success": False, "message": "Technician not found"}, 404

        if ticket.status in [TicketStatus.DONE, TicketStatus.INVALID]:
            return {"success": False, "message": "Cannot request technician for completed or invalid tickets"}, 400

        # Manager sends a request; technician acceptance starts active work.
        old_technician = ticket.technician.name if ticket.technician else None
        ticket.assigned_to = technician.id
        ticket.status = TicketStatus.ASSIGNED

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
