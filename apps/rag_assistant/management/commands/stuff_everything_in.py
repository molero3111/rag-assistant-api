import os
from django.core.management.base import BaseCommand
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from pydantic import BaseModel, Field
from tiktoken import get_encoding
from core.settings import GROQ_LLM_MODEL, GROQ_LLM_API_KEY
from apps.rag_assistant.utils import read_txt_file, get_random_turns


class InMemoryHistory(BaseChatMessageHistory, BaseModel):
    messages: list = Field(default_factory=list)
    def add_messages(self, messages):
        self.messages.extend(messages)
    def clear(self):
        self.messages = []

store = {}
def get_by_session_id(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryHistory()
    return store[session_id]

class Command(BaseCommand):
    help = "Demonstrate the 'stuff everything in' memory strategy for VAE publication chat (RunnableWithMessageHistory)."

    def handle(self, *args, **options):
        # Load publication and prompt
        base_dir = os.path.dirname(os.path.dirname(__file__)) + "/commands/"
        publication_path = os.path.join(base_dir, "resources/publications/vaes_publication.txt")
        vaes_prompt_path = os.path.join(base_dir, "../../prompts/vaes_prompt.txt")
        publication_content = read_txt_file(publication_path)
        vaes_prompt = read_txt_file(vaes_prompt_path)
        if not publication_content or not vaes_prompt:
            self.stdout.write(self.style.ERROR("Missing publication or prompt file."))
            return
        system_prompt = vaes_prompt.replace("{publication}", publication_content)

         # Load turns from JSON file and pick 4 random turns
        turns = get_random_turns(4) 

        # Build prompt template with system and history
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ])

        llm = ChatGroq(
            model=GROQ_LLM_MODEL,
            temperature=0.7,
            api_key=GROQ_LLM_API_KEY
        )
        chain = prompt | llm
        chain_with_history = RunnableWithMessageHistory(
            chain,
            get_by_session_id,
            input_messages_key="question",
            history_messages_key="history",
        )
        encoding = get_encoding("cl100k_base")

        session_id = "stuff_everything_in_demo"
        for user_input in turns:
            result = chain_with_history.invoke(
                {"question": user_input},
                config={"configurable": {"session_id": session_id}}
            )
            # Get all messages from history
            all_messages = store[session_id].messages
            all_text = "\n".join([msg.content for msg in all_messages])
            total_tokens = len(encoding.encode(all_text))
            self.stdout.write(self.style.SUCCESS(f"User: {user_input}"))
            self.stdout.write(f"AI Response: {result.content if hasattr(result, 'content') else result}")
            self.stdout.write(f"Total tokens in conversation so far: {total_tokens}")
            self.stdout.write("="*50)
            
