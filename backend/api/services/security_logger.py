"""
SecurityLogger
==============
Centraliza eventos de segurança num log dedicado.
Nunca lança exceções — fail-safe by design.
"""
import logging
from typing import Optional

logger = logging.getLogger('api.security')


def log_security_event(
    *,
    event_type: str,
    user=None,
    request=None,
    detail: str = '',
    extra: Optional[dict] = None,
    source: str = 'API',
) -> None:
    """
    Regista um evento de segurança no SecurityLog.

    event_type: SecurityLog.EventType choice
    user:       instância User explícita (opcional)
    request:    Django HttpRequest (para IP, user-agent, request_id)
    detail:     descrição legível
    extra:      dados adicionais em JSON
    source:     'API' | 'ADMIN' | 'WEB'
    """
    try:
        from api.models.audit import SecurityLog
        from api.middleware import get_client_ip, get_current_request

        if request is None:
            request = get_current_request()

        if user is None and request and hasattr(request, 'user') and request.user.is_authenticated:
            user = request.user

        ip = get_client_ip(request) if request else None
        ua = request.META.get('HTTP_USER_AGENT', '') if request else ''
        rid = getattr(request, 'audit_request_id', '') if request else ''
        src = source
        if request and request.path.startswith('/admin/'):
            src = 'ADMIN'

        SecurityLog.objects.create(
            user=user if (user and getattr(user, 'pk', None)) else None,
            user_email=getattr(user, 'email', '') or '',
            event_type=event_type,
            ip_address=ip,
            user_agent=ua,
            detail=detail,
            extra=extra,
            request_id=rid,
            source=src,
        )

        logger.info(f'[SecurityLog] {event_type} — {getattr(user, "email", "anonymous")} — {ip}')

    except Exception as exc:
        logger.warning(f'[SecurityLog] Failed to record: {exc}')
