import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, Text, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ContactGroup(str, enum.Enum):
    CLIENT = "CLIENT"
    PARTENAIRE = "PARTENAIRE"
    FOURNISSEUR = "FOURNISSEUR"
    AUTRE = "AUTRE"


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    nom: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    prenom: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    telephone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    entreprise: Mapped[str | None] = mapped_column(String(150), nullable=True)
    groupe: Mapped[ContactGroup] = mapped_column(
        Enum(
            ContactGroup,
            name="contact_group",
            values_callable=lambda members: [member.value for member in members],
        ),
        nullable=False,
        default=ContactGroup.AUTRE,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
