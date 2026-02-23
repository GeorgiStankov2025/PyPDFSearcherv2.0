"""Add user role

Revision ID: 19a3792a13a4
Revises: 4de68c6f3aa3
Create Date: 2026-02-23 16:33:03.679095

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '19a3792a13a4'
down_revision: Union[str, Sequence[str], None] = '4de68c6f3aa3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    # 1. Create the type manually first
    # This is what Postgres is complaining is missing
    user_role_type = sa.Enum('ADMIN', 'USER', name='user_role')
    user_role_type.create(op.get_bind(), checkfirst=True)

    # 2. Now the column creation will work
    op.add_column('users', sa.Column('user_role', user_role_type, server_default='USER', nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    op.drop_column('users', 'user_role')
    # Drop the type so you can recreate it if you run the migration again
    sa.Enum(name='user_role').drop(op.get_bind(), checkfirst=True)
