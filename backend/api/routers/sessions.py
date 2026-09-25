from fastapi import APIRouter, Depends

from backend.api.dependencies import (
    get_application,
    get_current_user,
)

from backend.api.schemas.session import (
    SessionResponse,
)

router = APIRouter(
    prefix="/sessions",
    tags=["Sessions"],
)


@router.post(
    "",
    response_model=SessionResponse,
)
def create_session(
    application=Depends(get_application),
    current_user=Depends(get_current_user),
):

    session_id = (
        application.assistant_service.create_session()
    )

    return SessionResponse(
        session_id=session_id
    )