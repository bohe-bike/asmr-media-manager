"""init

Revision ID: f92e52ff0691
Revises: 
Create Date: 2026-05-19 13:45:59.943112
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f92e52ff0691'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "author_rules",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("keyword", sa.Text(), nullable=False),
        sa.Column("match_type", sa.String(length=20), nullable=False),
        sa.Column("match_target", sa.String(length=30), nullable=False),
        sa.Column("creator", sa.String(length=200), nullable=True),
        sa.Column("circle", sa.String(length=200), nullable=True),
        sa.Column("cv", sa.String(length=200), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("hit_count", sa.Integer(), nullable=False),
        sa.Column("last_hit_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "match_target IN ('filename', 'metadata_artist', 'metadata_album', 'directory', 'all')",
            name="check_match_target",
        ),
        sa.CheckConstraint(
            "match_type IN ('contains', 'exact', 'regex', 'prefix', 'suffix')",
            name="check_match_type",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_author_rules_circle"), "author_rules", ["circle"], unique=False)
    op.create_index(op.f("ix_author_rules_creator"), "author_rules", ["creator"], unique=False)
    op.create_index(op.f("ix_author_rules_enabled"), "author_rules", ["enabled"], unique=False)
    op.create_index(op.f("ix_author_rules_keyword"), "author_rules", ["keyword"], unique=False)
    op.create_index(op.f("ix_author_rules_priority"), "author_rules", ["priority"], unique=False)

    op.create_table(
        "media",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("file_name", sa.Text(), nullable=False),
        sa.Column("file_hash", sa.String(length=64), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("media_type", sa.String(length=10), nullable=False),
        sa.Column("format", sa.String(length=20), nullable=False),
        sa.Column("duration", sa.Float(), nullable=True),
        sa.Column("bitrate", sa.Integer(), nullable=True),
        sa.Column("sample_rate", sa.Integer(), nullable=True),
        sa.Column("channels", sa.Integer(), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("rj_id", sa.String(length=20), nullable=True),
        sa.Column("dl_id", sa.String(length=20), nullable=True),
        sa.Column("creator", sa.String(length=200), nullable=True),
        sa.Column("circle", sa.String(length=200), nullable=True),
        sa.Column("cv", sa.String(length=200), nullable=True),
        sa.Column("platform", sa.String(length=20), nullable=True),
        sa.Column("language", sa.String(length=10), nullable=True),
        sa.Column("cover_path", sa.Text(), nullable=True),
        sa.Column("nfo_path", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("plex_ready", sa.Boolean(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("scanned_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("media_type IN ('audio', 'video')", name="check_media_type"),
        sa.CheckConstraint(
            "language IN ('ja', 'zh', 'en', 'other') OR language IS NULL",
            name="check_language",
        ),
        sa.CheckConstraint(
            "platform IN ('dlsite', 'patreon', 'youtube', 'other') OR platform IS NULL",
            name="check_platform",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'processed', 'renamed', 'error')",
            name="check_status",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("file_path"),
    )
    op.create_index(op.f("ix_media_creator"), "media", ["creator"], unique=False)
    op.create_index(op.f("ix_media_cv"), "media", ["cv"], unique=False)
    op.create_index(op.f("ix_media_file_hash"), "media", ["file_hash"], unique=False)
    op.create_index(op.f("ix_media_media_type"), "media", ["media_type"], unique=False)
    op.create_index(op.f("ix_media_rj_id"), "media", ["rj_id"], unique=False)
    op.create_index(op.f("ix_media_status"), "media", ["status"], unique=False)

    op.create_table(
        "scan_jobs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("scan_path", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("scan_type", sa.String(length=20), nullable=False),
        sa.Column("total_files", sa.Integer(), nullable=True),
        sa.Column("processed_files", sa.Integer(), nullable=True),
        sa.Column("new_files", sa.Integer(), nullable=True),
        sa.Column("error_files", sa.Integer(), nullable=True),
        sa.Column("errors", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=True),
        sa.Column("source", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tags_name"), "tags", ["name"], unique=True)

    op.create_table(
        "media_tags",
        sa.Column("media_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("source", sa.String(length=20), nullable=True),
        sa.ForeignKeyConstraint(["media_id"], ["media.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("media_id", "tag_id"),
    )


def downgrade() -> None:
    op.drop_table("media_tags")
    op.drop_index(op.f("ix_tags_name"), table_name="tags")
    op.drop_table("tags")
    op.drop_table("scan_jobs")
    op.drop_index(op.f("ix_media_status"), table_name="media")
    op.drop_index(op.f("ix_media_rj_id"), table_name="media")
    op.drop_index(op.f("ix_media_media_type"), table_name="media")
    op.drop_index(op.f("ix_media_file_hash"), table_name="media")
    op.drop_index(op.f("ix_media_cv"), table_name="media")
    op.drop_index(op.f("ix_media_creator"), table_name="media")
    op.drop_table("media")
    op.drop_index(op.f("ix_author_rules_priority"), table_name="author_rules")
    op.drop_index(op.f("ix_author_rules_keyword"), table_name="author_rules")
    op.drop_index(op.f("ix_author_rules_enabled"), table_name="author_rules")
    op.drop_index(op.f("ix_author_rules_creator"), table_name="author_rules")
    op.drop_index(op.f("ix_author_rules_circle"), table_name="author_rules")
    op.drop_table("author_rules")
