import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import (
    CurrentUser,
    SessionDep,
)
from app.models import (
    EventPublic,
    Inviteation,
)

router = APIRouter(prefix="/invites", tags=["invites", "events"])


@router.patch(
    "/{invite_id}",
    response_model=EventPublic,
)
def use_invite(
    *, session: SessionDep, invite_id: uuid.UUID, current_user: CurrentUser
) -> Any:
    """
    Use invite.
    """
    invite = session.get(Inviteation, invite_id)
    if not invite:
        raise HTTPException(
            status_code=404,
            detail="The invite with this id does not exist in the system",
        )
    if invite.expire_time > datetime.now():
        raise HTTPException(status_code=403, detail="This invite was expired")

    if not invite.event:
        raise HTTPException(
            status_code=404,
            detail="The event with this id does not exist in the system",
        )
    invite.event.invited_users.append(current_user)
    session.add(invite)
    session.add(invite.event)
    session.commit()
    session.refresh(invite.event)
    return invite.event
