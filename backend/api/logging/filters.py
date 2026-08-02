"""
Logging Filters
===============
Filtros customizados para enriquecer os registos de log com
informação de contexto: request_id, user, IP.
"""
import logging


class RequestContextFilter(logging.Filter):
    """
    Adiciona request_id, user e IP ao LogRecord quando disponíveis via thread-local.
    Funciona com o AuditMiddleware existente.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            from api.middleware import get_current_request, get_client_ip
            request = get_current_request()
            if request:
                record.request_id = getattr(request, 'audit_request_id', '-')
                record.user = (
                    request.user.email
                    if hasattr(request, 'user') and request.user.is_authenticated
                    else 'anonymous'
                )
                record.ip = get_client_ip(request) or '-'
                record.method = getattr(request, 'method', '-')
                record.path = getattr(request, 'path', '-')
            else:
                record.request_id = '-'
                record.user = '-'
                record.ip = '-'
                record.method = '-'
                record.path = '-'
        except Exception:
            record.request_id = '-'
            record.user = '-'
            record.ip = '-'
            record.method = '-'
            record.path = '-'
        return True


class SkipHealthCheckFilter(logging.Filter):
    """Suprime logs de health-check endpoints para não poluir os logs."""

    SKIP_PATHS = {'/health/', '/ping/', '/favicon.ico'}

    def filter(self, record: logging.LogRecord) -> bool:
        path = getattr(record, 'path', '')
        return path not in self.SKIP_PATHS
