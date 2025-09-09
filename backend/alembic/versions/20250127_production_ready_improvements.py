"""Add production-ready fields and indexes

Revision ID: 20250127_prod
Revises: 5b56126de0f
Create Date: 2025-01-27 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20250127_prod"
down_revision: Union[str, Sequence[str], None] = "5b56126de0f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add production-ready improvements."""

    # Add indexes for better performance
    op.create_index("ix_users_email_verified", "users", ["email", "is_verified"])
    op.create_index("ix_users_organization_id", "users", ["organization_id"])
    op.create_index("ix_connections_organization_id", "connections", ["organization_id"])
    op.create_index("ix_connections_status", "connections", ["status"])
    op.create_index("ix_organizations_name_lower", "organizations", [sa.text("LOWER(name)")])

    # Add created_at and updated_at to users table if not exists
    try:
        op.add_column(
            "users",
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
        )
    except Exception:
        pass  # Column might already exist

    try:
        op.add_column(
            "users",
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
        )
    except Exception:
        pass  # Column might already exist

    # Add created_at and updated_at to organizations table if not exists
    try:
        op.add_column(
            "organizations",
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
        )
    except Exception:
        pass  # Column might already exist

    try:
        op.add_column(
            "organizations",
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
        )
    except Exception:
        pass  # Column might already exist

    # Add additional user fields for production
    try:
        op.add_column("users", sa.Column("first_name", sa.String(100), nullable=True))
    except Exception:
        pass  # Column might already exist

    try:
        op.add_column("users", sa.Column("last_name", sa.String(100), nullable=True))
    except Exception:
        pass  # Column might already exist

    try:
        op.add_column(
            "users", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True)
        )
    except Exception:
        pass  # Column might already exist

    try:
        op.add_column("users", sa.Column("password_reset_token", sa.UUID(), nullable=True))
    except Exception:
        pass  # Column might already exist

    try:
        op.add_column(
            "users",
            sa.Column("password_reset_expires_at", sa.DateTime(timezone=True), nullable=True),
        )
    except Exception:
        pass  # Column might already exist

    # Add indexes for new fields
    try:
        op.create_index("ix_users_password_reset_token", "users", ["password_reset_token"])
    except Exception:
        pass  # Index might already exist

    # Add connection metadata fields
    try:
        op.add_column(
            "connections", sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True)
        )
    except Exception:
        pass  # Column might already exist

    try:
        op.add_column("connections", sa.Column("record_count", sa.Integer(), nullable=True))
    except Exception:
        pass  # Column might already exist

    try:
        op.add_column("connections", sa.Column("connection_string", sa.Text(), nullable=True))
    except Exception:
        pass  # Column might already exist

    # Add audit trail table
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id", sa.UUID(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])
    op.create_index("ix_audit_logs_resource", "audit_logs", ["resource_type", "resource_id"])


def downgrade() -> None:
    """Remove production-ready improvements."""

    # Drop audit logs table
    op.drop_table("audit_logs")

    # Drop indexes
    try:
        op.drop_index("ix_users_password_reset_token", table_name="users")
    except Exception:
        pass

    try:
        op.drop_index("ix_organizations_name_lower", table_name="organizations")
    except Exception:
        pass

    try:
        op.drop_index("ix_connections_status", table_name="connections")
    except Exception:
        pass

    try:
        op.drop_index("ix_connections_organization_id", table_name="connections")
    except Exception:
        pass

    try:
        op.drop_index("ix_users_organization_id", table_name="users")
    except Exception:
        pass

    try:
        op.drop_index("ix_users_email_verified", table_name="users")
    except Exception:
        pass

    # Drop columns
    try:
        op.drop_column("connections", "connection_string")
    except Exception:
        pass

    try:
        op.drop_column("connections", "record_count")
    except Exception:
        pass

    try:
        op.drop_column("connections", "last_sync_at")
    except Exception:
        pass

    try:
        op.drop_column("users", "password_reset_expires_at")
    except Exception:
        pass

    try:
        op.drop_column("users", "password_reset_token")
    except Exception:
        pass

    try:
        op.drop_column("users", "last_login_at")
    except Exception:
        pass

    try:
        op.drop_column("users", "last_name")
    except Exception:
        pass

    try:
        op.drop_column("users", "first_name")
    except Exception:
        pass

    try:
        op.drop_column("organizations", "updated_at")
    except Exception:
        pass

    try:
        op.drop_column("organizations", "created_at")
    except Exception:
        pass

    try:
        op.drop_column("users", "updated_at")
    except Exception:
        pass

    try:
        op.drop_column("users", "created_at")
    except Exception:
        pass
