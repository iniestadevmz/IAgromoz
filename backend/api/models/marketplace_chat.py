from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

TERMINAL_STATUSES = {'COMPLETED', 'CANCELLED'}


class MarketplaceChat(models.Model):
    STATUS_ACTIVE = 'ACTIVE'
    STATUS_CLOSED = 'CLOSED'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Ativo'),
        (STATUS_CLOSED, 'Encerrado'),
    ]

    buyer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='marketplace_chats_as_buyer'
    )
    seller = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='marketplace_chats_as_seller'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Chat #{self.id} {self.buyer} ↔ {self.seller} [{self.status}]"

    @property
    def is_active(self):
        return self.status == self.STATUS_ACTIVE


class MarketplaceMessage(models.Model):
    chat = models.ForeignKey(
        MarketplaceChat, on_delete=models.CASCADE, related_name='messages'
    )
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='marketplace_messages_sent'
    )
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Msg #{self.id} by {self.sender} in Chat #{self.chat_id}"


class MarketplaceChatReservation(models.Model):
    """Liga uma Transaction (reserva) a um MarketplaceChat."""
    chat = models.ForeignKey(
        MarketplaceChat, on_delete=models.CASCADE, related_name='chat_reservations'
    )
    transaction = models.OneToOneField(
        'api.Transaction', on_delete=models.CASCADE, related_name='chat_reservation'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Reservation #{self.transaction_id} in Chat #{self.chat_id}"
