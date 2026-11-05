import math
import logging
import uuid
from collections.abc import Sequence

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db import get_db
from .models import Contact, ContactGroup
from .schemas import ContactCreate, ContactPage, ContactPatch, ContactRead, ContactUpdate

app = FastAPI(
    title="Gestionnaire de Contacts",
    description="API REST de gestion de contacts professionnels.",
    version="1.0.0",
)
logger = logging.getLogger(__name__)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled API error for %s %s", request.method, request.url.path)
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
            detail="Un contact utilise déjà cette adresse e-mail.",
        ) from exc


def find_contact(db: Session, contact_id: uuid.UUID) -> Contact:
    contact = db.get(Contact, contact_id)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact introuvable.",
        )
    return contact


@app.get("/contacts/search", response_model=list[ContactRead], tags=["contacts"])
def search_contacts(
    q: str = Query(min_length=1, max_length=200),
    db: Session = Depends(get_db),
) -> Sequence[Contact]:
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


@app.get("/contacts", response_model=ContactPage, tags=["contacts"])
def list_contacts(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ContactPage:
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


@app.post(
    "/contacts",
    response_model=ContactRead,
    status_code=status.HTTP_201_CREATED,
    tags=["contacts"],
)
def create_contact(payload: ContactCreate, db: Session = Depends(get_db)) -> Contact:
    contact = Contact(**payload.model_dump())
    db.add(contact)
    commit_contact(db)
    db.refresh(contact)
    return contact


@app.get("/contacts/{contact_id}", response_model=ContactRead, tags=["contacts"])
def get_contact(contact_id: uuid.UUID, db: Session = Depends(get_db)) -> Contact:
    return find_contact(db, contact_id)


@app.put("/contacts/{contact_id}", response_model=ContactRead, tags=["contacts"])
def replace_contact(
    contact_id: uuid.UUID,
    payload: ContactUpdate,
    db: Session = Depends(get_db),
) -> Contact:
    contact = find_contact(db, contact_id)
    for field, value in payload.model_dump().items():
        setattr(contact, field, value)
    commit_contact(db)
    db.refresh(contact)
    return contact


@app.patch("/contacts/{contact_id}", response_model=ContactRead, tags=["contacts"])
def update_contact(
    contact_id: uuid.UUID,
    payload: ContactPatch,
    db: Session = Depends(get_db),
) -> Contact:
    contact = find_contact(db, contact_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(contact, field, value)
    commit_contact(db)
    db.refresh(contact)
    return contact


@app.delete(
    "/contacts/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["contacts"],
)
def delete_contact(contact_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    contact = find_contact(db, contact_id)
    db.delete(contact)
    db.commit()
