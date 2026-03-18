from django.db import models
from django.conf import settings
from api.models.location import Distrito, Provincia

User = settings.AUTH_USER_MODEL

class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    titulo = models.CharField(max_length=200,default="Nova conversa")
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo} ({self.user})"

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='mensagens')
    mensagem = models.TextField()
    is_bot = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        autor = "Bot" if self.is_bot else (self.user or self.session.user)
        return f"{autor}: {self.mensagem[:50]}"
