import os
from django.core.management.base import BaseCommand
from apps.rag_assistant.utils import ingest_all_pdfs

class Command(BaseCommand):
    help = "Ingest all PDFs from the specified directory into the FAISS vectorstore."

    def add_arguments(self, parser):
        parser.add_argument(
            '--pdf_dir',
            type=str,
            default='./apps/rag_assistant/management/commands/resources/pdfs/',
            help='Directory containing PDF files to ingest.'
        )

    def handle(self, *args, **options):
        pdf_dir = options['pdf_dir']
        self.stdout.write(self.style.SUCCESS(f'Ingesting PDFs from {pdf_dir}...'))
        ingest_all_pdfs(pdf_dir)
        self.stdout.write(self.style.SUCCESS('Ingestion complete.'))
