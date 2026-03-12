"""add technician profiles services reviews

Revision ID: 2e9fd81a7d31
Revises: 469781e8dbf2
Create Date: 2026-03-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2e9fd81a7d31'
down_revision = '469781e8dbf2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('profile_image_path', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('phone', sa.String(length=40), nullable=True))
        batch_op.add_column(sa.Column('location', sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column('bio', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('years_experience', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('base_price', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('technician_headline', sa.String(length=180), nullable=True))

    op.create_table(
        'technician_services',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('code', sa.String(length=80), nullable=False),
        sa.Column('label', sa.String(length=120), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    with op.batch_alter_table('technician_services', schema=None) as batch_op:
        batch_op.create_index('ix_technician_service_code', ['code'], unique=False)

    op.create_table(
        'technician_service_links',
        sa.Column('technician_id', sa.String(length=36), nullable=False),
        sa.Column('service_id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(['service_id'], ['technician_services.id']),
        sa.ForeignKeyConstraint(['technician_id'], ['users.id']),
        sa.PrimaryKeyConstraint('technician_id', 'service_id')
    )

    op.create_table(
        'technician_reviews',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('technician_id', sa.String(length=36), nullable=False),
        sa.Column('reviewer_id', sa.String(length=36), nullable=False),
        sa.Column('ticket_id', sa.String(length=36), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['reviewer_id'], ['users.id']),
        sa.ForeignKeyConstraint(['technician_id'], ['users.id']),
        sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('technician_id', 'reviewer_id', name='uq_technician_review_once_per_reviewer')
    )
    with op.batch_alter_table('technician_reviews', schema=None) as batch_op:
        batch_op.create_index('ix_technician_review_reviewer', ['reviewer_id'], unique=False)
        batch_op.create_index('ix_technician_review_technician', ['technician_id'], unique=False)


def downgrade():
    with op.batch_alter_table('technician_reviews', schema=None) as batch_op:
        batch_op.drop_index('ix_technician_review_technician')
        batch_op.drop_index('ix_technician_review_reviewer')
    op.drop_table('technician_reviews')

    op.drop_table('technician_service_links')

    with op.batch_alter_table('technician_services', schema=None) as batch_op:
        batch_op.drop_index('ix_technician_service_code')
    op.drop_table('technician_services')

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('technician_headline')
        batch_op.drop_column('base_price')
        batch_op.drop_column('years_experience')
        batch_op.drop_column('bio')
        batch_op.drop_column('location')
        batch_op.drop_column('phone')
        batch_op.drop_column('profile_image_path')
