from django.urls import path
from .views import RagChatView

urlpatterns = [
    path('chat/', RagChatView.as_view(), name='rag_chat'),
]
