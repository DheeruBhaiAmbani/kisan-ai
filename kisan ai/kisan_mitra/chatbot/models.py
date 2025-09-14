from django.db import models
from users.models import User

class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    title = models.CharField(max_length=100, blank=True) # AI can summarize/title the chat

    def __str__(self):
        return f"Chat Session {self.id} with {self.user.username}"

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10, choices=[('user', 'User'), ('ai', 'AI')])
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    # Optional: If you want to store tool calls or specific agent invoked
    metadata = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.sender}: {self.message[:50]}"