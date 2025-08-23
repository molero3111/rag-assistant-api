import os
from django.core.management.base import BaseCommand
from apps.rag_assistant.utils import read_txt_file
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from core.settings import GROQ_LLM_MODEL, GROQ_LLM_API_KEY

class Command(BaseCommand):
    help = "Run a Groq LLM chat about a research publication and print responses."

    def handle(self, *args, **options):
        # Initialize the LLM
        llm = ChatGroq(
            model=GROQ_LLM_MODEL,
            temperature=0.7,
            api_key=GROQ_LLM_API_KEY
        )

        publication_content = read_txt_file(os.path.join(
            os.path.dirname(__file__),
            "resources/publications/vaes_publication.txt"
        ))

        if publication_content is None:
            return self.stdout.write(self.style.ERROR(f"Publication file not found"))

        # Initialize conversation
        conversation = [
            SystemMessage(content=f"""
            You are a helpful AI assistant discussing a research publication.
            Base your answers only on this publication content:

            {publication_content}
            """)
        ]

        # User question 1
        conversation.append(HumanMessage(content="""
        What are variational autoencoders and list the top 5 applications for them as discussed in this publication.
        """))

        response1 = llm.invoke(conversation)
        self.stdout.write(self.style.SUCCESS("🤖 AI Response to Question 1:"))
        self.stdout.write(response1.content)
        self.stdout.write("="*50)

        # Add AI's response to conversation history
        conversation.append(AIMessage(content=response1.content))

        # User question 2 (follow-up)
        conversation.append(HumanMessage(content="""
        How does it work in case of anomaly detection?
        """))

        response2 = llm.invoke(conversation)
        self.stdout.write(self.style.SUCCESS("🤖 AI Response to Question 2:"))
        self.stdout.write(response2.content)