import logging
import math
import uuid
from collections.abc import Sequence

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db import get_db
from .models import Contact, ContactGroup
from .schemas import (
    ContactCreate,
    ContactPage,
    ContactPageV2,
    ContactPatch,
    ContactRead,
    ContactReadV2,
    ContactUpdate,
)

app = FastAPI(
    title="Gestionnaire de Contacts",
    description=(
        "API REST de gestion de contacts professionnels. Consultez les contrats "
        "versionnÃ©s dans Swagger UI : `/api/v1` (stable) et `/api/v2` (avec le "
        "champ calculÃ© `nom_complet`)."
    ),
    version="2.0.0",
    openapi_tags=[
        {"name": "v1", "description": "Version 1 stable de l'API Contacts."},
        {"name": "v2", "description": "Version 2, avec nom_complet ajoutÃ© aux rÃ©ponses."},
    ],
)
logger = logging.getLogger(__name__)
v1_router = APIRouter()
v2_router = APIRouter()


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, _exc: Exception) -> JSONResponse:
    logger.error(
        "Unhandled API error for %s %s",
        request.method,
        request.url.path,
        exc_info=(_exc.__class__, _exc, _exc.__traceback__),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Une erreur interne est survenue."},
    )


def commit_contact(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un contact utilise d\u00e9j\u00e0 cette adresse e-mail.",
        ) from exc


def find_contact(db: Session, contact_id: uuid.UUID) -> Contact:
    contact = db.get(Contact, contact_id)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact introuvable.",
        )
    return contact


def search_contacts_data(db: Session, q: str) -> Sequence[Contact]:
    pattern = f"%{q}%"
    conditions = [
        Contact.nom.ilike(pattern),
        Contact.prenom.ilike(pattern),
        Contact.email.ilike(pattern),
    ]
    try:
        group = ContactGroup(q.upper())
    except ValueError:
        pass
    else:
        conditions.append(Contact.groupe == group)
    return db.scalars(
        select(Contact)
        .where(or_(*conditions))
        .order_by(Contact.nom, Contact.prenom, Contact.id)
    ).all()


def list_contacts_data(db: Session, page: int, limit: int) -> ContactPage:
    total = db.scalar(select(func.count()).select_from(Contact)) or 0
    contacts = db.scalars(
        select(Contact)
        .order_by(Contact.nom, Contact.prenom, Contact.id)
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()
    return ContactPage(
        items=contacts,
        total=total,
        page=page,
        limit=limit,
        pages=math.ceil(total / limit),
    )


def create_contact_data(db: Session, payload: ContactCreate) -> Contact:
    contact = Contact(**payload.model_dump())
    db.add(contact)
    commit_contact(db)
    db.refresh(contact)
    return contact


def replace_contact_data(
    db: Session,
    contact_id: uuid.UUID,
    payload: ContactUpdate,
) -> Contact:
    contact = find_contact(db, contact_id)
    for field, value in payload.model_dump().items():
        setattr(contact, field, value)
    commit_contact(db)
    db.refresh(contact)
    return contact


def update_contact_data(
    db: Session,
    contact_id: uuid.UUID,
    payload: ContactPatch,
) -> Contact:
    contact = find_contact(db, contact_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(contact, field, value)
    commit_contact(db)
    db.refresh(contact)
    return contact


def delete_contact_data(db: Session, contact_id: uuid.UUID) -> None:
    contact = find_contact(db, contact_id)
    db.delete(contact)
    db.commit()


@v1_router.get("/contacts/search", response_model=list[ContactRead])
def search_contacts_v1(
    q: str = Query(min_length=1, max_length=200),
    db: Session = Depends(get_db),
) -> Sequence[Contact]:
    """Search contacts by name, email, or group (v1)."""
    return search_contacts_data(db, q)


@v1_router.get("/contacts", response_model=ContactPage)
def list_contacts_v1(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ContactPage:
    """Return a paginated contact list (v1)."""
    return list_contacts_data(db, page, limit)


@v1_router.post(
    "/contacts",
    response_model=ContactRead,
    status_code=status.HTTP_201_CREATED,
)
def create_contact_v1(payload: ContactCreate, db: Session = Depends(get_db)) -> Contact:
    """Create a contact (v1)."""
    return create_contact_data(db, payload)


@v1_router.get("/contacts/{contact_id}", response_model=ContactRead)
def get_contact_v1(contact_id: uuid.UUID, db: Session = Depends(get_db)) -> Contact:
    """Retrieve one contact by UUID (v1)."""
    return find_contact(db, contact_id)


@v1_router.put("/contacts/{contact_id}", response_model=ContactRead)
def replace_contact_v1(
    contact_id: uuid.UUID,
    payload: ContactUpdate,
    db: Session = Depends(get_db),
) -> Contact:
    """Replace a contact (v1)."""
    return replace_contact_data(db, contact_id, payload)


@v1_router.patch("/contacts/{contact_id}", response_model=ContactRead)
def update_contact_v1(
    contact_id: uuid.UUID,
    payload: ContactPatch,
    db: Session = Depends(get_db),
) -> Contact:
    """Partially update a contact (v1)."""
    return update_contact_data(db, contact_id, payload)


@v1_router.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact_v1(contact_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    """Delete a contact (v1)."""
    delete_contact_data(db, contact_id)


@v2_router.get("/contacts/search", response_model=list[ContactReadV2])
def search_contacts_v2(
    q: str = Query(min_length=1, max_length=200),
    db: Session = Depends(get_db),
) -> Sequence[Contact]:
    """Search contacts by name, email, or group (v2 includes nom_complet)."""
    return search_contacts_data(db, q)


@v2_router.get("/contacts", response_model=ContactPageV2)
def list_contacts_v2(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ContactPageV2:
    """Return a paginated contact list with nom_complet (v2)."""
    page_data = list_contacts_data(db, page, limit)
    return ContactPageV2(
        items=[
            ContactReadV2(
                **item.model_dump(),
                nom_complet=" ".join(
                    part for part in (item.prenom, item.nom) if part
                ),
            )
            for item in page_data.items
        ],
        total=page_data.total,
        page=page_data.page,
        limit=page_data.limit,
        pages=page_data.pages,
    )


@v2_router.post(
    "/contacts",
    response_model=ContactReadV2,
    status_code=status.HTTP_201_CREATED,
)
def create_contact_v2(payload: ContactCreate, db: Session = Depends(get_db)) -> Contact:
    """Create a contact (v2 response adds nom_complet)."""
    return create_contact_data(db, payload)


@v2_router.get("/contacts/{contact_id}", response_model=ContactReadV2)
def get_contact_v2(contact_id: uuid.UUID, db: Session = Depends(get_db)) -> Contact:
    """Retrieve one contact by UUID (v2)."""
    return find_contact(db, contact_id)


@v2_router.put("/contacts/{contact_id}", response_model=ContactReadV2)
def replace_contact_v2(
    contact_id: uuid.UUID,
    payload: ContactUpdate,
    db: Session = Depends(get_db),
) -> Contact:
    """Replace a contact (v2 response adds nom_complet)."""
    return replace_contact_data(db, contact_id, payload)


@v2_router.patch("/contacts/{contact_id}", response_model=ContactReadV2)
def update_contact_v2(
    contact_id: uuid.UUID,
    payload: ContactPatch,
    db: Session = Depends(get_db),
) -> Contact:
    """Partially update a contact (v2 response adds nom_complet)."""
    return update_contact_data(db, contact_id, payload)


@v2_router.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact_v2(contact_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    """Delete a contact (v2)."""
    delete_contact_data(db, contact_id)


app.include_router(v1_router, prefix="/api/v1", tags=["v1"])
app.include_router(v2_router, prefix="/api/v2", tags=["v2"])
# Keep pre-versioning URLs available while clients move to /api/v1.
app.include_router(v1_router, include_in_schema=False)
