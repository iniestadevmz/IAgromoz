from django.utils import timezone
from django.db import transaction as db_transaction
from api.models.marketplace_chat import MarketplaceChat, MarketplaceChatReservation, TERMINAL_STATUSES


def get_or_create_chat_for_reservation(txn):
    """
    Cria ou reutiliza um MarketplaceChat ACTIVE entre buyer e seller.
    Associa sempre a transação ao chat via MarketplaceChatReservation.
    Se não existir chat ativo, cria um novo (nunca reabre chats CLOSED).
    """
    with db_transaction.atomic():
        chat = (
            MarketplaceChat.objects
            .filter(buyer=txn.buyer, seller=txn.seller, status=MarketplaceChat.STATUS_ACTIVE)
            .select_for_update()
            .first()
        )
        if not chat:
            chat = MarketplaceChat.objects.create(
                buyer=txn.buyer,
                seller=txn.seller,
                status=MarketplaceChat.STATUS_ACTIVE,
            )
        MarketplaceChatReservation.objects.get_or_create(
            chat=chat,
            transaction=txn,
        )
    return chat


def maybe_close_chat(txn):
    """
    Após uma transação mudar para estado terminal (COMPLETED/CANCELLED),
    verifica se todas as reservas do chat estão em estado terminal.
    Se sim, encerra o chat.
    """
    try:
        reservation = txn.chat_reservation
    except Exception:
        return

    chat = reservation.chat
    if chat.status == MarketplaceChat.STATUS_CLOSED:
        return

    # Verifica se alguma reserva associada ainda está em estado não-terminal
    pending = chat.chat_reservations.exclude(
        transaction__status__in=TERMINAL_STATUSES
    ).exists()

    if not pending:
        with db_transaction.atomic():
            MarketplaceChat.objects.filter(pk=chat.pk).update(
                status=MarketplaceChat.STATUS_CLOSED,
                closed_at=timezone.now(),
            )
