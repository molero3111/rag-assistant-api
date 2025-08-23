from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
import os
from .utils import (handle_rag_chat, handle_model_native_structured_output, 
                    handle_facts_and_explanations, handle_rag_chat_with_groq)

PROMPT_FOLDER = os.path.join(os.path.dirname(__file__), "prompts")

class RagChatView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        user_input = request.data.get('prompt')
        prompt_path = os.path.join(PROMPT_FOLDER, "custom_prompt.txt")
        if not os.path.exists(prompt_path):
            prompt_path = os.path.join(PROMPT_FOLDER, "prompt.txt")
        response = handle_rag_chat(user_input, prompt_path)
        status_code = status.HTTP_200_OK if not response.get('error', None) else status.HTTP_400_BAD_REQUEST
        return Response(response, status=status_code)


# prompt based structured output
class RagChatStructuredView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        user_input = request.data.get('prompt')
        # Use the structured output format hints prompt
        prompt_path = os.path.join(PROMPT_FOLDER, "prompt_output_format_hints.txt")
        response = handle_rag_chat(user_input, prompt_path)
        status_code = status.HTTP_200_OK if not response.get('error', None) else status.HTTP_400_BAD_REQUEST
        return Response(response, status=status_code)


# model-native structured output
class RagChatModelNativeStructuredView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        user_input = request.data.get('prompt')
        prompt_path = os.path.join(PROMPT_FOLDER, "model_native_structured_output_prompt.txt")
        response = handle_model_native_structured_output(user_input, prompt_path)
        status_code = status.HTTP_200_OK if not response.get('error', None) else status.HTTP_400_BAD_REQUEST
        return Response(response, status=status_code)

# facts and explanations
class RagFactsAndExplanationsView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        user_input = request.data.get('topic')
        if not user_input:
            return Response({'error': 'Topic is required.'}, status=status.HTTP_400_BAD_REQUEST)
        response = handle_facts_and_explanations(user_input)
        status_code = status.HTTP_200_OK if not response.get('error', None) else status.HTTP_500_INTERNAL_SERVER_ERROR
        return Response(response, status=status_code)

# Groq-based chat
class GroqRagChatView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        user_input = request.data.get('prompt')
        prompt_path = os.path.join(PROMPT_FOLDER, "custom_prompt.txt")
        if not os.path.exists(prompt_path):
            prompt_path = os.path.join(PROMPT_FOLDER, "prompt.txt")
        return Response(handle_rag_chat_with_groq(user_input))
