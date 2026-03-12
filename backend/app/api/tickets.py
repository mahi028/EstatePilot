from flask_restful import Resource
from flask import request
from flask_jwt_extended import current_user

from app.models import (
    db, User, Ticket, TicketStatus, TicketPriority,
    ActivityLog, Notification, UserRole,
)
from app.forms import CreateTicketForm
from app.utils.RBAC import roles_required


def _serialize_ticket(ticket):
    return {
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

        logs = (
            db.session.execute(
                db.select(ActivityLog)
                .filter_by(ticket_id=ticket.id)
                .order_by(ActivityLog.created_at.desc())
            )
            .scalars()
            .all()
        )

        data = _serialize_ticket(ticket)
        data["activity_logs"] = [
            {
                "id": log.id,
                "action": log.action,
                "user_id": log.user_id,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]

        return {"success": True, "ticket": data}, 200


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
