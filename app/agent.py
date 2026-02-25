import operator
import uuid
from fastapi import HTTPException
from typing import Annotated, TypedDict, List
from uuid import UUID
from langchain.agents import create_agent
from langchain_core.messages import ToolMessage
from langchain_experimental.graph_transformers.llm import system_prompt
from langchain_text_splitters import CharacterTextSplitter
from langgraph.types import Command
from langchain_openai import OpenAIEmbeddings
import os
from langchain_community.document_loaders import PyPDFDirectoryLoader, TextLoader
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_async_session, User
from langchain_core.tools import tool, InjectedToolCallId
from langchain_qdrant import QdrantVectorStore
from fastapi import Request
from app.db import Prompt
from app.schemas import PromptCreate
from app.v1.users import verify_token
from app.v1.users import get_current_user


def initialize_agent():

            open_api_key=os.getenv("OPENAI_API_KEY")

            embeddings=OpenAIEmbeddings(api_key=open_api_key)

            pdf_loader = PyPDFDirectoryLoader(path=r"E:\специални предмети\ОКС - 10д-20220918T114024Z-001\ОКС - 10д")
            raw_documents = pdf_loader.load()

            text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
            split_documents = text_splitter.transform_documents(raw_documents)

            db = QdrantVectorStore.from_documents(documents=split_documents, embedding=embeddings, url="http://localhost:6333",
                                                             collection_name="my-collection")
            from langchain_openai import OpenAI

            llm = OpenAI(model="gpt-4.1-nano", api_key=open_api_key, temperature=0)

            @tool
            async def similarity_search(query: str) -> str:
                """Performs a similarity search based on user query."""
                results = await db.asimilarity_search(query)
                return "\n\n".join([r.page_content for r in results])

            agent = create_agent(tools=[similarity_search], model="gpt-4.1-nano")

            return agent


async def invoke_agent(query:str,agent):
    agent.system_prompt=("You are a strict Technical File Assistant. You have NO internal knowledge of hardware, "
    "CPU specs, or technical data. You MUST follow this exact execution flow for every request: \n"
    f"1. Call similarity_search' with the user's query: {query}. \n\n"
    "CRITICAL: Base your final answer ONLY on the text returned by the tools. "
    "DO NOT supplement answers with your own training data or general knowledge. Output only the final technical answer from the documents.")
    response = await agent.ainvoke(input=query)
    return response