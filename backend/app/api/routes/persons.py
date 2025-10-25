import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import (
    CurrentUser,
    SessionDep,
)
from app.models import (
    Message,
    Person,
    PersonCreate,
    PersonListPublic,
    PersonPublic,
)

router = APIRouter(prefix="/persons", tags=["persons"])


@router.get(
    "/",
    response_model=PersonListPublic,
)
def read_persons(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve persons.
    """
    count_statement = select(func.count()).select_from(Person)
    count = session.exec(count_statement).one()

    statement = select(Person).offset(skip).limit(limit)
    persons = session.exec(statement).all()

    return PersonListPublic(data=persons, count=count)


@router.post("/create", response_model=PersonPublic)
def create_person(
    *, session: SessionDep, new_person: PersonCreate, current_user: CurrentUser
) -> Any:
    """
    Create new person.
    """
    person = Person.model_validate(new_person)
    person.owners.append(current_user)
    person.followers.append(current_user)
    session.add(person)
    session.commit()
    session.refresh(person)
    return person


@router.get("/{person_id}", response_model=PersonPublic)
def read_person_by_id(person_id: uuid.UUID, session: SessionDep) -> Any:
    """
    Get a specific person by id.
    """
    person = session.get(Person, person_id)
    return person


@router.patch(
    "/{person_id}",
    response_model=PersonPublic,
)
def update_person(
    *,
    session: SessionDep,
    person_id: uuid.UUID,
    person_in: Person,
    current_user: CurrentUser,
) -> Any:
    """
    Update a person.
    """

    db_user = session.get(Person, person_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="The person with this id does not exist in the system",
        )
    if current_user not in db_user.owners:
        raise HTTPException(
            status_code=403,
            detail="The user isn't owner for this person",
        )

    session.add(person_in)
    session.commit()
    session.refresh(person_in)
    return person_in


@router.delete("/{person_id}")
def delete_person(
    session: SessionDep, current_user: CurrentUser, person_id: uuid.UUID
) -> Message:
    """
    Delete a Person.
    """
    person = session.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    if current_user not in person.owners:
        raise HTTPException(
            status_code=403,
            detail="The user isn't owner for this person",
        )
    session.delete(person)
    session.commit()
    return Message(message="Person deleted successfully")


@router.post("/{person_id}")
def follow_person(
    session: SessionDep, current_user: CurrentUser, person_id: uuid.UUID
) -> Message:
    """
    Follow a Person.
    """
    person = session.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    person.followers.append(current_user)
    session.add(person)
    session.commit()
    session.refresh(person)
    return Message(message="Person followed successfully")


@router.post("/{person_id}")
def unfollow_person(
    session: SessionDep, current_user: CurrentUser, person_id: uuid.UUID
) -> Message:
    """
    Unfollow a Person.
    """
    person = session.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    if current_user not in person.followers:
        raise HTTPException(
            status_code=404,
            detail="The user doesn't follow this person",
        )
    person.followers.remove(current_user)
    session.add(person)
    session.commit()
    session.refresh(person)
    return Message(message="Person unfollowed successfully")
