import os
from uuid import uuid4
from typing import List, Any

from django.core.management.base import BaseCommand

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq

from langmem.short_term import summarize_messages, RunningSummary
from langchain_core.messages.utils import count_tokens_approximately

from tiktoken import get_encoding
from core.settings import (GROQ_LLM_MODEL, GROQ_LLM_API_KEY, SUMMARIZER_MAX_TOKENS, 
SUMMARIZER_MAX_SUMMARY_TOKENS, SUMMARIZER_MAX_TOKENS_BEFORE_SUMMARY)
from apps.rag_assistant.utils import read_txt_file, get_random_turns

def make_human_message(text: str) -> Any:
    """Try to create a HumanMessage with an id; if constructor doesn't accept id, fall back to dict."""
    try:
        return HumanMessage(content=text, id=str(uuid4()))
    except TypeError:
        return {"id": str(uuid4()), "type": "human", "content": text}

def make_ai_message(text: str) -> Any:
    """Try to create an AIMessage with an id; if not possible, fall back to dict."""
    try:
        return AIMessage(content=text, id=str(uuid4()))
    except TypeError:
        return {"id": str(uuid4()), "type": "ai", "content": text}


class Command(BaseCommand):
    help = "Summarize conversation each turn and invoke LLM with reduced history (ensuring messages have id fields)."

    def handle(self, *args, **options):
        # Load prompt/publication
        base_dir = os.path.dirname(os.path.dirname(__file__)) + "/commands/"
        publication_path = os.path.join(base_dir, "resources/publications/vaes_publication.txt")
        vaes_prompt_path = os.path.join(base_dir, "../../prompts/vaes_prompt.txt")
        publication_content = read_txt_file(publication_path)
        vaes_prompt = read_txt_file(vaes_prompt_path)
        if not publication_content or not vaes_prompt:
            self.stdout.write(self.style.ERROR("Missing publication or prompt file."))
            return

        system_prompt = vaes_prompt.replace("{publication}", publication_content)
        turns = get_random_turns(4)

        # Chat prompt template expects a "history" placeholder (list of messages)
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

        # Raw session messages (list of messages with ids). We keep them as "Any" because we may fallback to dicts.
        session_messages: List[Any] = []

        # RunningSummary to inspect the human-readable summary paragraph
        running_summary = RunningSummary(summary="", summarized_message_ids=[], last_summarized_message_id=None)

        encoding = get_encoding("cl100k_base")

        for user_input in turns:
            # 1) Append user message with an id
            user_msg = make_human_message(user_input)
            session_messages.append(user_msg)

            # 2) Summarize the current session messages
            try:
                summary_result = summarize_messages(
                    session_messages,
                    running_summary=running_summary,
                    model=llm,
                    max_tokens=SUMMARIZER_MAX_TOKENS,
                    max_summary_tokens=SUMMARIZER_MAX_SUMMARY_TOKENS,
                    max_tokens_before_summary=SUMMARIZER_MAX_TOKENS_BEFORE_SUMMARY,
                    token_counter=count_tokens_approximately,
                )
            except Exception as e:
                # Helpful debug output if summarizer still complains
                self.stdout.write(self.style.ERROR(f"Summarization failed: {e}"))
                # Save best-effort summary and continue
                summary_result = None

            if summary_result:
                running_summary = summary_result.running_summary
                llm_input_messages = summary_result.messages  # trimmed/annotated messages for the LLM
                self.stdout.write(self.style.NOTICE(f"[DEBUG] Summarization done. Total messages now: {len(llm_input_messages)}"))
            else:
                # Fallback: use last N messages as raw history (but keep ids)
                llm_input_messages = session_messages[-10:]  # cheap fallback

            # 3) Invoke chain with reduced history. ChatPromptTemplate expects "history" key.
            ai_text = ""
            try:
                # Provide both question and history explicitly
                result = chain.invoke({"question": user_input, "history": llm_input_messages})
                ai_text = result.content if hasattr(result, "content") else str(result)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"LLM invoke failed: {e}"))
                ai_text = f"<LLM_ERROR: {e}>"
                

            # 4) Persist AI response (with id) back into raw session_messages
            ai_msg = make_ai_message(ai_text)
            session_messages.append(ai_msg)

            summary_string = "\n".join(str(getattr(msg, "content", "")) for msg in llm_input_messages)
            total_tokens = len(encoding.encode(summary_string))

            self.stdout.write(f"User input: {user_input}")
            self.stdout.write(self.style.WARNING(f"\n{summary_string}\n"))
            self.stdout.write(self.style.WARNING(f"Total tokens in summary: {total_tokens}"))
            self.stdout.write(self.style.SUCCESS(f"AI Response: {ai_text}"))
            self.stdout.write(self.style.NOTICE("=" * 100))
