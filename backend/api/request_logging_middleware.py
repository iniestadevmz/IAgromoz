"""
RequestLoggingMiddleware
========================
Regista todos os requests HTTP com:
  endpoint, método, status code, duração, user, IP, request_id.

Complementa o AuditMiddleware existente — não o substitui.
AuditMiddleware grava na BD (AuditLog).
RequestLoggingMiddleware grava nos ficheiros de log (api.log / console).
"""
import logging
import time

logger = logging.getLogger('api.requests')

SKIP_PATHS = ('/static/', '/media/', '/favicon.ico')


class RequestLoggingMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if any(request.path.startswith(p) for p in SKIP_PATHS):
            return self.get_response(request)

        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = (time.monotonic() - start) * 1000

        self._log(request, response, duration_ms)
        return response

    def _log(self, request, response, duration_ms: float) -> None:
        request_id = getattr(request, 'audit_request_id', '-')
        user = '-'
        if hasattr(request, 'user') and request.user.is_authenticated:
            user = request.user.email

        try:
            from api.middleware import get_client_ip
            ip = get_client_ip(request) or '-'
        except Exception:
            ip = request.META.get('REMOTE_ADDR', '-')

        status = response.status_code
        level = logging.WARNING if status >= 400 else logging.INFO

        logger.log(
            level,
            f'{request.method} {request.path} {status} {duration_ms:.1f}ms | '
            f'req={request_id} user={user} ip={ip}',
            extra={
                'request_id': request_id,
                'user': user,
                'ip': ip,
                'method': request.method,
                'path': request.path,
            }
        )
