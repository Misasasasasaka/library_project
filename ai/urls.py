"""
AI 推荐 URL 路由
"""
from django.urls import path
from . import views

urlpatterns = [
    path("ai/chat", views.chat_view, name="ai_chat"),
    path("ai/chat/stream", views.chat_stream_view, name="ai_chat_stream"),
]
