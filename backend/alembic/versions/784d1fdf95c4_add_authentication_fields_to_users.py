"""add authentication fields to users

Revision ID: 784d1fdf95c4
Revises: 81a629525629
Create Date: 2026-08-31 12:00:54.991670

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '784d1fdf95c4'
down_revision: Union[str, None] = '81a629525629'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # email/password_hash start nullable so the ADD COLUMN succeeds against
    # the existing dev_user row, which has neither yet. We backfill that
    # row below, then tighten both columns to NOT NULL.
    op.add_column('users', sa.Column('email', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('password_hash', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False))
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), server_default='false', nullable=False))
    op.alter_column('users', 'username',
               existing_type=sa.VARCHAR(length=50),
               nullable=True)

    # Turn the pre-existing dev_user row into the working admin account.
    # Same email/password the seed script uses for a fresh database, so an
    # upgraded database and a freshly-seeded one end up identical. See
    # README.md for the dev password (never printed here or in logs).
    from app.services.auth_service import DEV_ADMIN_EMAIL, DEV_ADMIN_PASSWORD, hash_password

    users_table = sa.table(
        'users',
        sa.column('username', sa.String),
        sa.column('email', sa.String),
        sa.column('password_hash', sa.String),
        sa.column('is_admin', sa.Boolean),
    )
    op.execute(
        users_table.update()
        .where(users_table.c.username == 'dev_user')
        .values(
            email=DEV_ADMIN_EMAIL,
            password_hash=hash_password(DEV_ADMIN_PASSWORD),
            is_admin=True,
        )
    )

    op.alter_column('users', 'email', existing_type=sa.String(length=255), nullable=False)
    op.alter_column('users', 'password_hash', existing_type=sa.String(length=255), nullable=False)
    op.create_unique_constraint('uq_users_email', 'users', ['email'])


def downgrade() -> None:
    # Note: this fails if any user row has a NULL username (e.g. anyone who
    # registered through /api/auth/register after this migration ran),
    # since username is being forced back to NOT NULL. Expected — this
    # project doesn't guarantee a clean downgrade after real usage.
    op.drop_constraint('uq_users_email', 'users', type_='unique')
    op.alter_column('users', 'username',
               existing_type=sa.VARCHAR(length=50),
               nullable=False)
    op.drop_column('users', 'is_admin')
    op.drop_column('users', 'is_active')
    op.drop_column('users', 'password_hash')
    op.drop_column('users', 'email')
