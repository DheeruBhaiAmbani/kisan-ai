import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .agents import KisanMitraOrchestrator # Your agent import
from .models import ChatSession, ChatMessage
from django.shortcuts import get_object_or_404, render
from datetime import datetime

# A simple decorator to log chat messages
def chat_logger(func):
    def wrapper(request, *args, **kwargs):
        user = request.user
        data = json.loads(request.body)
        user_message = data.get('message')
        session_id = data.get('session_id')

        if session_id:
            chat_session = get_object_or_404(ChatSession, id=session_id, user=user)
        else:
            chat_session = ChatSession.objects.create(user=user, title=user_message[:50]) # Initial title
            session_id = chat_session.id

        ChatMessage.objects.create(session=chat_session, sender='user', message=user_message)

        response = func(request, chat_session, user_message, *args, **kwargs)

        # Assuming response is a JsonResponse with 'message' key
        ai_response_text = json.loads(response.content).get('message')
        ChatMessage.objects.create(session=chat_session, sender='ai', message=ai_response_text)
        return response
    return wrapper


@csrf_exempt # Only use for API endpoints expected to be called without traditional form submission
@login_required # Ensure only logged-in users can chat
@chat_logger
def chat_with_ai(request, chat_session, user_message):
    if request.method == 'POST':
        # Initialize orchestrator with user's pin code for localized advice
        user_pin_code = request.user.pin_code if request.user.is_authenticated else None
        orchestrator = KisanMitraOrchestrator(user_pin_code=user_pin_code)
        
        ai_response = orchestrator.process_query(user_message)

        # Update session end time and potentially title
        chat_session.end_time = datetime.now()
        if not chat_session.title.startswith("Chat Session"): # Only update if not generic
             chat_session.title = user_message[:50] # Or use a smarter AI summary
        chat_session.save()

        return JsonResponse({'message': ai_response, 'session_id': chat_session.id})
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def chat_interface(request):
    # Retrieve existing chat sessions for the sidebar
    chat_sessions = ChatSession.objects.filter(user=request.user).order_by('-start_time')
    return render(request, 'chatbot/chat.html', {'chat_sessions': chat_sessions})

@login_required
def get_chat_history(request, session_id):
    chat_session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    messages = list(chat_session.messages.order_by('timestamp').values('sender', 'message', 'timestamp'))
    return JsonResponse({'messages': messages, 'session_id': session_id, 'title': chat_session.title})


