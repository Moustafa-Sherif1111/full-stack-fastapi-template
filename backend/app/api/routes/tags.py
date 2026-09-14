"""Tags CRUD endpoints.

Introduced in v1.1.0 — allows users to create and manage coloured tags
that can be attached to Items for organisation purposes.
"""
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Message,
    Tag,
    TagCreate,
    TagPublic,
    TagsPublic,
    TagUpdate,
)

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("/", response_model=TagsPublic)
def read_tags(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """Return all tags owned by the current user."""
    count_stmt = (
        select(func.count())
        .select_from(Tag)
        .where(Tag.owner_id == current_user.id)
    )
    count = session.exec(count_stmt).one()

    stmt = (
        select(Tag)
        .where(Tag.owner_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    tags = session.exec(stmt).all()
    return TagsPublic(data=list(tags), count=count)


@router.get("/{tag_id}", response_model=TagPublic)
def read_tag(
    tag_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Return a single tag by ID (must be owned by current user)."""
    tag = session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    if tag.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return tag


@router.post("/", response_model=TagPublic, status_code=201)
def create_tag(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    tag_in: TagCreate,
) -> Any:
    """Create a new tag for the current user."""
    # Prevent duplicate tag names per user
    existing = session.exec(
        select(Tag)
        .where(Tag.owner_id == current_user.id, Tag.name == tag_in.name)
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Tag with name '{tag_in.name}' already exists",
        )

    tag = Tag.model_validate(tag_in, update={"owner_id": current_user.id})
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag


@router.patch("/{tag_id}", response_model=TagPublic)
def update_tag(
    tag_id: uuid.UUID,
    *,
    session: SessionDep,
    current_user: CurrentUser,
    tag_in: TagUpdate,
) -> Any:
    """Partially update a tag."""
    tag = session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    if tag.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    update_data = tag_in.model_dump(exclude_unset=True)
    tag.sqlmodel_update(update_data)
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag


@router.delete("/{tag_id}", response_model=Message)
def delete_tag(
    tag_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Delete a tag. The tag is automatically unlinked from all items."""
    tag = session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    if tag.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    session.delete(tag)
    session.commit()
    return Message(message="Tag deleted successfully")
