from datetime import datetime
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.params import Depends
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.agent import invoke_reports_agent
from app.db import get_async_session, ReportRequest, User
from app.schemas import CreateReport
from app.v1.files import download_file
from app.v1.users import verify_token, get_current_user
from docx import Document
router=APIRouter(dependencies=[Depends(verify_token)])

@router.post("/report_requests",tags=["report_requests"])
async def create_report(request:CreateReport,session:AsyncSession=Depends(get_async_session),current_user:dict=Depends(get_current_user)):


    #user_search=await session.execute(select(User).where(User.username == current_user["username"]))
    #user=user_search.scalars().first()

    username=current_user["username"]

    result=await invoke_reports_agent(request.message,username)
    document_content=result['messages'][-1].content[0].get('text', '').replace("*","")
    if 'I cannot fulfill this request' in document_content:
        return {"message":"I cannot fulfill this request because the required information is not present in the database. Try to be more specific or choose a different topic."}
    else:

        document_content = document_content.replace("##", "")
        document_title=document_content.splitlines()[0]
        document=Document()
        document.add_heading(document_title,level=1)
        document.add_heading(f"Author:{current_user['username']}",level=2)
        document.add_paragraph(document_content)
        document.save(rf"D:\ПУ\II курс\Python\PyPDFSearcher\generated_reports\{document_title}.docx")
        return await download_file(document_title+".docx")


"""
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
async def delete_report_request(id:str,session:AsyncSession=Depends(get_async_session),current_user:dict=Depends(get_current_user)):
    try:
        user_search=await session.execute(select(User).where(User.username == current_user["username"]))
        user=user_search.scalars().first()
        id_uuid=uuid.UUID(id)
        request_search=await session.execute(select(ReportRequest).where(ReportRequest.id == id_uuid))
        report_request=request_search.scalars().first()
        if user.id!=report_request.user_id:
            raise HTTPException(status_code=403,detail="You are not authorized to perform this action.")
        if report_request is None:
            raise HTTPException(status_code=404, detail="Report request not found")
        await session.execute(delete(ReportRequest).where(ReportRequest.id == id_uuid))
        await session.commit()
        return {"message":"Report request deleted successfully"}
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
"""