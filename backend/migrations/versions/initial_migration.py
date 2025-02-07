"""initial migration

Revision ID: initial_migration
Revises: 
Create Date: 2024-02-06 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = 'initial_migration'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create users table
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(64), nullable=False),
        sa.Column('email', sa.String(120), nullable=False),
        sa.Column('password_hash', sa.String(128)),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )

    # Create user_config table
    op.create_table(
        'user_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('theme', sa.String(50), default='dark'),
        sa.Column('theme_customization', sa.Text()),
        sa.Column('cli_preferences', sa.Text()),
        sa.Column('timeout_settings', sa.Text()),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )

    # Create devices table
    op.create_table(
        'device',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(64), nullable=False),
        sa.Column('host', sa.String(128), nullable=False),
        sa.Column('username', sa.String(64), nullable=False),
        sa.Column('password', sa.String(256), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('last_used', sa.DateTime()),
        sa.Column('status', sa.String(20), default='unknown'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('host')
    )

    # Create command_template table
    op.create_table(
        'command_template',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('command', sa.Text(), nullable=False),
        sa.Column('category', sa.String(50)),
        sa.Column('variables', sa.Text()),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('user.id')),
        sa.Column('is_favorite', sa.Boolean(), default=False),
        sa.Column('is_system', sa.Boolean(), default=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create command_history table
    op.create_table(
        'command_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id')),
        sa.Column('device_id', sa.Integer(), sa.ForeignKey('device.id')),
        sa.Column('command', sa.Text(), nullable=False),
        sa.Column('output', sa.Text()),
        sa.Column('status', sa.String(20)),
        sa.Column('executed_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('execution_time', sa.Float()),
        sa.Column('is_favorite', sa.Boolean(), default=False),
        sa.Column('error_message', sa.Text()),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # Drop tables in reverse order
    op.drop_table('command_history')
    op.drop_table('command_template')
    op.drop_table('device')
    op.drop_table('user_config')
    op.drop_table('user') 