from django.urls import path
from .views import (RagChatView, RagChatStructuredView, RagChatModelNativeStructuredView, 
                    RagFactsAndExplanationsView, GroqRagChatView)

urlpatterns = [
    path('chat/', RagChatView.as_view(), name='rag_chat'),
    path('animals-list/', RagChatStructuredView.as_view(), name='prompt_animals_list'),
    path('animals/',  RagChatModelNativeStructuredView.as_view(), name='animals_list'),
    path('facts/', RagFactsAndExplanationsView.as_view(), name='facts_and_explanations'),
    path('groq-chat/', GroqRagChatView.as_view(), name='groq_rag_chat'),
]
