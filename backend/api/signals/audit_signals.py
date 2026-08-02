"""
Audit Signals — CRUD, Admin login, role change tracking.
"""
from django.db.models.signals import post_save, pre_delete, pre_save
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from django.conf import settings

from api.services.audit_logger import log_action
from api.signals.utils import safe_serialize

TRACKED_FIELDS = {'role', 'is_staff', 'is_superuser', 'is_active'}
SKIP_MODELS = {'AuditLog', 'SecurityLog', 'PageVisit'}


def is_disabled() -> bool:
    return not getattr(settings, 'AUDIT_ENABLED', True)


# ── CRUD ──────────────────────────────────────────────────────────────────────

@receiver(post_save)
def log_create_update(sender, instance, created, **kwargs):
    if is_disabled() or sender.__name__ in SKIP_MODELS:
        return
    try:
        log_action(
            action='CREATE' if created else 'UPDATE',
            instance=instance,
            after=safe_serialize(instance),
            status='SUCCESS',
        )
    except Exception:
        pass


@receiver(pre_delete)
def log_delete(sender, instance, **kwargs):
    if is_disabled() or sender.__name__ in SKIP_MODELS:
        return
    try:
        log_action(
            action='DELETE',
            instance=instance,
            before=safe_serialize(instance),
            status='SUCCESS',
        )
    except Exception:
        pass


# ── Role change detector ──────────────────────────────────────────────────────

@receiver(pre_save)
def track_role_change(sender, instance, **kwargs):
    if is_disabled() or sender.__name__ != 'User' or not instance.pk:
        return
    try:
        old = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    for field in TRACKED_FIELDS:
        old_val = getattr(old, field, None)
        new_val = getattr(instance, field, None)
        if old_val == new_val:
            continue
        try:
            from api.middleware import get_current_request
            req = get_current_request()
            changer = req.user if (req and hasattr(req, 'user') and req.user.is_authenticated) else None
            log_action(
                action='ROLE_CHANGED',
                user=changer,
                resource='User',
                resource_id=str(instance.pk),
                before={field: str(old_val)},
                after={field: str(new_val)},
                detail=f'{field}: {old_val} -> {new_val} for {instance.email}',
                severity='HIGH',
            )
            if field == 'role':
                from api.services.notification_service import alert_role_changed
                alert_role_changed(
                    instance.email, str(old_val), str(new_val),
                    getattr(changer, 'email', 'system')
                )
        except Exception:
            pass


# ── Django auth signals (Admin + JWT) ─────────────────────────────────────────

@receiver(user_logged_in)
def on_user_logged_in(sender, request, user, **kwargs):
    if is_disabled():
        return
    try:
        source = 'ADMIN' if (request and request.path.startswith('/admin/')) else 'API'
        log_action(
            action='LOGIN', user=user, resource='Auth',
            resource_id=str(user.pk), status='SUCCESS',
            detail=f'Login: {user.email}', request=request, source=source,
        )
    except Exception:
        pass


@receiver(user_logged_out)
def on_user_logged_out(sender, request, user, **kwargs):
    if is_disabled():
        return
    try:
        source = 'ADMIN' if (request and request.path.startswith('/admin/')) else 'API'
        log_action(
            action='LOGOUT', user=user, resource='Auth',
            resource_id=str(user.pk) if user else '',
            status='SUCCESS', detail=f'Logout: {getattr(user, "email", "unknown")}',
            request=request, source=source,
        )
    except Exception:
        pass


@receiver(user_login_failed)
def on_user_login_failed(sender, credentials, request, **kwargs):
    if is_disabled():
        return
    try:
        email = credentials.get('email') or credentials.get('username', '')
        source = 'ADMIN' if (request and request.path.startswith('/admin/')) else 'API'
        log_action(
            action='LOGIN_FAILED', user=None, resource='Auth', resource_id='',
            status='FAILED', severity='MEDIUM',
            detail=f"Failed login for '{email}'",
            request=request, source=source,
        )
        from api.services.notification_service import alert_login_failed
        from api.middleware import get_client_ip
        alert_login_failed(email, get_client_ip(request) if request else '')
    except Exception:
        pass
