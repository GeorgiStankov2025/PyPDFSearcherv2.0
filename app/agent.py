from langchain.agents import create_agent
from langchain_text_splitters import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
import os
from langchain_community.document_loaders import PyPDFDirectoryLoader, TextLoader
from langchain_core.tools import tool, InjectedToolCallId
from langchain_qdrant import QdrantVectorStore

open_api_key=os.getenv("OPENAI_API_KEY")

embeddings=OpenAIEmbeddings(api_key=open_api_key)

pdf_loader = PyPDFDirectoryLoader(path=r"E:\специални предмети\ОКС - 10д-20220918T114024Z-001\ОКС - 10д")
raw_documents = pdf_loader.load()

text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
split_documents = text_splitter.transform_documents(raw_documents)

db = QdrantVectorStore.from_documents(documents=list(split_documents), embedding=embeddings, url="http://localhost:6333",
                                                             collection_name="my-collection")
from langchain_openai import OpenAI

llm = OpenAI(model="gpt-4.1-nano", api_key=open_api_key, temperature=0)


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

async def invoke_agent(query):

    inputs = {"messages": [("user", query)]}
    response=await chat_agent.ainvoke(inputs)
    return response["messages"][-1].content

