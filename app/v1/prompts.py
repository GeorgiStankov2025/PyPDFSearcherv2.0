# %%
import operator
from typing import Annotated, TypedDict, List

from fastapi import APIRouter,Depends
from langchain_experimental.graph_transformers.llm import system_prompt
from langgraph.types import Command
from langchain_openai import OpenAIEmbeddings
import os
from langchain_community.document_loaders import PyPDFDirectoryLoader, TextLoader
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_async_session
from langchain_core.tools import tool, InjectedToolCallId
from langchain_qdrant import QdrantVectorStore

from app.db import Prompt
from app.schemas import PromptCreate
from app.v1.users import verify_token

router=APIRouter(dependencies=[Depends(verify_token)])
@router.post("/prompts",tags=["prompts"])
async def create_prompt(request:PromptCreate,session:AsyncSession=Depends(get_async_session)):

    class AgentState(TypedDict):
        messages: Annotated[list, operator.add]
        documents: List

    open_api_key=os.getenv("OPENAI_API_KEY")

    embeddings=OpenAIEmbeddings(api_key=open_api_key)

    @tool
    async def load_pdfs(tool_call_id: Annotated[str, InjectedToolCallId])->Command:
        """A tool allowing access to a directory of PDF files"""
        pdf_loader=PyPDFDirectoryLoader(path=r"E:\специални предмети\ОКС - 10д-20220918T114024Z-001\ОКС - 10д")
        raw_documents=await pdf_loader.aload()
        return Command(
            update={"documents": raw_documents,
            "messages": [
                    ToolMessage(
                        content=f"Successfully loaded documents.",
                        tool_call_id=tool_call_id
                    )
                ]
            }
        )
    # %%
    from langgraph.prebuilt import InjectedState
    from langchain_core.messages import ToolMessage
    from langchain_text_splitters import CharacterTextSplitter

    @tool
    async def text_splitting(tool_call_id: Annotated[str, InjectedToolCallId],state: Annotated[dict, InjectedState]):
        """A tool allowing you to perform text splitting on PDF files, loaded with the load_pdf_documents tool"""
        raw_docs = state.get("documents", [])
        text_splitter=CharacterTextSplitter(chunk_size=1000,chunk_overlap=0)
        split_documents=await text_splitter.atransform_documents(raw_docs)
        return Command(

            update={"documents": split_documents,
            "messages": [
                    ToolMessage(
                        content=f"Successfully split documents.",
                        tool_call_id=tool_call_id
                    )
                ]
            }

        )

    # %%
    @tool
    async def convert_to_vectorstore_data_and_similarity_search(query:str,state: Annotated[dict, InjectedState])->str:
        """Converts documents loaded with load_pdf_documents and split by text_splitting tool to a vector store. Then it performs a similarity search based on user query. If text is not split return to text_splitting tool."""
        docs=state.get("documents", [])
        db=await QdrantVectorStore.afrom_documents(documents=docs,embedding=embeddings,url="http://localhost:6333",collection_name="my-collection")
        results=await db.asimilarity_search(query)
        return "\n\n".join([r.page_content for r in results])
    # %%
    from langchain_openai import OpenAI

    llm=OpenAI(model="gpt-4.1-nano",api_key=open_api_key, temperature=0)
    # %%
    from langchain.agents import create_agent
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.prebuilt import create_react_agent

    query = {"messages": [("user", request.message)]}

    agent = create_agent(tools=[load_pdfs, text_splitting,convert_to_vectorstore_data_and_similarity_search],model="gpt-4.1-nano",
        system_prompt="You are a strict Technical File Assistant. You have NO internal knowledge of hardware, "
    "CPU specs, or technical data. You MUST follow this exact execution flow for every request: \n"
    "1. Call 'load_pdfs' to access the directory. \n"
    "2. Call 'text_splitting' to process the loaded documents. \n"
    f"3. Call 'convert_to_vectorstore_data_and_similarity_search' with the user's query: {query}. \n\n"
    "CRITICAL: Base your final answer ONLY on the text returned by the tools. "
    "DO NOT supplement answers with your own training data or general knowledge. Output only the final technical answer from the documents.")

    response=await agent.ainvoke(input=query)

    prompt=Prompt(

        message=request.message,
        response=response["messages"][-1].content,

    )
    session.add(prompt)
    await session.commit()
    await session.refresh(prompt)
    return prompt