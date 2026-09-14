import uuid
from datetime import UTC, datetime

from pydantic import EmailStr
from sqlalchemy import DateTime
from sqlmodel import Field, Relationship, SQLModel


def get_datetime_utc() -> datetime:
    return datetime.now(UTC)


# ---------------------------------------------------------------------------
# Tag  (new in v1.1.0)
# ---------------------------------------------------------------------------

class TagBase(SQLModel):
    name: str = Field(min_length=1, max_length=64, index=True)
    color: str | None = Field(default=None, max_length=7)  # hex colour e.g. #ff5733


class TagCreate(TagBase):
    pass


class TagUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    color: str | None = Field(default=None, max_length=7)


# Many-to-many link table between Item and Tag
class ItemTagLink(SQLModel, table=True):
    item_id: uuid.UUID = Field(foreign_key="item.id", primary_key=True, ondelete="CASCADE")
    tag_id: uuid.UUID = Field(foreign_key="tag.id", primary_key=True, ondelete="CASCADE")


class Tag(TagBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    owner_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    owner: "User | None" = Relationship(back_populates="tags")
    items: list["Item"] = Relationship(back_populates="tags", link_model=ItemTagLink)


class TagPublic(TagBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime | None = None


class TagsPublic(SQLModel):
    data: list[TagPublic]
    count: int


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(SQLModel):
    email: EmailStr | None = Field(default=None, max_length=255)
    is_active: bool | None = None
    is_superuser: bool | None = None
    full_name: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)
    tags: list[Tag] = Relationship(back_populates="owner", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime | None = None


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# ---------------------------------------------------------------------------
# Item
# ---------------------------------------------------------------------------

# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    tag_ids: list[uuid.UUID] = Field(default_factory=list)


# Properties to receive on item update
class ItemUpdate(SQLModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)
    tag_ids: list[uuid.UUID] | None = None


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")
    tags: list[Tag] = Relationship(back_populates="items", link_model=ItemTagLink)


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime | None = None
    tags: list[TagPublic] = []


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# ---------------------------------------------------------------------------
# Auth / generic
# ---------------------------------------------------------------------------

# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)
