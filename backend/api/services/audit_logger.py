"""
Audit Logger Service
====================
Ponto central de auditoria. Nunca lança exceções.

Uso:
    from api.services.audit_logger import log_action

Melhorias:
- Device info (browser, OS, device type)
- Snapshot seguro (exclui campos sensíveis)
- Hash encadeado para integridade
- SecurityLog automático para eventos críticos
"""
import uuid
import logging

logger = logging.getLogger('api.audit')

CRUD_ACTIONS = {'CREATE', 'UPDATE', 'DELETE'}

# Campos excluídos dos snapshots before/after
SENSITIVE_FIELDS = {
    'password', 'token', 'jwt', 'secret', 'api_key',
    'refresh_token', 'access_token', 'id_token', 'google_id',
    'last_login', 'password_hash',
}

# Acções que geram também SecurityLog
SECURITY_ACTIONS = {
    'LOGIN', 'LOGIN_FAILED', 'LOGOUT',
    'ROLE_CHANGED', 'PASSWORD_CHANGED', 'PERMISSION_DENIED',
    'GOOGLE_LOGIN', 'GOOGLE_LINKED',
}

# Mapeamento de severity por acção
ACTION_SEVERITY = {
    'DELETE': 'HIGH',
    'ROLE_CHANGED': 'HIGH',
    'LOGIN_FAILED': 'MEDIUM',
    'PERMISSION_DENIED': 'MEDIUM',
    'PASSWORD_CHANGED': 'MEDIUM',
    'CREATE': 'LOW',
    'UPDATE': 'LOW',
    'LOGIN': 'LOW',
    'LOGOUT': 'LOW',
    'VIEW': 'LOW',
    'REQUEST': 'LOW',
    'GOOGLE_LOGIN': 'LOW',
}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_current_request():
    try:
        from api.middleware import get_current_request
        return get_current_request()
    except Exception:
        return None


def _get_ip(request):
    if request is None:
        return None
    try:
        from api.middleware import get_client_ip
        return get_client_ip(request)
    except Exception:
        return request.META.get('REMOTE_ADDR')


def _get_user_agent(request) -> str:
    if request is None:
        return ''
    return request.META.get('HTTP_USER_AGENT', '')


def _get_request_id(request) -> str:
    if request is None:
        return str(uuid.uuid4())
    return getattr(request, 'audit_request_id', str(uuid.uuid4()))


def _resolve_user(user, request):
    if user is not None:
        return user
    if request and hasattr(request, 'user') and request.user.is_authenticated:
        return request.user
    return None


def _safe_snapshot(data: dict) -> dict:
    """Remove campos sensíveis do snapshot."""
    if not data:
        return data
    return {k: v for k, v in data.items() if k.lower() not in SENSITIVE_FIELDS}


def _get_previous_hash() -> str:
    try:
        from api.models.audit import AuditLog
        last = AuditLog.objects.only('current_hash').order_by('-timestamp').first()
        return last.current_hash if last else ''
    except Exception:
        return ''


def serialize_instance(instance) -> dict:
    """Serializa instância para JSON seguro, excluindo campos sensíveis."""
    if instance is None:
        return None
    try:
        from api.signals.utils import safe_serialize
        data = safe_serialize(instance)
        return _safe_snapshot(data) if data else None
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Main logger
# ─────────────────────────────────────────────────────────────────────────────

def log_action(
    *,
    action: str,
    user=None,
    resource: str = '',
    instance=None,
    resource_id=None,
    status: str = 'SUCCESS',
    severity: str = None,
    detail: str = '',
    before: dict = None,
    after: dict = None,
    request=None,
    source: str = 'API',
):
    """
    Cria entrada no AuditLog.

    user:     utilizador explícito — sempre tem prioridade
    severity: se None, inferido pela acção
    """
    try:
        from api.models.audit import AuditLog
        from api.services.device_info import parse_device_info

        if request is None:
            request = _get_current_request()

        # Resolve instância
        if instance is not None:
            resource = instance.__class__.__name__
            resource_id = str(instance.pk) if instance.pk else ''

        resolved_resource_id = str(resource_id) if resource_id is not None else ''

        if action in CRUD_ACTIONS and not resolved_resource_id:
            logger.warning(f'[AuditLog] Blocked {action} — missing resource_id')
            return None

        # Resolve user
        user = _resolve_user(user, request)
        user_email = getattr(user, 'email', '') or ''

        # Source
        if source == 'API' and request:
            if getattr(request, 'path', '').startswith('/admin/'):
                source = 'ADMIN'

        # Severity auto
        if severity is None:
            severity = ACTION_SEVERITY.get(action, 'LOW')

        # Device info
        ua = _get_user_agent(request)
        device = parse_device_info(ua)

        # Snapshots seguros
        safe_before = _safe_snapshot(before) if before else None
        safe_after = _safe_snapshot(after) if after else None

        # Hash encadeado
        previous_hash = _get_previous_hash()

        entry = AuditLog(
            user=user if (user and getattr(user, 'pk', None)) else None,
            user_email=user_email,
            action=action,
            resource=resource,
            resource_id=resolved_resource_id,
            status=status,
            severity=severity,
            detail=detail,
            before=safe_before,
            after=safe_after,
            ip_address=_get_ip(request),
            user_agent=ua,
            http_method=getattr(request, 'method', '') if request else '',
            path=getattr(request, 'path', '') if request else '',
            query_params=request.GET.dict() if request else None,
            source=source,
            request_id=_get_request_id(request),
            browser=device['browser'],
            operating_system=device['operating_system'],
            device_type=device['device_type'],
            previous_hash=previous_hash,
        )

        # Calcular hash após preencher campos
        entry.save()
        entry.current_hash = entry.compute_hash()
        entry.save(update_fields=['current_hash'])

        logger.debug(
            f'[AuditLog] {action} {resource} id={resolved_resource_id} '
            f'user={user_email or "anonymous"} status={status}'
        )

        # Espelhar em SecurityLog para eventos críticos
        if action in SECURITY_ACTIONS:
            _mirror_to_security_log(entry, action, user, request)

        return entry

    except Exception as exc:
        logger.warning(f'[AuditLog] Failed: {exc}')
        return None


def _mirror_to_security_log(audit_entry, action: str, user, request):
    """Replica eventos de segurança no SecurityLog."""
    try:
        from api.services.security_logger import log_security_event
        event_map = {
            'LOGIN': 'LOGIN',
            'LOGIN_FAILED': 'LOGIN_FAILED',
            'LOGOUT': 'LOGOUT',
            'ROLE_CHANGED': 'ROLE_CHANGED',
            'PASSWORD_CHANGED': 'PASSWORD_CHANGED',
            'PERMISSION_DENIED': 'PERMISSION_DENIED',
            'GOOGLE_LOGIN': 'GOOGLE_LOGIN',
            'GOOGLE_LINKED': 'GOOGLE_LINKED',
        }
        event_type = event_map.get(action)
        if event_type:
            log_security_event(
                event_type=event_type,
                user=user,
                request=request,
                detail=audit_entry.detail,
                source=audit_entry.source,
            )
    except Exception:
        pass
