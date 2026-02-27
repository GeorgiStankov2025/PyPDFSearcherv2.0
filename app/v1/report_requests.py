import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent import invoke_reports_agent
from app.db import get_async_session, ReportRequest
from app.schemas import CreateReport
from app.v1.users import verify_token

router=APIRouter(dependencies=[Depends(verify_token)])

@router.post("/report_requests",tags=["report_requests"])
async def create_report(request:CreateReport):
    result=await invoke_reports_agent(request.message)
    return result

@router.get("/report_requests",tags=["report_requests"])
async def get_all_report_requests(session:AsyncSession=Depends(get_async_session)):
    result=await session.execute(select(ReportRequest).order_by(ReportRequest.created_at.desc()))
    return [row[0] for row in result.all()]

@router.get("/report_requests/{id}",tags=["report_requests"])
async def get_all_report_requests(id:str,session:AsyncSession=Depends(get_async_session)):

    try:
        id_uuid=uuid.UUID(id)
        request_search=await session.execute(select(ReportRequest).where(ReportRequest.id == id_uuid))
        report_request=request_search.scalars().first()
        if report_request is None:
            raise HTTPException(status_code=404, detail="Report request not found")
        return report_request
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/report_requests/{id}",tags=["report_requests"])
async def delete_report_request(id:str,session:AsyncSession=Depends(get_async_session)):
    try:
        id_uuid=uuid.UUID(id)
        request_search=await session.execute(select(ReportRequest).where(ReportRequest.id == id_uuid))
        report_request=request_search.scalars().first()
        if report_request is None:
            raise HTTPException(status_code=404, detail="Report request not found")
        await session.execute(delete(ReportRequest).where(ReportRequest.id == id_uuid))
        await session.commit()
        return {"message":"Report request deleted successfully"}
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))