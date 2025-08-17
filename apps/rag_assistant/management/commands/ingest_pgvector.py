import os
from django.core.management.base import BaseCommand
from langchain_postgres import PGEngine, PGVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from django.db import connection
from core.settings import CHUNK_SIZE, DB_CONNECTION_URL, EMBEDDING_MODEL, VECTOR_SIZE

class Command(BaseCommand):
    help = "Ingest all PDFs from the specified directory into the pgvector vectorstore."

    def add_arguments(self, parser):
        parser.add_argument(
            '--collection_name',
            type=str,
            default='rag_docs',
            help='Collection name for pgvector.'
        )
        parser.add_argument(
            '--reinstall-collection',
            type=bool,
            default=True,
            help='Drop and recreate the collection table before ingestion.'
        )

    def handle(self, *args, **options):
        collection_name = options['collection_name']
        reinstall_collection = options['reinstall_collection']
        
        if reinstall_collection:
            self.stdout.write(self.style.WARNING(f'Dropping table and deleting all data for collection "{collection_name}"...'))
            with connection.cursor() as cursor:
                # Drop the collection table
                cursor.execute(f'DROP TABLE IF EXISTS "{collection_name}";')
            self.stdout.write(self.style.WARNING(f'Dropped table and deleted all data for collection \"{collection_name}\".'))

        pdf_dir = './apps/rag_assistant/management/commands/resources/pdfs/'
        self.stdout.write(self.style.SUCCESS(f'Ingesting PDFs from {pdf_dir} into pgvector collection "{collection_name}"...'))

        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        engine = PGEngine.from_connection_string(url=DB_CONNECTION_URL)

        # Ensure the table exists
        engine.init_vectorstore_table(
            table_name=collection_name,
            vector_size=VECTOR_SIZE,
        )

        all_docs = []
        pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
        for pdf_file in pdf_files:
            loader = PyPDFLoader(os.path.join(pdf_dir, pdf_file))
            docs = loader.load()
            all_docs.extend(docs)

        splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=50)
        chunks = splitter.split_documents(all_docs)

        vectorstore = PGVectorStore.create_sync(
            engine=engine,
            table_name=collection_name,
            embedding_service=embeddings,
        )
        vectorstore.add_documents(chunks)
        self.stdout.write(self.style.SUCCESS('Ingestion to pgvector complete.'))
