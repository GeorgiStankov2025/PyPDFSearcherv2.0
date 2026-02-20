from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app import emails
from app.v1 import users, prompts
from app.db import create_db_and_tables

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield
app=FastAPI(lifespan=lifespan)
app.include_router(prompts.router)
app.include_router(users.router)
app.include_router(emails.router)

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
