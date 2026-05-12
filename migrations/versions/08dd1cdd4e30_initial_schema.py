"""
initial schema

Revision ID: 08dd1cdd4e30
Revises: 
Create Date: 2026-05-11 19:25:16.060236
"""
from alembic import op
import sqlalchemy as sa


revision = '08dd1cdd4e30'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('prediction_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('prediction_type', sa.String(length=20), nullable=False),
    sa.Column('inputs', sa.JSON(), nullable=False),
    sa.Column('outputs', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('prediction_logs')
