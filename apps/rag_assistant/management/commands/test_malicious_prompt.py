import os
import random
import json
from django.core.management.base import BaseCommand
from apps.rag_assistant.utils import read_txt_file
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from core.settings import GROQ_LLM_MODEL, GROQ_LLM_API_KEY

class Command(BaseCommand):
    help = "Test a random malicious prompt against the VAEs system prompt and publication."

    def handle(self, *args, **options):
        # Paths
        base_dir = os.path.dirname(__file__)
        publication_path = os.path.join(base_dir, "resources/publications/vaes_publication.txt")
        vaes_prompt_path = os.path.join(base_dir, "../../prompts/vaes_prompt.txt")
        malicious_prompts_path = os.path.join(base_dir, "../../prompts/malicious_user_prompts.json")

        # Read files
        publication_content = read_txt_file(publication_path)
        vaes_prompt = read_txt_file(vaes_prompt_path)
        try:
            with open(malicious_prompts_path, "r", encoding="utf-8") as f:
                malicious_prompts = json.load(f)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error reading malicious prompts: {e}"))
            return

        if not publication_content or not vaes_prompt or not malicious_prompts:
            self.stdout.write(self.style.ERROR("Missing required files or content."))
            return

        # Pick a random malicious prompt
        user_prompt = random.choice(malicious_prompts)
        self.stdout.write(self.style.WARNING(f"Testing malicious prompt: {user_prompt}"))

        # Format system prompt
        system_prompt = vaes_prompt.replace("{publication}", publication_content)

        # Build conversation
        conversation = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        # Run LLM
        llm = ChatGroq(
            model=GROQ_LLM_MODEL,
            temperature=0.7,
            api_key=GROQ_LLM_API_KEY
        )
        response = llm.invoke(conversation)
        self.stdout.write(self.style.SUCCESS("🤖 AI Response:"))
        self.stdout.write(response.content)
