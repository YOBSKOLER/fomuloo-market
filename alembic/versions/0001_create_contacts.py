"""Create contacts table.

Revision ID: 0001_create_contacts
Revises:
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0001_create_contacts"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

contact_group = sa.Enum(
    "CLIENT",
    "PARTENAIRE",
    "FOURNISSEUR",
    "AUTRE",
    name="contact_group",
)


def upgrade() -> None:
    op.create_table(
        "contacts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("nom", sa.String(length=100), nullable=False),
        sa.Column("prenom", sa.String(length=100), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("telephone", sa.String(length=30), nullable=True),
        sa.Column("entreprise", sa.String(length=150), nullable=True),
        sa.Column("groupe", contact_group, nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_contacts_nom", "contacts", ["nom"], unique=False)
    op.create_index("ix_contacts_email", "contacts", ["email"], unique=True)
    op.create_index("ix_contacts_groupe", "contacts", ["groupe"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_contacts_groupe", table_name="contacts")
    op.drop_index("ix_contacts_email", table_name="contacts")
    op.drop_index("ix_contacts_nom", table_name="contacts")
    op.drop_table("contacts")
