import uuid
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import (
    CurrentUser,
    SessionDep,
)
from app.models import (
    Event,
    EventCreate,
    EventPublic,
    EventsListPublic,
    Inviteation,
    Message,
    User,
)

router = APIRouter(prefix="/evetns", tags=["events"])


@router.get(
    "/",
    response_model=EventsListPublic,
)
def read_events(
    session: SessionDep,
    current_user: CurrentUser = None,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve events.
    """
    count_statement = (
        select(func.count())
        .select_from(Event)
        .where(
            Event.is_private is False
            or current_user is Event.invited_users
            or current_user is Event.creator
        )
    )
    count = session.exec(count_statement).one()

    statement = (
        select(Event)
        .offset(skip)
        .where(Event.is_private is False or current_user is Event.invited_users)
        .limit(limit)
    )
    events = session.exec(statement).all()

    return EventsListPublic(data=events, count=count)


@router.post("/create-event", response_model=EventPublic)
def create_event(
    *, session: SessionDep, new_event: EventCreate, current_user: CurrentUser
) -> Any:
    """
    Create new event.
    """
    event = Event.model_validate(new_event)
    event.creator = current_user
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


@router.get("/{event_id}", response_model=EventPublic)
def read_event_by_id(
    event_id: uuid.UUID, session: SessionDep, current_user: CurrentUser = None
) -> Any:
    """
    Get a specific event by id.
    """
    event = session.get(Event, event_id).where(
        Event.is_private is False
        or current_user is Event.invited_users
        or current_user is Event.creator
    )
    return event


@router.patch(
    "/update/{event_id}",
    response_model=EventPublic,
)
def update_event(
    *,
    session: SessionDep,
    event_id: uuid.UUID,
    event_in: Event,
    current_user: CurrentUser,
) -> Any:
    """
    Update a event.
    """
    db_user = session.get(Event, event_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="The event with this id does not exist in the system",
        )
    if current_user is not db_user.creator:
        raise HTTPException(
            status_code=405,
            detail="This event belong to someone else",
        )

    session.add(event_in)
    session.commit()
    session.refresh(event_in)
    return event_in


@router.delete("/delete/{event_id}")
def delete_person(
    session: SessionDep, current_user: CurrentUser, event_id: uuid.UUID
) -> Message:
    """
    Delete a Event.
    """
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if current_user is not event.creator:
        raise HTTPException(
            status_code=405,
            detail="This event belong to someone else",
        )
    session.delete(event)
    session.commit()
    return Message(message="Event deleted successfully")


@router.post(
    "/attend/{event_id}",
)
def attend_event(
    session: SessionDep, current_user: CurrentUser, event_id: uuid.UUID
) -> Message:
    """
    Attend to Event.
    """
    event = session.get(Event, event_id).where(
        Event.is_private is False
        or current_user is Event.invited_users
        or current_user is Event.creator
    )
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    event.attends.append(current_user)
    session.add(event)
    session.commit()
    session.refresh(event)
    return Message(message="Attends successfully")


@router.post("/cancel-attendee/{event_id}")
def cancel_attendee(
    session: SessionDep, current_user: CurrentUser, event_id: uuid.UUID
) -> Message:
    """
    cancel attendees to Event.
    """
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if current_user not in event.attends:
        raise HTTPException(
            status_code=404,
            detail="The user doesn't follow this event",
        )
    event.attends.remove(current_user)
    session.add(event)
    session.commit()
    session.refresh(event)
    return Message(message="Cancel attendees successfully")


@router.post("/remove-attendee/{event_id}")
def remove_attendee(
    session: SessionDep,
    user_id: uuid.UUID,
    current_user: CurrentUser,
    event_id: uuid.UUID,
) -> Message:
    """
    Remove attendees from Event.
    """
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if current_user is not event.creator:
        raise HTTPException(
            status_code=405,
            detail="The event doesn't belong to this user",
        )

    user_to_remove = session.get(User, user_id)
    if not user_to_remove:
        raise HTTPException(status_code=404, detail="User not found")
    if user_to_remove not in event.attends:
        raise HTTPException(status_code=404, detail="User not found in this event")
    event.attends.remove(user_to_remove)
    session.add(event)
    session.commit()
    session.refresh(event)
    return Message(message="Remove attendee successfully")


@router.post("/create-invite", response_model=uuid.UUID)
def create_invitation(
    *,
    session: SessionDep,
    event_id: uuid.UUID,
    current_user: CurrentUser,
    expire_time: datetime = datetime.now() + timedelta(30),
) -> Any:
    """
    Create new invitation.
    """
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if current_user is not event.creator:
        raise HTTPException(
            status_code=405,
            detail="The event doesn't belong to this user",
        )
    invitation = Inviteation(expire_time=expire_time, creator=current_user, event=event)
    session.add(invitation)
    session.commit()
    session.refresh(invitation)
    return invitation.id
