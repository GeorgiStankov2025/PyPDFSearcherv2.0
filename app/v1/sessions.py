from datetime import datetime
from uuid import uuid4, UUID

from fastapi import APIRouter, Depends,Response

from app.schemas import SessionData
from app.session import backend, cookie, verifier

router=APIRouter()

@router.post("/create_session/{name}")
async def create_session(name: str,filename:str, response: Response):

    session = uuid4()
    data = SessionData(username=name,filename=filename,created_at=datetime.now())

    await backend.create(session, data)
    cookie.attach_to_response(response, session)

    return f"created session for {name}"


@router.get("/get_current_session", dependencies=[Depends(cookie)])
async def get_current_session(session_data: SessionData = Depends(verifier)):
    return session_data


@router.post("/delete_session")
async def del_session(response: Response, session_id: UUID = Depends(cookie)):
    await backend.delete(session_id)
    cookie.delete_from_response(response)
    return "deleted session"
