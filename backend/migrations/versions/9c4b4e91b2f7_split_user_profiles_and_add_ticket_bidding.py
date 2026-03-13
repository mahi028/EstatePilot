"""split user profiles and add ticket bidding

Revision ID: 9c4b4e91b2f7
Revises: 2e9fd81a7d31
Create Date: 2026-03-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9c4b4e91b2f7"
down_revision = "2e9fd81a7d31"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tenant_profiles",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("manager_id", sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(["manager_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("user_id"),
    )
    with op.batch_alter_table("tenant_profiles", schema=None) as batch_op:
        batch_op.create_index("ix_tenant_profile_manager", ["manager_id"], unique=False)

    op.create_table(
        "manager_profiles",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("user_id"),
    )

    op.create_table(
        "technician_profiles",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("years_experience", sa.Integer(), nullable=True),
        sa.Column("base_price", sa.Float(), nullable=True),
        sa.Column("technician_headline", sa.String(length=180), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("user_id"),
    )

    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            INSERT INTO tenant_profiles (user_id, manager_id)
            SELECT id, manager_id FROM users WHERE role = 'TENANT'
            """
        )
    )
    connection.execute(
        sa.text(
            """
            INSERT INTO manager_profiles (user_id)
            SELECT id FROM users WHERE role = 'MANAGER'
            """
        )
    )
    connection.execute(
        sa.text(
            """
            INSERT INTO technician_profiles (user_id, years_experience, base_price, technician_headline)
            SELECT id, years_experience, base_price, technician_headline
            FROM users
            WHERE role = 'TECHNICIAN'
            """
        )
    )

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_index("ix_users_manager")
        batch_op.drop_column("manager_id")
        batch_op.drop_column("years_experience")
        batch_op.drop_column("base_price")
        batch_op.drop_column("technician_headline")

    with op.batch_alter_table("tickets", schema=None) as batch_op:
        batch_op.add_column(sa.Column("service_tag_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("technician_request_pending", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.create_foreign_key(
            "fk_tickets_service_tag_id_technician_services",
            "technician_services",
            ["service_tag_id"],
            ["id"],
        )

    op.create_table(
        "ticket_bids",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("ticket_id", sa.String(length=36), nullable=False),
        sa.Column("technician_id", sa.String(length=36), nullable=False),
        sa.Column("proposed_price", sa.Float(), nullable=False),
        sa.Column("message", sa.String(length=500), nullable=True),
        sa.Column("is_selected_for_request", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["technician_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticket_id", "technician_id", name="uq_ticket_bid_ticket_technician"),
    )
    with op.batch_alter_table("ticket_bids", schema=None) as batch_op:
        batch_op.create_index("ix_ticket_bid_ticket", ["ticket_id"], unique=False)
        batch_op.create_index("ix_ticket_bid_technician", ["technician_id"], unique=False)



def downgrade():
    with op.batch_alter_table("ticket_bids", schema=None) as batch_op:
        batch_op.drop_index("ix_ticket_bid_technician")
        batch_op.drop_index("ix_ticket_bid_ticket")
    op.drop_table("ticket_bids")

    with op.batch_alter_table("tickets", schema=None) as batch_op:
        batch_op.drop_constraint("fk_tickets_service_tag_id_technician_services", type_="foreignkey")
        batch_op.drop_column("technician_request_pending")
        batch_op.drop_column("service_tag_id")

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("manager_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("years_experience", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("base_price", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("technician_headline", sa.String(length=180), nullable=True))
        batch_op.create_index("ix_users_manager", ["manager_id"], unique=False)
        batch_op.create_foreign_key("fk_users_manager_id_users", "users", ["manager_id"], ["id"])

    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            UPDATE users
            SET manager_id = (
                SELECT tenant_profiles.manager_id
                FROM tenant_profiles
                WHERE tenant_profiles.user_id = users.id
            )
            WHERE id IN (SELECT user_id FROM tenant_profiles)
            """
        )
    )
    connection.execute(
        sa.text(
            """
            UPDATE users
            SET years_experience = (
                    SELECT technician_profiles.years_experience
                    FROM technician_profiles
                    WHERE technician_profiles.user_id = users.id
                ),
                base_price = (
                    SELECT technician_profiles.base_price
                    FROM technician_profiles
                    WHERE technician_profiles.user_id = users.id
                ),
                technician_headline = (
                    SELECT technician_profiles.technician_headline
                    FROM technician_profiles
                    WHERE technician_profiles.user_id = users.id
                )
            WHERE id IN (SELECT user_id FROM technician_profiles)
            """
        )
    )

    op.drop_table("technician_profiles")
    op.drop_table("manager_profiles")

    with op.batch_alter_table("tenant_profiles", schema=None) as batch_op:
        batch_op.drop_index("ix_tenant_profile_manager")
    op.drop_table("tenant_profiles")
