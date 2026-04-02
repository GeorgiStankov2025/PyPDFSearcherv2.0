from fastapi import Request,Response
from app.agent import invoke_reports_agent
from app.schemas import CreateReport, SessionData

async def create_report(request:CreateReport,response: Response,username:str,conversation_id:str):

    result=await invoke_reports_agent(request.message,username,conversation_id,response)
    document_content=result['messages'][-1].content[0].get('text', '').replace("*","")
    return document_content
