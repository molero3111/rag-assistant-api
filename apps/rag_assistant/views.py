from django.shortcuts import render
from .utils import get_relevant_context
from django.conf import settings
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
import os

LLM_API_URL = getattr(settings, "LLM_API_URL", "http://localhost:1234/v1/chat/completions")
LLM_MODEL = getattr(settings, "LLM_MODEL", "mistralai/mathstral-7b-v0.1")
LLM_API_KEY = getattr(settings, "LLM_API_KEY", "")

PROMPT_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "prompt.txt")
if not os.path.exists(PROMPT_TEMPLATE_PATH):
    PROMPT_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "prompt_template.txt")

def load_prompt_template():
    with open(PROMPT_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        return f.read()

class RagChatView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        user_input = request.data.get('prompt')
        if not user_input:
            return Response({'error': 'Prompt is required.'}, status=status.HTTP_400_BAD_REQUEST)
        context = get_relevant_context(user_input)
        prompt_template = load_prompt_template()
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
