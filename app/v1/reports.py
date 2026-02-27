from fastapi import APIRouter, Depends

from app.agent import invoke_reports_agent
from app.schemas import CreateReport
from app.v1.users import verify_token

router=APIRouter(dependencies=[Depends(verify_token)])

@router.post("/reports",tags=["reports"])
async def create_report(request:CreateReport):
    result=await invoke_reports_agent(request.message)
    return result

