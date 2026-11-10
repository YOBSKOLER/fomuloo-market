import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from .models import ContactGroup


class ContactCreate(BaseModel):
    nom: str = Field(min_length=1, max_length=100)
    prenom: str | None = Field(default=None, max_length=100)
    email: EmailStr
    telephone: str | None = Field(default=None, max_length=30)
    entreprise: str | None = Field(default=None, max_length=150)
    groupe: ContactGroup = ContactGroup.AUTRE
    notes: str | None = None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower()


class ContactUpdate(ContactCreate):
    pass


class ContactPatch(BaseModel):
    nom: str | None = Field(default=None, min_length=1, max_length=100)
    prenom: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = None
    telephone: str | None = Field(default=None, max_length=30)
    entreprise: str | None = Field(default=None, max_length=150)
    groupe: ContactGroup | None = None
    notes: str | None = None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr | None) -> str | None:
        return str(value).lower() if value is not None else None

    @model_validator(mode="after")
    def require_at_least_one_field(self) -> "ContactPatch":
        if not self.model_fields_set:
            raise ValueError("Au moins un champ doit être fourni.")
        return self


class ContactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nom: str
    prenom: str | None
    email: EmailStr
    telephone: str | None
    entreprise: str | None
    groupe: ContactGroup
    notes: str | None
    created_at: datetime
    updated_at: datetime


class ContactReadV2(ContactRead):
    nom_complet: str


class ContactPage(BaseModel):
    items: list[ContactRead]
    total: int
    page: int
    limit: int
    pages: int


class ContactPageV2(BaseModel):
    items: list[ContactReadV2]
    total: int
    page: int
    limit: int
    pages: int


class ErrorResponse(BaseModel):
    detail: str | list[dict[str, object]]
