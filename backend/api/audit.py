"""
Audit Trail Service
===================
Central utility for recording audit logs.

The key design principle:
  - CREATE/UPDATE/DELETE logs come from signals (post_save / pre_delete)
    so the PK is always available after the DB write.
  - The middleware only logs AUTH actions (LOGIN, LOGOUT, LOGIN_FAILED)
    and generic HTTP-level events — never CREATE/UPDATE/DELETE, to avoid
    the empty resource_id problem.
  - log_action() accepts an `instance` parameter and extracts pk automatically.

Usage:
    from api.audit import log_action, AuditAction, AuditStatus

    # With instance (preferred — pk extracted automatically)
    log_action(
        user=request.user,
        action=AuditAction.UPDATE,
        instance=product,
        status=AuditStatus.SUCCESS,
        detail='Price updated',
        request=request,
        before={'price': '100.00'},
        after={'price': '150.00'},
    )

    # Without instance (for auth events)
    log_action(
        user=user,
        action=AuditAction.LOGIN,
        resource='Auth',
        resource_id=str(user.pk),
        status=AuditStatus.SUCCESS,
        detail='Login successful',
        request=request,
    )
"""

import uuid
import logging

logger = logging.getLogger(__name__)


class AuditAction:
    CREATE           = 'CREATE'
    UPDATE           = 'UPDATE'
    DELETE           = 'DELETE'
    LOGIN            = 'LOGIN'
    LOGOUT           = 'LOGOUT'
    LOGIN_FAILED     = 'LOGIN_FAILED'
    UPGRADE_REQUEST  = 'UPGRADE_REQUEST'
    UPGRADE_APPROVED = 'UPGRADE_APPROVED'
    UPGRADE_REJECTED = 'UPGRADE_REJECTED'
    VIEW             = 'VIEW'

    # Actions that MUST have a resource_id
    REQUIRE_RESOURCE_ID = {'CREATE', 'UPDATE', 'DELETE'}


class AuditStatus:
    SUCCESS = 'SUCCESS'
    FAILED  = 'FAILED'


class AuditSource:
    API   = 'API'
    WEB   = 'WEB'
    ADMIN = 'ADMIN'


def _get_ip(request):
    if request is None:
        return None
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _get_user_agent(request):
    if request is None:
        return ''
    return request.META.get('HTTP_USER_AGENT', '')


def _get_request_id(request):
    if request is None:
        return str(uuid.uuid4())
    return getattr(request, 'audit_request_id', str(uuid.uuid4()))


def _get_source(request):
    if request is None:
        return AuditSource.API
    path = getattr(request, 'path', '')
    if path.startswith('/admin/'):
        return AuditSource.ADMIN
    return AuditSource.API


def _resource_name_from_instance(instance):
    """Extract the model class name as the resource name."""
    return instance.__class__.__name__


def log_action(
    user=None,
    action=AuditAction.CREATE,
    instance=None,       # preferred: pass the model instance
    resource='',         # fallback if no instance
    resource_id='',      # fallback if no instance
    status=AuditStatus.SUCCESS,
    detail='',
    request=None,
    before=None,
    after=None,
    source=None,
):
    """
    Record an audit log entry. Never raises — all errors are silently caught.

    When `instance` is provided:
      - resource is derived from instance.__class__.__name__
      - resource_id is derived from instance.pk (guaranteed non-empty after save)

    When `instance` is None:
      - resource and resource_id must be provided manually (for auth events etc.)
    """
    try:
        from api.models.audit import AuditLog

        # ── Resolve resource and resource_id from instance ────────────────
        if instance is not None:
            resolved_resource    = _resource_name_from_instance(instance)
            resolved_resource_id = str(instance.pk) if instance.pk is not None else ''
        else:
            resolved_resource    = resource
            resolved_resource_id = str(resource_id) if resource_id else ''

        # ── Validate: warn if CREATE/UPDATE/DELETE has no resource_id ─────
        if action in AuditAction.REQUIRE_RESOURCE_ID and not resolved_resource_id:
            logger.warning(
                f"[AuditLog] WARNING: action={action} resource={resolved_resource} "
                f"has empty resource_id. Log will be recorded but investigate the caller."
            )

        # ── Resolve user email ─────────────────────────────────────────────
        user_email = ''
        if user and hasattr(user, 'email'):
            user_email = user.email or ''

        AuditLog.objects.create(
            user=user if (user and hasattr(user, 'pk') and user.pk) else None,
            user_email=user_email,
            action=action,
            resource=resolved_resource,
            resource_id=resolved_resource_id,
            status=status,
            detail=detail,
            before=before,
            after=after,
            ip_address=_get_ip(request),
            user_agent=_get_user_agent(request),
            source=source or _get_source(request),
            request_id=_get_request_id(request),
        )

    except Exception as exc:
        # Audit failures must NEVER break the application
        logger.warning(f"[AuditLog] Failed to record log: {exc}")


def serialize_instance(instance):
    """
    Safely serialize a model instance to a plain dict for before/after snapshots.
    Returns None on failure.
    """
    if instance is None:
        return None
    try:
        from django.forms.models import model_to_dict
        data = model_to_dict(instance)
        result = {}
        for k, v in data.items():
            if isinstance(v, (str, int, float, bool, type(None))):
                result[k] = v
            else:
                result[k] = str(v)
        return result
    except Exception:
        return None
