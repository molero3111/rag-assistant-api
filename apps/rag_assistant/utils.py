import os
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

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
        _vectorstore = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
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
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(all_docs)
    # Embed chunks
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    # Store in FAISS
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local("faiss_index")
