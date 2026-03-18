from typing import Optional, Dict, Any
from uuid import UUID

from fastapi import HTTPException,Request
from fastapi_sessions.backends.implementations import InMemoryBackend
from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters
from fastapi_sessions.session_verifier import SessionVerifier
import json

from app.schemas import SessionData

cookie_params=CookieParameters()

cookie=SessionCookie(

    cookie_name="report_cookie",
    identifier="general_verifier",
    auto_error=False,
    secret_key='THE_BIG_SECRET',
    cookie_params=cookie_params,

)

backend=InMemoryBackend[UUID,SessionData]()


def get_metadata(request: Request) -> Optional[Dict[str, Any]]:
    """
    Extract and parse metadata from cookie.
    Returns None if cookie doesn't exist.
    """
    metadata_cookie = request.cookies.get("metadata")

    if not metadata_cookie:
        return None

    try:
        metadata = json.loads(metadata_cookie)
        return metadata
    except json.JSONDecodeError:
        return None