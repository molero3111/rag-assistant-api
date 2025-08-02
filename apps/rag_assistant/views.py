from django.shortcuts import render
from .utils import get_relevant_context
from django.conf import settings
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
import os


# LangChain and model import for structured output
from .models import AnimalList
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate

LLM_API_URL = getattr(settings, "LLM_API_URL", "http://localhost:1234/v1/chat/completions")
LLM_MODEL = getattr(settings, "LLM_MODEL", "mistralai/mathstral-7b-v0.1")
LLM_API_KEY = getattr(settings, "LLM_API_KEY", "")
PROMPT_FOLDER = os.path.join(os.path.dirname(__file__), "prompts")

def handle_rag_chat(user_input, prompt_path):
    if not user_input:
        return Response({'error': 'Prompt is required.'}, status=status.HTTP_400_BAD_REQUEST)
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
        return Response({"response": data["choices"][0]["message"]["content"].strip()})
    except Exception as e:
        return Response({"error": f"Error communicating with the model: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Handler for model-native structured output
def handle_model_native_structured_output(user_input, prompt_path):
    if not user_input:
        return Response({'error': 'Prompt is required.'}, status=status.HTTP_400_BAD_REQUEST)
    context = get_relevant_context(user_input)
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_template = f.read()
    prompt = ChatPromptTemplate.from_template(prompt_template)
    # Use ChatDeepSeek for DeepSeek models
    model = ChatDeepSeek(model=LLM_MODEL, temperature=0, api_key=LLM_API_KEY)
    chain = prompt | model.with_structured_output(AnimalList)
    try:
        result = chain.invoke({"context": context, "user_input": user_input})
        return Response(result.model_dump())
    except Exception as e:
        return Response({"error": f"Error communicating with the model: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RagChatView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        user_input = request.data.get('prompt')
        # Use the default prompt
        prompt_path = os.path.join(PROMPT_FOLDER, "custom_prompt.txt")
        if not os.path.exists(prompt_path):
            prompt_path = os.path.join(PROMPT_FOLDER, "prompt.txt")
        return handle_rag_chat(user_input, prompt_path)


class RagChatStructuredView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        user_input = request.data.get('prompt')
        # Use the structured output format hints prompt
        prompt_path = os.path.join(PROMPT_FOLDER, "prompt_output_format_hints.txt")
        return handle_rag_chat(user_input, prompt_path)


# New view for model-native structured output
class RagChatModelNativeStructuredView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        user_input = request.data.get('prompt')
        prompt_path = os.path.join(PROMPT_FOLDER, "model_native_structured_output_prompt.txt")
        return handle_model_native_structured_output(user_input, prompt_path)
