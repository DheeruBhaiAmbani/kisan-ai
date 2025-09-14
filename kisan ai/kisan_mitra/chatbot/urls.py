from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.chat_with_ai, name='chat_with_ai'),
    path('chat/interface/', views.chat_interface, name='chat_interface'),
    path('chat/history/<int:session_id>/', views.get_chat_history, name='get_chat_history'),
]