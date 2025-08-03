import os
import requests
from django.conf import settings
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from core.settings import CHUNK_SIZE
from langchain_core.output_parsers import StrOutputParser
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import PromptTemplate
from .models import AnimalList
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FAISS_INDEX_PATH = os.path.join(PROJECT_ROOT, "faiss_index")
LLM_API_URL = getattr(settings, "LLM_API_URL", "http://localhost:1234/v1/chat/completions")
LLM_MODEL = getattr(settings, "LLM_MODEL", "TheBloke/deepseek-llm-7B-chat-GGUF")
LLM_API_KEY = getattr(settings, "LLM_API_KEY", "")
PROMPT_FOLDER = os.path.join(os.path.dirname(__file__), "prompts")


# Module-level variables (loaded once)
_embeddings = None
_vectorstore = None

def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return _embeddings

def get_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        embeddings = get_embeddings()
        _vectorstore = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
    return _vectorstore

def get_relevant_context(query, k=4):
    vectorstore = get_vectorstore()
    docs = vectorstore.similarity_search(query, k=k)
    return "\n\n".join([doc.page_content for doc in docs])

def ingest_all_pdfs(pdf_dir):
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
    
def handle_rag_chat(user_input, prompt_path):
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

def handle_model_native_structured_output(user_input, prompt_path):
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
        explanation_result = full_chain.invoke({"topic": user_input, "context": context})
        return {"result": explanation_result}
    except Exception as e:
        return {"error": f"Error communicating with the model: {e}"}