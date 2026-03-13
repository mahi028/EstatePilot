"""add user and technician pincodes

Revision ID: 1c6a29b7f4d8
Revises: 9c4b4e91b2f7
Create Date: 2026-03-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1c6a29b7f4d8"
down_revision = "9c4b4e91b2f7"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("pincode", sa.String(length=12), nullable=True))

    with op.batch_alter_table("technician_profiles", schema=None) as batch_op:
        batch_op.add_column(sa.Column("service_pincode", sa.String(length=12), nullable=True))


def downgrade():
    with op.batch_alter_table("technician_profiles", schema=None) as batch_op:
        batch_op.drop_column("service_pincode")

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("pincode")
