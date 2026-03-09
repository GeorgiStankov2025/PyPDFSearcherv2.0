import asyncio
import re
import selectors
import uuid

from asyncstdlib import await_each
from fastapi.params import Depends
from langchain.agents import create_agent
from langchain_text_splitters import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
import os
from langchain_community.document_loaders import PyPDFDirectoryLoader, TextLoader
from langchain_core.tools import tool, InjectedToolCallId
from langchain_qdrant import QdrantVectorStore
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres import PostgresSaver
import requests
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
from pygments.lexer import default
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.v1.users import get_current_user

open_api_key=os.getenv("OPENAI_API_KEY")

embeddings=OpenAIEmbeddings(api_key=open_api_key,model="text-embedding-3-small")
"""
pdf_loader = PyPDFDirectoryLoader(path=r"path to folder")
raw_documents = pdf_loader.load()

text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
split_documents = text_splitter.transform_documents(raw_documents)

db = QdrantVectorStore.from_documents(documents=list(split_documents), embedding=embeddings, url="http://localhost:6333",
                                              collection_name="scotty-collection")"""

db=QdrantVectorStore.from_existing_collection(collection_name="scotty-collection",embedding=embeddings)

from langchain_openai import OpenAI

gpt_llm = OpenAI(model="gpt-4.1-nano", api_key=open_api_key, temperature=0)
gemini_llm=ChatGoogleGenerativeAI(model="gemini-2.0-flash",max_retries=6,
    stop=["\n\n"])

spare_symbols=[

    '\n',
    '@',
    '#',
    '*'

]


@tool
async def similarity_search(query: str) -> str:
     """Performs a similarity search based on user query."""
     results = await db.asimilarity_search(query)
     return "\n\n".join([r.page_content for r in results])

chat_agent = create_agent(tools=[similarity_search], model="gpt-4.1-nano",system_prompt=("ROLE: Technical Document Specialist. STATUS: Grounded Retrieval Mode (2026). "
                                                                                    "INSTRUCTIONS: "
                                                                                    "1. ALWAYS start by calling 'similarity_search' with the user's intent."
                                                                                    "2. USE ONLY the retrieved context to answer. You are forbidden from using external CPU/Hardware knowledge."
                                                                                    "3. FLEXIBILITY: You may interpret technical synonyms (e.g., if the text says 'draws 65W' and the user asks for 'TDP', you may connect them). "
                                                                                    "4. REASONING: If the data is present but spread across multiple chunks, synthesize them into a clear answer."
                                                                                    "5. HARD STOP: If the retrieved text does not contain the specific numerical values or facts requested, state: 'Requested technical data not found in provided documentation'."
                                                                                    "CRITICAL: Do not mention your internal training data. If it isn't in the tool results, it doesn't exist."))

async def invoke_chat_agent(query):

    inputs = {"messages": [("user", query)]}
    response=await chat_agent.ainvoke(inputs)
    return response["messages"][-1].content

reports_agent=None
_pool=None

async def report_agent_setup():

    global reports_agent
    global _pool
    _pool=AsyncConnectionPool(conninfo="postgresql://postgres:Bit_2024@localhost/pypdfsearcherdb",max_size=10)
    await _pool.open()
    await _pool.wait()
    checkpointer=AsyncPostgresSaver(_pool)
    await checkpointer.setup()
    reports_agent = create_agent(
            tools=[similarity_search],
            model="gemini-2.5-flash",
            system_prompt="You are a strict Data Analysis Agent. Your sole purpose is to generate reports based on information retrieved from a vector database. "
                          "CORE OPERATIONAL RULES: "
                          "1. MANDATORY TOOL USE: You must call the `similarity_search` tool for every request. You are not permitted to answer without first performing a search. "
                          "2. SOURCE LIMITATION: Your output must be based EXCLUSIVELY on the data returned by the `similarity_search` tool. "
                          "3. KNOWLEDGE CUTOFF: You must ignore all of your internal training data, general knowledge, and external facts. If a fact is not explicitly stated in the retrieved documents, it does not exist for the purpose of this report. "
                          "4. STATE MANAGEMENT & EDITING: If a user requests a modification to a previously generated report, you must: "
                          "Access the last saved state from the Checkpointer. "
                          "Treat the Checkpointer data as 'Primary Truth', secondary only to new similarity_search results. "
                          "Clearly output the revised version, highlighting only the changes requested while maintaining the original data's integrity."
                          "5. INSUFFICIENT DATA PROTOCOL: If the retrieved documents do not contain the specific information required to answer the prompt, or if the search returns no results, you must state exactly: 'I cannot fulfill this request because the required information is not present in the database.' Do not attempt to fill in gaps with your own logic or assumptions. "
                          "6. NO HALLUCINATION: Do not infer, speculate, or provide 'likely' scenarios. Stick to the literal text provided in the search results."
                          "- Title your report based on the user's input. SEPARATE the content on a new line"
                          "- Use bullet points for clarity."
                          "- Only include information found in the search results.",
            checkpointer=checkpointer,
    )

async def close_pool():
    global _pool
    if _pool:
        await _pool.close()

loop_factory = lambda: asyncio.SelectorEventLoop(selectors.SelectSelector())
asyncio.run(report_agent_setup(),loop_factory=loop_factory)

async def invoke_reports_agent(query,username:str):
    inputs = {"messages": [("user", query)]}
    config={"configurable": {"thread_id":f"{username}"}}
    result=await reports_agent.ainvoke(inputs,config)
    return result