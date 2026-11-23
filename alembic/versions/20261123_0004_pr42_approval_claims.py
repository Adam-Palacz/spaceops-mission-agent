"""PR4.2: durable approvals and transactional execution claims."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261123_0004"
down_revision = "20260603_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "approval_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("idempotency_key", sa.Text(), nullable=False, unique=True),
        sa.Column("incident_id", sa.Text(), nullable=False),
        sa.Column("step_index", sa.Integer(), nullable=False),
        sa.Column("step", postgresql.JSONB(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("decided_at", sa.DateTime(timezone=True)),
        sa.Column("decided_by", sa.Text()),
        sa.Column(
            "execution_status",
            sa.Text(),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("execution_claim_token", postgresql.UUID(as_uuid=True)),
        sa.Column("execution_worker_id", sa.Text()),
        sa.Column("execution_claimed_at", sa.DateTime(timezone=True)),
        sa.Column("execution_lease_until", sa.DateTime(timezone=True)),
        sa.Column(
            "execution_attempts",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("execution_completed_at", sa.DateTime(timezone=True)),
        sa.Column("execution_result", postgresql.JSONB()),
        sa.Column("execution_error", sa.Text()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="ck_approval_requests_status",
        ),
        sa.CheckConstraint(
            "execution_status IN ('pending', 'claimed', 'succeeded', 'failed')",
            name="ck_approval_requests_execution_status",
        ),
    )
    op.create_index(
        "ix_approval_requests_status_created",
        "approval_requests",
        ["status", "created_at"],
    )
    op.create_index(
        "ix_approval_requests_execution_lease",
        "approval_requests",
        ["execution_lease_until"],
        postgresql_where=sa.text("execution_status = 'claimed'"),
    )


def downgrade() -> None:
    op.drop_index(
        "ix_approval_requests_execution_lease",
        table_name="approval_requests",
    )
    op.drop_index("ix_approval_requests_status_created", table_name="approval_requests")
    op.drop_table("approval_requests")
