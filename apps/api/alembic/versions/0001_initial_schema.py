"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-09-25

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String, nullable=False, unique=True),
        sa.Column("auth_provider_id", sa.String, nullable=False, unique=True),
        sa.Column("plan_tier", sa.String, nullable=False, server_default="free"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_auth_provider_id", "users", ["auth_provider_id"])

    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("plan", sa.String, nullable=False, server_default="free"),
        sa.Column("status", sa.String, nullable=False, server_default="active"),
        sa.Column("renewal_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("monthly_token_budget", sa.Integer, nullable=False, server_default="0"),
    )
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"])

    op.create_table(
        "ingested_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("source_type", sa.String, nullable=False),
        sa.Column("source_url", sa.String, nullable=True),
        sa.Column("title", sa.String, nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("chunk_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("vector_collection_name", sa.String, nullable=False),
        sa.Column("status", sa.String, nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ingested_sources_user_id", "ingested_sources", ["user_id"])

    op.create_table(
        "watchlists",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("symbol", sa.String, nullable=False),
        sa.Column("timeframe", sa.String, nullable=False),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_watchlists_user_id", "watchlists", ["user_id"])

    op.create_table(
        "advisories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("symbol", sa.String, nullable=False),
        sa.Column("timeframe", sa.String, nullable=False),
        sa.Column("action", sa.String, nullable=False),
        sa.Column("confidence_score", sa.Float, nullable=False),
        sa.Column("payload_json", postgresql.JSONB, nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_advisories_user_id", "advisories", ["user_id"])

    op.create_table(
        "alert_deliveries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("advisory_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("advisories.id"), nullable=False),
        sa.Column("channel", sa.String, nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_alert_deliveries_advisory_id", "alert_deliveries", ["advisory_id"])

    op.create_table(
        "usage_counters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("tokens_used", sa.Integer, nullable=False, server_default="0"),
        sa.Column("api_calls_made", sa.Integer, nullable=False, server_default="0"),
        sa.Column("cost_estimate_usd", sa.Float, nullable=False, server_default="0"),
        sa.UniqueConstraint("user_id", "date", name="uq_usage_counters_user_date"),
    )
    op.create_index("ix_usage_counters_user_id", "usage_counters", ["user_id"])

    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("event_type", sa.String, nullable=False),
        sa.Column("detail_json", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_log_user_id", "audit_log", ["user_id"])


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("usage_counters")
    op.drop_table("alert_deliveries")
    op.drop_table("advisories")
    op.drop_table("watchlists")
    op.drop_table("ingested_sources")
    op.drop_table("subscriptions")
    op.drop_table("users")
