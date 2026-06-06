from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.conf import settings

from api.services.audit_logger import log_action
from api.signals.utils import safe_serialize


def is_disabled():
    return not getattr(settings, "AUDIT_ENABLED", True)


@receiver(post_save)
def log_create_update(sender, instance, created, **kwargs):

    if is_disabled():
        return

    if sender.__name__ == "AuditLog":
        return

    try:
        log_action(
            action="CREATE" if created else "UPDATE",
            instance=instance,
            after=safe_serialize(instance),
            status="SUCCESS",
        )
    except Exception:
        pass


@receiver(pre_delete)
def log_delete(sender, instance, **kwargs):

    if is_disabled():
        return

    if sender.__name__ == "AuditLog":
        return

    try:
        log_action(
            action="DELETE",
            instance=instance,
            before=safe_serialize(instance),
            status="SUCCESS",
        )
    except Exception:
        pass