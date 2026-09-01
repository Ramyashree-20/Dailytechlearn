"""create topics table

Revision ID: f3230de49d24
Revises:
Create Date: 2026-09-01 21:39:18.394004

Fixes a real gap found deploying to a fresh database (Neon via Render):
the `topics` table was never created by any Alembic migration — the
original root migration (5907ee5aeff8, "add questions table") creates
`questions` with `FOREIGN KEY(topic_id) REFERENCES topics(id)`, assuming
`topics` already existed. That was true on every database this project
had run against so far, because `topics` (along with `questions`) was
created directly via `Base.metadata.create_all()` very early on, before
Alembic was introduced in Phase 2 — so every existing database (local dev
included) has always had a `topics` table Alembic never actually created
and therefore never tracked.

This migration is inserted as the new ROOT (down_revision=None), ahead of
5907ee5aeff8, so a completely empty database creates `topics` before
`questions` needs it. It recreates exactly the columns `topics` had at
that point in project history — before category_id/importance/active
existed (those are added later by 345a257932b1, further down the chain,
unchanged by this fix).

Existing databases (local dev, or any database that already has a
`topics` table and is already at or past 5907ee5aeff8 in its recorded
`alembic_version`) are unaffected: Alembic only runs migrations between a
database's current recorded version and the target, never migrations
"behind" where it already is — so this new root never runs against them.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3230de49d24'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'topics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('topics')
