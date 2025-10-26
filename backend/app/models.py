import uuid
from datetime import datetime

from pydantic import EmailStr, HttpUrl
from sqlmodel import Field, Relationship, SQLModel


class UserEventsInvitesLink(SQLModel, table=True):
    event_id: uuid.UUID | None = Field(
        default=None, foreign_key="event.id", primary_key=True
    )
    user_id: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", primary_key=True
    )


class UserEventsAttendeesLink(SQLModel, table=True):
    event_id: uuid.UUID | None = Field(
        default=None, foreign_key="event.id", primary_key=True
    )
    user_id: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", primary_key=True
    )


class PersonEventsLink(SQLModel, table=True):
    event_id: uuid.UUID | None = Field(
        default=None, foreign_key="event.id", primary_key=True
    )
    person_id: uuid.UUID | None = Field(
        default=None, foreign_key="person.id", primary_key=True
    )


class PersonUserOwnersLink(SQLModel, table=True):
    user_id: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", primary_key=True
    )
    person_id: uuid.UUID | None = Field(
        default=None, foreign_key="person.id", primary_key=True
    )


class PersonUserFollowersLink(SQLModel, table=True):
    user_id: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", primary_key=True
    )
    person_id: uuid.UUID | None = Field(
        default=None, foreign_key="person.id", primary_key=True
    )
    notify: bool = Field(default=True)


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
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
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
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)

    created_date: datetime = Field(default_factory=datetime.now)
    last_modified: datetime = Field(
        default_factory=datetime.now, sa_column_kwargs={"onupdate": datetime.now}
    )
    owns: list["Person"] = Relationship(
        back_populates="owners", link_model=PersonUserOwnersLink
    )
    follows: list["Person"] = Relationship(
        back_populates="followers", link_model=PersonUserFollowersLink
    )
    attend_events: list["Event"] = Relationship(
        back_populates="attends", link_model=UserEventsAttendeesLink
    )
    invited_events: list["Event"] = Relationship(
        back_populates="invited_users", link_model=UserEventsInvitesLink
    )
    inviteation_created: list["Inviteation"] = Relationship(back_populates="creator")

    events_created: list["Event"] = Relationship(back_populates="created")


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


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


class PersonBase(SQLModel):
    first_name: str = Field(min_length=1, max_length=255)
    last_name: str = Field(min_length=1, max_length=255)
    birthdate: datetime | None = Field(default=None)
    memorialdate: datetime | None = Field(default=None)
    description: str | None = Field(default=None)
    # personalmemoryweblinks: Optional[list[HttpUrl]] = Field(default=None, sa_type="JSON")
    # officialmemoryweblinks: Optional[list[HttpUrl]] = Field(default=None, sa_type="JSON")


class PersonPublic(PersonBase):
    id: uuid.UUID


class Person(PersonBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owners: list[User] = Relationship(
        back_populates="owns", link_model=PersonUserOwnersLink
    )
    followers: list["User"] = Relationship(
        back_populates="follows", link_model=PersonUserFollowersLink
    )
    events: list["Event"] = Relationship(
        back_populates="persons", link_model=PersonEventsLink
    )

    created_date: datetime = Field(default_factory=datetime.now)
    last_modified: datetime = Field(
        default_factory=datetime.now, sa_column_kwargs={"onupdate": datetime.now}
    )


class PersonListPublic(SQLModel):
    persons: list["PersonPublic"]
    count: int


class PersonCreate(PersonBase):
    pass


class PersonUpdate(PersonBase):
    pass


class EventBase(SQLModel):
    starttime: datetime | None = Field(default=None)
    endtime: datetime | None = Field(default=None)
    description: str | None = Field(default=None)
    location: str | None = Field(default=None)
    is_private: bool = Field(default=False)


class Event(EventBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    creator: User = Relationship(back_populates="events_created")
    persons: list[Person] = Relationship(
        back_populates="events", link_model=PersonEventsLink
    )
    attends: list[User] = Relationship(
        back_populates="attend_events", link_model=UserEventsAttendeesLink
    )
    invited_users: list[User] = Relationship(
        back_populates="invited_events", link_model=UserEventsInvitesLink
    )
    inviteation_created: list["Inviteation"] = Relationship(back_populates="event")
    created_date: datetime = Field(default_factory=datetime.now)
    last_modified: datetime = Field(
        default_factory=datetime.now, sa_column_kwargs={"onupdate": datetime.now}
    )


class EventCreate(EventBase):
    pass


class EventUpdate(EventBase):
    pass


class EventPublic(EventBase):
    id: uuid.UUID


class EventsListPublic(SQLModel):
    events: list[EventPublic]
    count: int


class InviteationBase(SQLModel):
    token: uuid.UUID = Field(default_factory=uuid.uuid4)


class InviteationPublic(InviteationBase):
    url: HttpUrl | None


class Inviteation(InviteationBase, table=True):
    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    creator: User = Relationship(back_populates="inviteation_created")
    event: Event = Relationship(back_populates="inviteation_created")
    created_time: datetime = Field(default_factory=datetime.now)
    expire_time: datetime
