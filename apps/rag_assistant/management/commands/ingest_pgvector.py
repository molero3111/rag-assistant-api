import os
from django.core.management.base import BaseCommand
from langchain_community.vectorstores.pgvector import PGVector
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from core.settings import CHUNK_SIZE, DB_CONNECTION_URL

class Command(BaseCommand):
    help = "Ingest all PDFs from the specified directory into the pgvector vectorstore."

    def add_arguments(self, parser):
        parser.add_argument(
            '--collection_name',
            type=str,
            default='rag_docs',
            help='Collection name for pgvector.'
        )

    def handle(self, *args, **options):
        collection_name = options['collection_name']
        pdf_dir = './apps/rag_assistant/management/commands/resources/pdfs/'
        self.stdout.write(self.style.SUCCESS(f'Ingesting PDFs from {pdf_dir} into pgvector collection "{collection_name}"...'))

        all_docs = []
        pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
        for pdf_file in pdf_files:
            loader = PyPDFLoader(os.path.join(pdf_dir, pdf_file))
            docs = loader.load()
            all_docs.extend(docs)

        splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=50)
        chunks = splitter.split_documents(all_docs)

        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

        # Store in pgvector
        vectorstore = PGVector.from_documents(
            chunks,
            embeddings,
            collection_name=collection_name,
            connection_string=DB_CONNECTION_URL,
        )
        self.stdout.write(self.style.SUCCESS('Ingestion to pgvector complete.'))
