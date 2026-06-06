"""
Audit Logger Service
====================
Single source of truth for all audit logging.

Import:
    from api.services.audit_logger import log_action

Key fix:
    - `user` parameter is ALWAYS respected when passed explicitly
    - Falls back to request.user only when user=None AND request has authenticated user
    - LOGIN logs pass user explicitly — never rely on request.user for auth events
"""

import uuid
import logging

logger = logging.getLogger("api.audit")

_CRUD_ACTIONS = {"CREATE", "UPDATE", "DELETE"}


def _get_current_request():
    try:
        from api.middleware import get_current_request
        return get_current_request()
    except Exception:
        return None


def _get_ip(request):
    if request is None:
        return None
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _get_user_agent(request):
    if request is None:
        return ""
    return request.META.get("HTTP_USER_AGENT", "")


def _get_request_id(request):
    if request is None:
        return str(uuid.uuid4())
    return getattr(request, "audit_request_id", str(uuid.uuid4()))


def _resolve_user_from_request(request):
    """Get authenticated user from request — only used as fallback."""
    if request and hasattr(request, "user") and request.user.is_authenticated:
        return request.user
    return None


def serialize_instance(instance):
    """Safely serialize a model instance to a plain dict."""
    if instance is None:
        return None
    try:
        from django.forms.models import model_to_dict
        data = model_to_dict(instance)
        return {
            k: v if isinstance(v, (str, int, float, bool, type(None))) else str(v)
            for k, v in data.items()
        }
    except Exception as e:
        logger.debug(f"[AuditLog] serialize_instance failed: {e}")
        return None


def log_action(
    *,
    action,
    user=None,              # EXPLICIT user — always respected (e.g. for LOGIN)
    resource="",
    instance=None,
    resource_id=None,
    status="SUCCESS",
    severity="LOW",
    detail="",
    before=None,
    after=None,
    request=None,
    source="API",
):
    """
    Record an audit log entry. Never raises.

    Parameters
    ----------
    user        : User instance — ALWAYS used when provided (critical for LOGIN)
    action      : str — CREATE, UPDATE, DELETE, LOGIN, LOGOUT, LOGIN_FAILED, etc.
    resource    : str — model name, e.g. 'Product', 'Auth'
    instance    : model instance — pk extracted automatically for CRUD
    resource_id : str — manual fallback when instance is not available
    status      : 'SUCCESS' or 'FAILED'
    severity    : 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    detail      : human-readable description
    before/after: dict snapshots for UPDATE/DELETE
    request     : Django request (for IP, user-agent, request_id)
    source      : 'API', 'WEB', 'ADMIN'
    """
    try:
        from api.models.audit import AuditLog

        # Use thread-local request as fallback if not passed
        if request is None:
            request = _get_current_request()

        # ── Resolve resource and resource_id from instance ────────────────
        if instance is not None:
            resource = instance.__class__.__name__
            resource_id = str(instance.pk) if instance.pk is not None else ""

        resolved_resource_id = str(resource_id) if resource_id is not None else ""

        # ── Validate CRUD must have resource_id ───────────────────────────
        if action in _CRUD_ACTIONS and not resolved_resource_id:
            logger.warning(
                f"[AuditLog] BLOCKED: action={action} resource={resource} "
                f"has empty resource_id."
            )
            return None

        # ── Resolve user ──────────────────────────────────────────────────
        # IMPORTANT: explicit `user` parameter always wins.
        # Only fall back to request.user if user was not passed.
        if user is None:
            user = _resolve_user_from_request(request)

        user_email = getattr(user, "email", "") or ""

        # ── Resolve source ────────────────────────────────────────────────
        if source == "API" and request:
            path = getattr(request, "path", "")
            if path.startswith("/admin/"):
                source = "ADMIN"

        entry = AuditLog.objects.create(
            user=user if (user and getattr(user, "pk", None)) else None,
            user_email=user_email,
            action=action,
            resource=resource,
            resource_id=resolved_resource_id,
            status=status,
            severity=severity,
            detail=detail,
            before=before,
            after=after,
            ip_address=_get_ip(request),
            user_agent=_get_user_agent(request),
            http_method=getattr(request, "method", "") if request else "",
            path=getattr(request, "path", "") if request else "",
            query_params=request.GET.dict() if request else None,
            source=source,
            request_id=_get_request_id(request),
        )

        logger.debug(
            f"[AuditLog] {action} {resource} id={resolved_resource_id} "
            f"user={user_email or 'anonymous'} status={status}"
        )
        return entry

    except Exception as exc:
        logger.warning(f"[AuditLog] Failed to record log: {exc}")
        return None
