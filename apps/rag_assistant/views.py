from django.shortcuts import render
from .utils import get_relevant_context
from django.conf import settings
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

LLM_API_URL = getattr(settings, "LLM_API_URL", "http://localhost:1234/v1/chat/completions")
LLM_MODEL = getattr(settings, "LLM_MODEL", "mistralai/mathstral-7b-v0.1")
LLM_API_KEY = getattr(settings, "LLM_API_KEY", "")

class RagChatView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        user_input = request.data.get('prompt')
        if not user_input:
            return Response({'error': 'Prompt is required.'}, status=status.HTTP_400_BAD_REQUEST)
        context = get_relevant_context(user_input)
        messages = [
            {"role": "user", "content": (
                "You are a helpful tutor for children and teenagers. "
                "Use the following context from textbooks to help answer the question. "
                "Let's think step by step.\n\n"
                "If the context contains relevant formulas, definitions, or examples, use them to solve the problem, even if the exact answer is not present. "
                "If the context is not helpful in the way that the question is not really about math nor biology, you may answer based on your own knowledge.\n\n"
                "If the context is not helpful at all, still try to solve their inquiry either with your knowledge or by suggesting another book or resource.\n\n"
                f"Context:\n{context}\n\nQuestion:\n{user_input}"
            )}
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
