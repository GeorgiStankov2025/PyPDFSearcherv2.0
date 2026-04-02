from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from starlette.middleware.sessions import SessionMiddleware
from app import emails, report_requests, files
from app.agent import report_agent_setup, close_pool
from app.v1 import users, admin, conversations
from app.db import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    await report_agent_setup()
    yield
    await close_pool()
app=FastAPI(lifespan=lifespan)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(conversations.router)

app.add_middleware(SessionMiddleware, secret_key='THE_BIG_SECRET')

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="PyPDFSearcher",
        version="1.0.0",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    openapi_schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__=="__main__":

    uvicorn.run("main:app",host="127.0.0.1",port=5000,reload=True)
