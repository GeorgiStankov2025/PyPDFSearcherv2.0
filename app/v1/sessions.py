from datetime import datetime
from typing import Dict, Optional, Any
from uuid import uuid4, UUID

from fastapi import APIRouter, Depends, Response, HTTPException,Request

from app.schemas import SessionData
from app.session import backend, cookie, get_metadata
router=APIRouter()

@router.post("/set-metadata")
async def set_metadata(response: Response, metadata: SessionData):
    """
    Set metadata cookie.
    """
    response.set_cookie(
        key="metadata",
        value=metadata.model_dump_json(),
        httponly=True,  # JavaScript cannot access
        secure=True,  # HTTPS only
        samesite="strict",  # CSRF protection
        max_age=7 * 24 * 60 * 60  # 7 days
    )

    return {
        "message": "Metadata cookie set",
        "metadata": metadata
    }


# ============================================
# GET METADATA FROM COOKIE
# ============================================


@router.get("/api/metadata", response_model=SessionData)
async def get_user_metadata(request: Request):

    metadata=get_metadata(request)
    """
    Get user metadata from cookie.
    """
    if not metadata:
        raise HTTPException(
            status_code=400,
            detail="No metadata cookie found"
        )

    return SessionData(**metadata)

# ============================================
# UPDATE THEME IN COOKIE
# ============================================