"""agents, delivery, forward-testing, connectors, trade journal

Revision ID: 0002_agents_delivery_connectors
Revises: 0001_initial_schema
Create Date: 2026-09-25

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_agents_delivery_connectors"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Telegram linking (Phase 6, Section 11: encrypted at rest)
    op.add_column("users", sa.Column("telegram_chat_id_encrypted", sa.String, nullable=True))

    # Forward paper-test tracking on a watchlist entry (Phase 6 / Section 9.3)
    op.add_column(
        "watchlists",
        sa.Column("forward_test_status", sa.String, nullable=False, server_default="not_started"),
    )
    op.add_column("watchlists", sa.Column("forward_test_started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("watchlists", sa.Column("forward_test_ends_at", sa.DateTime(timezone=True), nullable=True))

    # Advisory outcome grading (Phase 5 scorecard + Phase 6 forward-test grading)
    op.add_column("advisories", sa.Column("outcome", sa.String, nullable=False, server_default="open"))
    op.add_column("advisories", sa.Column("outcome_at", sa.DateTime(timezone=True), nullable=True))

    # Generic MCP connector framework (Section 20 / Phase 8)
    op.create_table(
        "connectors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("endpoint_url", sa.String, nullable=False),
        sa.Column("credentials_encrypted", sa.String, nullable=True),
        sa.Column("category", sa.String, nullable=False, server_default="custom"),
        sa.Column("status", sa.String, nullable=False, server_default="unverified"),
        sa.Column("discovered_tools", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("last_health_check_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_connectors_user_id", "connectors", ["user_id"])

    # Trade journal — manual log of trades actually taken (Section 19 page 16)
    op.create_table(
        "trade_journal_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("advisory_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("advisories.id"), nullable=True),
        sa.Column("symbol", sa.String, nullable=False),
        sa.Column("direction", sa.String, nullable=False),
        sa.Column("entry_price", sa.Float, nullable=False),
        sa.Column("exit_price", sa.Float, nullable=True),
        sa.Column("size", sa.Float, nullable=False),
        sa.Column("stop_loss", sa.Float, nullable=True),
        sa.Column("take_profit", sa.Float, nullable=True),
        sa.Column("pnl", sa.Float, nullable=True),
        sa.Column("notes", sa.String, nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_trade_journal_entries_user_id", "trade_journal_entries", ["user_id"])


def downgrade() -> None:
    op.drop_table("trade_journal_entries")
    op.drop_table("connectors")
    op.drop_column("advisories", "outcome_at")
    op.drop_column("advisories", "outcome")
    op.drop_column("watchlists", "forward_test_ends_at")
    op.drop_column("watchlists", "forward_test_started_at")
    op.drop_column("watchlists", "forward_test_status")
    op.drop_column("users", "telegram_chat_id_encrypted")
