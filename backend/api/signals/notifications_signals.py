"""
Signals
=======
1. Notifications — business events (purchase, upgrade request/decision)
2. Audit trail   — automatic CREATE/UPDATE/DELETE via post_save / pre_delete

Why signals for audit (not middleware):
  - post_save fires AFTER save → instance.pk is always set → resource_id never empty
  - pre_delete fires BEFORE deletion → instance.pk still available
  - Middleware cannot get pk for CREATE (object doesn't exist at request time)

Import convention:
    from api.services.audit_logger import log_action
"""

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver



@receiver(post_save, sender='api.Transaction')
def notify_seller_on_purchase(sender, instance, created, **kwargs):
    """Notify seller when a buyer reserves a product."""
    if created and instance.status == 'RESERVED':
        try:
            from api.models.notifications import Notification
            buyer_name = instance.buyer.get_full_name() or instance.buyer.email
            Notification.objects.create(
                recipient=instance.seller,
                message=f"{buyer_name} wants to buy '{instance.product.name}'."
            )
        except Exception:
            pass


@receiver(post_save, sender='api.Transaction')
def notify_buyer_on_confirmation(sender, instance, created, **kwargs):
    """Notify buyer when seller confirms the reservation (AWAITING_PAYMENT)."""
    if not created and instance.status == 'AWAITING_PAYMENT':
        try:
            from api.models.notifications import Notification
            seller_name = instance.seller.get_full_name() or instance.seller.email
            Notification.objects.create(
                recipient=instance.buyer,
                message=(
                    f"'{instance.product.name}' foi confirmado por {seller_name}. "
                    f"Proceda ao pagamento para concluir a compra."
                )
            )
        except Exception:
            pass


@receiver(post_save, sender='api.Transaction')
def notify_seller_on_payment(sender, instance, created, **kwargs):
    """Notify seller when payment is confirmed (PAID)."""
    if not created and instance.status == 'PAID':
        try:
            from api.models.notifications import Notification
            buyer_name = instance.buyer.get_full_name() or instance.buyer.email
            Notification.objects.create(
                recipient=instance.seller,
                message=(
                    f"Pagamento recebido de {buyer_name} para '{instance.product.name}'. "
                    f"Pode agora concluir a transação."
                )
            )
        except Exception:
            pass


@receiver(post_save, sender='api.UpgradeRequest')
def handle_upgrade_request(sender, instance, created, **kwargs):
    """Notify admins on new request; notify user on decision."""
    try:
        from api.models.notifications import Notification
        from django.contrib.auth import get_user_model
        User = get_user_model()

        if created and instance.status == 'PENDING':
            user_name = instance.user.get_full_name() or instance.user.email
            admins = User.objects.filter(role='ADMIN')
            Notification.objects.bulk_create([
                Notification(
                    recipient=admin,
                    message=(
                        f"User '{user_name}' requested an upgrade to Producer. "
                        f"Review at: POST /api/users/{instance.user.id}/approve-upgrade/"
                    )
                )
                for admin in admins
            ])

        elif not created and instance.status in ('APPROVED', 'REJECTED'):
            message = (
                "Your upgrade request to Producer has been approved. "
                "You can now list products on the marketplace."
                if instance.status == 'APPROVED'
                else
                "Your upgrade request to Producer has been rejected by an admin. "
                "You may submit a new request if you wish."
            )
            Notification.objects.create(recipient=instance.user, message=message)
    except Exception:
        pass
