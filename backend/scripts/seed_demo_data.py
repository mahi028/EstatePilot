import argparse
import sys
from pathlib import Path
from typing import Iterable

from sqlalchemy import or_

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app import create_app
from app.models import (
    db,
    ActivityLog,
    ManagementInvitation,
    ManagerProfile,
    Notification,
    TechnicianProfile,
    TechnicianReview,
    TechnicianService,
    TenantProfile,
    Ticket,
    TicketBid,
    TicketComment,
    TicketImage,
    TicketPriority,
    TicketStatus,
    UserRole,
    Users,
    technician_service_links,
)

DEMO_DOMAIN = "eplt.com"
DEMO_PREFIX = "[DEMO]"


def _ensure_services() -> dict[str, TechnicianService]:
    seed_services = [
        ("plumbing", "Plumbing"),
        ("electrical", "Electrical"),
        ("hvac", "HVAC"),
        ("appliance", "Appliance Repair"),
        ("painting", "Painting"),
        ("carpentry", "Carpentry"),
    ]

    by_code: dict[str, TechnicianService] = {}
    for code, label in seed_services:
        service = db.session.execute(
            db.select(TechnicianService).filter(TechnicianService.code == code)
        ).scalar_one_or_none()
        if service is None:
            service = TechnicianService(code=code, label=label, description=f"{label} services")
            db.session.add(service)
            db.session.flush()
        by_code[code] = service
    return by_code


def _ensure_user(
    *,
    name: str,
    email: str,
    role: UserRole,
    password: str,
    manager_id: str | None = None,
    pincode: str | None = None,
    location: str | None = None,
    phone: str | None = None,
    bio: str | None = None,
    years_experience: int | None = None,
    base_price: float | None = None,
    technician_headline: str | None = None,
    service_pincode: str | None = None,
    services: Iterable[TechnicianService] | None = None,
) -> Users:
    user = db.session.execute(db.select(Users).filter(Users.email == email)).scalar_one_or_none()

    if user is None:
        user = Users(name=name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

    user.name = name
    user.phone = phone
    user.pincode = pincode
    user.location = location
    user.bio = bio

    if role == UserRole.MANAGER and user.manager_profile is None:
        user.manager_profile = ManagerProfile(user_id=user.id)

    if role == UserRole.TENANT:
        user.manager_id = manager_id

    if role == UserRole.TECHNICIAN:
        user.years_experience = years_experience
        user.base_price = base_price
        user.technician_headline = technician_headline
        user.service_pincode = service_pincode
        if services is not None:
            user.services = list(services)

    return user


def _ensure_ticket(
    *,
    title: str,
    description: str,
    tenant: Users,
    service: TechnicianService,
    priority: TicketPriority,
    status: TicketStatus,
    assigned_to: Users | None = None,
    request_pending: bool = False,
) -> Ticket:
    ticket = db.session.execute(
        db.select(Ticket).filter(Ticket.title == title, Ticket.created_by == tenant.id)
    ).scalar_one_or_none()

    if ticket is None:
        ticket = Ticket(
            title=title,
            description=description,
            created_by=tenant.id,
            service_tag_id=service.id,
            priority=priority,
            status=status,
            assigned_to=assigned_to.id if assigned_to else None,
            technician_request_pending=request_pending,
        )
        db.session.add(ticket)
        db.session.flush()
        ActivityLog.create(ticket_id=ticket.id, user_id=tenant.id, action="Demo ticket created")
    else:
        ticket.description = description
        ticket.service_tag_id = service.id
        ticket.priority = priority
        ticket.status = status
        ticket.assigned_to = assigned_to.id if assigned_to else None
        ticket.technician_request_pending = request_pending

    return ticket


def _ensure_bid(ticket: Ticket, technician: Users, price: float, message: str, selected: bool = False) -> None:
    bid = db.session.execute(
        db.select(TicketBid).filter(TicketBid.ticket_id == ticket.id, TicketBid.technician_id == technician.id)
    ).scalar_one_or_none()
    if bid is None:
        bid = TicketBid(
            ticket_id=ticket.id,
            technician_id=technician.id,
            proposed_price=price,
            message=message,
            is_selected_for_request=selected,
        )
        db.session.add(bid)
    else:
        bid.proposed_price = price
        bid.message = message
        bid.is_selected_for_request = selected


def _ensure_comment(ticket: Ticket, user: Users, body: str) -> None:
    existing = db.session.execute(
        db.select(TicketComment).filter(
            TicketComment.ticket_id == ticket.id,
            TicketComment.user_id == user.id,
            TicketComment.body == body,
        )
    ).scalar_one_or_none()
    if existing is None:
        db.session.add(TicketComment(ticket_id=ticket.id, user_id=user.id, body=body))


def _ensure_notification(user_id: str, message: str) -> None:
    existing = db.session.execute(
        db.select(Notification).filter(Notification.user_id == user_id, Notification.message == message)
    ).scalar_one_or_none()
    if existing is None:
        Notification.create(user_id=user_id, message=message)


def _ensure_review(technician: Users, reviewer: Users, ticket: Ticket, rating: int, comment: str) -> None:
    existing = db.session.execute(
        db.select(TechnicianReview).filter(
            TechnicianReview.technician_id == technician.id,
            TechnicianReview.reviewer_id == reviewer.id,
        )
    ).scalar_one_or_none()
    if existing is None:
        db.session.add(
            TechnicianReview(
                technician_id=technician.id,
                reviewer_id=reviewer.id,
                ticket_id=ticket.id,
                rating=rating,
                comment=comment,
            )
        )


def _demo_user_ids() -> list[str]:
    return [
        user_id
        for (user_id,) in db.session.execute(
            db.select(Users.id).filter(Users.email.like(f"%@{DEMO_DOMAIN}"))
        ).all()
    ]


def _reset_demo_data() -> None:
    user_ids = _demo_user_ids()

    demo_ticket_ids = [
        ticket_id
        for (ticket_id,) in db.session.execute(
            db.select(Ticket.id).filter(Ticket.title.like(f"{DEMO_PREFIX}%"))
        ).all()
    ]

    if demo_ticket_ids:
        db.session.execute(db.delete(TicketBid).filter(TicketBid.ticket_id.in_(demo_ticket_ids)))
        db.session.execute(db.delete(TicketComment).filter(TicketComment.ticket_id.in_(demo_ticket_ids)))
        db.session.execute(db.delete(ActivityLog).filter(ActivityLog.ticket_id.in_(demo_ticket_ids)))
        db.session.execute(db.delete(TicketImage).filter(TicketImage.ticket_id.in_(demo_ticket_ids)))
        db.session.execute(db.delete(TechnicianReview).filter(TechnicianReview.ticket_id.in_(demo_ticket_ids)))
        db.session.execute(db.delete(Ticket).filter(Ticket.id.in_(demo_ticket_ids)))

    if user_ids:
        db.session.execute(db.delete(Notification).filter(Notification.user_id.in_(user_ids)))
        db.session.execute(
            db.delete(ManagementInvitation).filter(
                or_(
                    ManagementInvitation.manager_id.in_(user_ids),
                    ManagementInvitation.tenant_id.in_(user_ids),
                )
            )
        )
        db.session.execute(
            db.delete(TechnicianReview).filter(
                or_(
                    TechnicianReview.technician_id.in_(user_ids),
                    TechnicianReview.reviewer_id.in_(user_ids),
                )
            )
        )
        db.session.execute(
            technician_service_links.delete().where(
                technician_service_links.c.technician_id.in_(user_ids)
            )
        )
        db.session.execute(db.delete(TenantProfile).filter(TenantProfile.user_id.in_(user_ids)))
        db.session.execute(db.delete(ManagerProfile).filter(ManagerProfile.user_id.in_(user_ids)))
        db.session.execute(db.delete(TechnicianProfile).filter(TechnicianProfile.user_id.in_(user_ids)))
        db.session.execute(db.delete(Users).filter(Users.id.in_(user_ids)))

    db.session.commit()


def seed_demo_data(password: str) -> None:
    existing_demo_ticket = db.session.execute(
        db.select(Ticket.id).filter(Ticket.title.like(f"{DEMO_PREFIX}%")).limit(1)
    ).first()
    if existing_demo_ticket:
        print("Demo data already exists. Use --reset to recreate.")
        return

    services = _ensure_services()

    manager_1 = _ensure_user(
        name="Maya Manager",
        email=f"maya.manager@{DEMO_DOMAIN}",
        role=UserRole.MANAGER,
        password=password,
        pincode="560001",
        location="Bengaluru",
        phone="+91 9900011111",
        bio="Demo property manager overseeing premium apartments.",
    )
    manager_2 = _ensure_user(
        name="Noah Manager",
        email=f"noah.manager@{DEMO_DOMAIN}",
        role=UserRole.MANAGER,
        password=password,
        pincode="400001",
        location="Mumbai",
        phone="+91 9900022222",
        bio="Demo manager for mixed-use buildings.",
    )

    tenant_1 = _ensure_user(
        name="Ava Tenant",
        email=f"ava.tenant@{DEMO_DOMAIN}",
        role=UserRole.TENANT,
        password=password,
        manager_id=manager_1.id,
        pincode="560034",
        location="Koramangala",
        phone="+91 9888800011",
        bio="Lives in Tower A, unit 302.",
    )
    tenant_2 = _ensure_user(
        name="Liam Tenant",
        email=f"liam.tenant@{DEMO_DOMAIN}",
        role=UserRole.TENANT,
        password=password,
        manager_id=manager_1.id,
        pincode="560102",
        location="HSR Layout",
        phone="+91 9888800022",
        bio="Works from home, prefers morning visits.",
    )
    tenant_3 = _ensure_user(
        name="Emma Tenant",
        email=f"emma.tenant@{DEMO_DOMAIN}",
        role=UserRole.TENANT,
        password=password,
        manager_id=manager_2.id,
        pincode="400050",
        location="Bandra",
        phone="+91 9888800033",
        bio="Demo tenant with appliance-heavy tickets.",
    )

    tech_1 = _ensure_user(
        name="Priya Plumber",
        email=f"priya.tech@{DEMO_DOMAIN}",
        role=UserRole.TECHNICIAN,
        password=password,
        pincode="560070",
        location="JP Nagar",
        phone="+91 9777700011",
        years_experience=7,
        base_price=650.0,
        technician_headline="Leak detection and bathroom fittings specialist",
        service_pincode="560001",
        services=[services["plumbing"], services["appliance"]],
    )
    tech_2 = _ensure_user(
        name="Arjun Electric",
        email=f"arjun.tech@{DEMO_DOMAIN}",
        role=UserRole.TECHNICIAN,
        password=password,
        pincode="560076",
        location="BTM Layout",
        phone="+91 9777700022",
        years_experience=5,
        base_price=550.0,
        technician_headline="Residential electrical fault troubleshooting",
        service_pincode="560001",
        services=[services["electrical"], services["hvac"]],
    )
    tech_3 = _ensure_user(
        name="Sara HVAC",
        email=f"sara.tech@{DEMO_DOMAIN}",
        role=UserRole.TECHNICIAN,
        password=password,
        pincode="400053",
        location="Andheri",
        phone="+91 9777700033",
        years_experience=9,
        base_price=800.0,
        technician_headline="Cooling and ventilation optimization expert",
        service_pincode="400001",
        services=[services["hvac"], services["electrical"]],
    )

    db.session.flush()

    open_ticket = _ensure_ticket(
        title=f"{DEMO_PREFIX} Kitchen sink blockage",
        description="Kitchen sink drains very slowly and overflows during peak use.",
        tenant=tenant_1,
        service=services["plumbing"],
        priority=TicketPriority.HIGH,
        status=TicketStatus.OPEN,
    )
    pending_ticket = _ensure_ticket(
        title=f"{DEMO_PREFIX} Bedroom AC fan noise",
        description="AC indoor unit makes rattling noise at medium fan speed.",
        tenant=tenant_2,
        service=services["hvac"],
        priority=TicketPriority.MEDIUM,
        status=TicketStatus.OPEN,
        assigned_to=tech_3,
        request_pending=True,
    )
    assigned_ticket = _ensure_ticket(
        title=f"{DEMO_PREFIX} Hallway light flickering",
        description="Lights in shared hallway flicker every evening.",
        tenant=tenant_2,
        service=services["electrical"],
        priority=TicketPriority.MEDIUM,
        status=TicketStatus.ASSIGNED,
        assigned_to=tech_2,
    )
    in_progress_ticket = _ensure_ticket(
        title=f"{DEMO_PREFIX} Washing machine vibration",
        description="Machine shakes excessively during spin cycle.",
        tenant=tenant_3,
        service=services["appliance"],
        priority=TicketPriority.HIGH,
        status=TicketStatus.IN_PROGRESS,
        assigned_to=tech_1,
    )
    done_ticket = _ensure_ticket(
        title=f"{DEMO_PREFIX} Living room AC low cooling",
        description="Cooling restored after refrigerant and filter service.",
        tenant=tenant_1,
        service=services["hvac"],
        priority=TicketPriority.HIGH,
        status=TicketStatus.DONE,
        assigned_to=tech_3,
    )
    invalid_ticket = _ensure_ticket(
        title=f"{DEMO_PREFIX} Balcony repaint request",
        description="Ticket invalidated because repaint was already completed by society vendor.",
        tenant=tenant_3,
        service=services["painting"],
        priority=TicketPriority.LOW,
        status=TicketStatus.INVALID,
    )

    _ensure_bid(open_ticket, tech_1, 750.0, "Can resolve in one visit with drain camera.", selected=False)
    _ensure_bid(open_ticket, tech_2, 680.0, "Available tomorrow evening.", selected=False)

    _ensure_comment(assigned_ticket, tech_2, f"{DEMO_PREFIX} Parts requested and site visit scheduled.")
    _ensure_comment(in_progress_ticket, tech_1, f"{DEMO_PREFIX} Replaced dampers and testing spin balance.")
    _ensure_comment(done_ticket, tech_3, f"{DEMO_PREFIX} Cooling performance normalized and ticket closed.")

    _ensure_review(
        technician=tech_3,
        reviewer=tenant_1,
        ticket=done_ticket,
        rating=5,
        comment="Great response time and clear explanation of the fix.",
    )
    _ensure_review(
        technician=tech_2,
        reviewer=manager_1,
        ticket=assigned_ticket,
        rating=4,
        comment="Professional communication and punctual service.",
    )

    _ensure_notification(manager_1.id, f"{DEMO_PREFIX} New bid arrived for kitchen sink blockage")
    _ensure_notification(tenant_2.id, f"{DEMO_PREFIX} Technician request sent for bedroom AC fan noise")
    _ensure_notification(tech_3.id, f"{DEMO_PREFIX} Please respond to pending AC request")
    _ensure_notification(tenant_1.id, f"{DEMO_PREFIX} Your AC ticket was marked done")

    db.session.commit()

    print("Demo data inserted successfully.")
    print(f"Demo login password for all demo users: {password}")
    print(f"Demo email domain: @{DEMO_DOMAIN}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed EstatePilot database with demo data")
    parser.add_argument("--password", default="demo12345", help="Password for all demo users")
    parser.add_argument("--reset", action="store_true", help="Delete old demo data before seeding")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        if args.reset:
            _reset_demo_data()
            print("Old demo data removed.")
        seed_demo_data(password=args.password)


if __name__ == "__main__":
    main()
