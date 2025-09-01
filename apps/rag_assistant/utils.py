import os
import requests
from json import load, JSONDecodeError
from random import sample
from langchain_community.vectorstores import FAISS
from langchain_postgres import PGEngine, PGVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.output_parsers import StrOutputParser
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_deepseek import ChatDeepSeek
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage


from core.settings import (CHUNK_SIZE, VECTORSTORE_BACKEND, PGVECTOR_COLLECTION_NAME,
DB_CONNECTION_URL, EMBEDDING_MODEL, LLM_API_URL, LLM_MODEL, LLM_API_KEY, GROQ_LLM_MODEL, GROQ_LLM_API_KEY)
from .models import AnimalList
import logging
logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FAISS_INDEX_PATH = os.path.join(PROJECT_ROOT, "faiss_index")
PROMPT_FOLDER = os.path.join(os.path.dirname(__file__), "prompts")

# Module-level variables (loaded once)
_embeddings = None
_vectorstore = None
_pgvectorstore = None
_pgengine = None


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return _embeddings

def get_vectorstore():
    global _vectorstore, _pgvectorstore
    embeddings = get_embeddings()
    if VECTORSTORE_BACKEND == "faiss":
        print("[RAG] Using FAISS vectorstore backend.")
        if _vectorstore is None:
            _vectorstore = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
        return _vectorstore
    elif VECTORSTORE_BACKEND == "pgvector":
        print(f"[RAG] Using pgvector backend (PGVectorStore). Collection: {PGVECTOR_COLLECTION_NAME}")
        global _pgengine
        if not DB_CONNECTION_URL:
            raise ValueError("DB_CONNECTION_URL must be set in settings for pgvector backend.")
        if _pgengine is None:
            _pgengine = PGEngine.from_connection_string(url=DB_CONNECTION_URL)
        if _pgvectorstore is None:
            _pgvectorstore = PGVectorStore.create_sync(
                engine=_pgengine,
                table_name=PGVECTOR_COLLECTION_NAME,
                embedding_service=embeddings,
            )
        return _pgvectorstore
    else:
        print(f"[RAG] Unknown VECTORSTORE_BACKEND: {VECTORSTORE_BACKEND}")
        raise ValueError(f"Unknown VECTORSTORE_BACKEND: {VECTORSTORE_BACKEND}")

def get_relevant_context(query: str, k: int = 4):
    vectorstore = get_vectorstore()
    docs = vectorstore.similarity_search(query, k=k)
    return "\n\n".join([doc.page_content for doc in docs])

def ingest_all_pdfs(pdf_dir: str):
    all_docs = []
    pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
    for pdf_file in pdf_files:
        loader = PyPDFLoader(os.path.join(pdf_dir, pdf_file))
        docs = loader.load()
        all_docs.extend(docs)
    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=50)
    chunks = splitter.split_documents(all_docs)
    # Embed chunks
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    # Store in FAISS
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(FAISS_INDEX_PATH)

def handle_rag_chat(user_input: str, prompt_path: str):
    if not user_input:
        return {"error": "Prompt is required."}
    context = get_relevant_context(user_input)
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_template = f.read()
    prompt_content = prompt_template.format(context=context, user_input=user_input)
    messages = [
        {"role": "user", "content": prompt_content}
    ]
    headers = {"Content-Type": "application/json"}
    if LLM_API_KEY:
        headers["Authorization"] = f"Bearer {LLM_API_KEY}"
    payload = {
        "model": LLM_MODEL,
        "messages": messages
    }
    try:
        response = requests.post(LLM_API_URL, headers=headers, json=payload, timeout=600)
        response.raise_for_status()
        data = response.json()
        return {"response": data["choices"][0]["message"]["content"].strip()}
    except Exception as e:
        return {"error": f"Error communicating with the model: {e}"}

def handle_model_native_structured_output(user_input: str, prompt_path: str):
    if not user_input:
        return {"error": "Prompt is required."}
    context = get_relevant_context(user_input)
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_template = f.read()
    prompt = ChatPromptTemplate.from_template(prompt_template)
    model = ChatDeepSeek(model=LLM_MODEL, temperature=0, api_key=LLM_API_KEY)
    chain = prompt | model.with_structured_output(AnimalList)
    try:
        result = chain.invoke({"context": context, "user_input": user_input})
        return result.model_dump()
    except Exception as e:
        return {"error": f"Error communicating with the model: {e}"}

# Handler for chained facts and elaboration
def handle_facts_and_explanations(user_input):
    logger.info("Generating facts and explanations for topic: %s", user_input)
    context = get_relevant_context(user_input)
    # First prompt: generate 3 short facts
    facts_prompt = PromptTemplate(
        input_variables=["topic", "context"],
        template="Using the following context, generate three important short facts (titles only, no explanations) about {topic}:\nContext: {context}",
    )
    # Second prompt: elaborate on each fact
    explanation_prompt = PromptTemplate(
        input_variables=["facts", "context"],
        template="Using the following context, provide a brief explanation for each fact below.\nContext: {context}\nFacts: {facts}",
    )
    model = ChatDeepSeek(model=LLM_MODEL, temperature=0, api_key=LLM_API_KEY)
    output_parser = StrOutputParser()
    # Chain 1: Generate facts
    facts_chain = facts_prompt | model | output_parser
    # Chain 2: Elaborate on facts
    explanation_chain = explanation_prompt | model | output_parser
    def create_explanation_input(facts):
        new_context = get_relevant_context(facts)
        return {"facts": facts, "context": new_context}
    # Full chain: facts -> explanation
    full_chain = facts_chain | create_explanation_input | explanation_chain
    try:
        logger.info("Facts chain input: topic=%s, context=%s", user_input, context)
        explanation_result = full_chain.invoke({"topic": user_input, "context": context})
        return {"result": explanation_result}
    except Exception as e:
        logger.error("Error occurred: %s", e)
        return {"error": f"Error communicating with the model: {e}"}

def handle_rag_chat_with_groq(user_input: str):
    if not user_input:
        return {"error": "Prompt is required."}
    # context = get_relevant_context(user_input)
    # with open(prompt_path, "r", encoding="utf-8") as f:
    #     prompt_template = f.read()
    # prompt_content = prompt_template.format(context=context, user_input=user_input)
    # Basic question
    messages = [
        SystemMessage(content="You are a helpful AI assistant."),
        HumanMessage(content=user_input)
    ]
    llm = ChatGroq(
        model=GROQ_LLM_MODEL,
        temperature=0.7,
        api_key=GROQ_LLM_API_KEY
    )

    response = llm.invoke(messages)
    return response.content



def read_txt_file(file_path: str):
    """
    Reads the content of a text file and returns it as a string.
    If the file is not found, returns None.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None

def load_json_file(file_path: str):
    """
    Loads and returns the contents of a JSON file as a Python object.
    Returns None if the file is not found or cannot be parsed.
    """
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return load(f)
    except (FileNotFoundError, JSONDecodeError):
        return None

def get_random_turns(n: int = 4, turns: list[str] = None):
    """
    Returns a random sample of turns from the provided list.
    """
    if turns is None:
        turns = load_json_file(os.path.join(os.path.dirname(__file__), "management/commands/resources/turns.json"))
        if not turns:
            raise RuntimeError("Failed to load turns")
    return sample(turns, n) if turns else None