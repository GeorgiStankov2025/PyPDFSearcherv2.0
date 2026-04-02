import asyncio
import selectors
from fastapi import Depends, APIRouter,Response
from langchain.agents import create_agent
from langchain_openai import OpenAIEmbeddings
import os
from langchain_core.tools import tool
from langchain_qdrant import QdrantVectorStore
from langchain_google_genai import ChatGoogleGenerativeAI
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app import thread_variables

router=APIRouter()

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

reports_agent=None
_pool=None

async def report_agent_setup():

    global reports_agent
    global _pool
    _pool=AsyncConnectionPool(conninfo="postgresql://postgres:Bit_2024@localhost/pypdfsearcherdb",max_size=10,kwargs={"autocommit": True}, # Essential for the migration setup
        open=False)
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



async def invoke_reports_agent(query,username:str,conversation_id:str,response: Response):
    #cookie_data=await get_user_metadata(state_request)
    inputs = {"messages": [("user", query)]}

    if thread_variables.topic != "" and username in thread_variables.topic and conversation_id in thread_variables.topic:
        config = {"configurable": {"thread_id": f"{thread_variables.topic}"}}
    else:
        config = {"configurable": {"thread_id": f"{username+"+"+conversation_id}"}}
        thread_variables.topic =f"{username+"+"+conversation_id}"

    result=await reports_agent.ainvoke(inputs,config)
    return result