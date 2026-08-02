from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.shortcuts import get_object_or_404

from api.models.marketplace_chat import MarketplaceChat, MarketplaceMessage, MarketplaceChatReservation
from api.models.marketplace import Transaction
from api.serializers.marketplace_chat import (
    MarketplaceChatSerializer,
    MarketplaceMessageSerializer,
    MarketplaceChatReservationSerializer,
)
from api.permissions import IsMarketplaceChatParticipant


class MarketplaceChatViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    GET /marketplace/chats/          — lista chats ACTIVE do utilizador autenticado
    GET /marketplace/chats/{id}/     — detalhes do chat
    GET /marketplace/chats/{id}/messages/     — mensagens do chat
    POST /marketplace/chats/{id}/messages/    — enviar mensagem
    GET /marketplace/chats/{id}/reservations/ — reservas do chat
    """
    serializer_class = MarketplaceChatSerializer
    permission_classes = [IsAuthenticated, IsMarketplaceChatParticipant]

    def get_queryset(self):
        user = self.request.user
        return (
            MarketplaceChat.objects
            .filter(Q(buyer=user) | Q(seller=user), status=MarketplaceChat.STATUS_ACTIVE)
            .select_related('buyer', 'seller')
            .prefetch_related('messages')
        )

    def get_object(self):
        """Permite aceder a chats CLOSED nas sub-rotas, mas não na listagem."""
        user = self.request.user
        qs = MarketplaceChat.objects.filter(
            Q(buyer=user) | Q(seller=user)
        ).select_related('buyer', 'seller')
        obj = get_object_or_404(qs, pk=self.kwargs['pk'])
        self.check_object_permissions(self.request, obj)
        return obj

    @action(detail=True, methods=['get', 'post'], url_path='messages')
    def messages(self, request, pk=None):
        chat = self.get_object()

        if request.method == 'GET':
            msgs = chat.messages.select_related('sender').all()
            # Marcar como lidas as mensagens do outro utilizador
            msgs.exclude(sender=request.user).filter(is_read=False).update(is_read=True)
            serializer = MarketplaceMessageSerializer(msgs, many=True, context={'request': request})
            return Response(serializer.data)

        # POST — enviar mensagem
        if not chat.is_active:
            return Response(
                {"detail": "Este chat está encerrado. Não é possível enviar mensagens."},
                status=status.HTTP_403_FORBIDDEN,
            )
        content = request.data.get('content', '').strip()
        if not content:
            return Response({"detail": "O conteúdo da mensagem não pode ser vazio."}, status=400)

        msg = MarketplaceMessage.objects.create(
            chat=chat,
            sender=request.user,
            content=content,
        )
        serializer = MarketplaceMessageSerializer(msg, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='reservations')
    def reservations(self, request, pk=None):
        chat = self.get_object()
        qs = chat.chat_reservations.select_related('transaction__product')
        serializer = MarketplaceChatReservationSerializer(qs, many=True)
        return Response(serializer.data)


class ReservationChatView(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    GET /marketplace/reservations/{id}/chat/
    Retorna o chat associado a uma reserva (transação).
    """
    serializer_class = MarketplaceChatSerializer
    permission_classes = [IsAuthenticated, IsMarketplaceChatParticipant]

    def get_object(self):
        user = self.request.user
        txn = get_object_or_404(
            Transaction,
            pk=self.kwargs['pk'],
        )
        if user not in (txn.buyer, txn.seller) and not user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Não tem acesso a esta reserva.")

        chat = get_object_or_404(
            MarketplaceChat,
            chat_reservations__transaction=txn,
        )
        self.check_object_permissions(self.request, chat)
        return chat

    def retrieve(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = self.get_serializer(obj, context={'request': request})
        return Response(serializer.data)
