"""
ExceptionLoggingMiddleware
==========================
Captura TODAS as excepções não tratadas, regista com traceback completo
e volta a lançar — nunca engole o erro, deixa o Django tratá-lo normalmente.

Garante que erros 500 aparecem em:
  - console (stdout → Gunicorn → systemd → journalctl)
  - logs/error.log
"""
import logging
import time

from django.db import ProgrammingError, IntegrityError
from django.core.exceptions import ValidationError, PermissionDenied, ObjectDoesNotExist
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger('api.exceptions')


class ExceptionLoggingMiddleware:
    """
    Regista excepções não tratadas com contexto completo.
    Sempre relança — nunca return Response().
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        try:
            response = self.get_response(request)
            return response
        except Exception as exc:
            duration = (time.monotonic() - start) * 1000
            self._log_exception(request, exc, duration)
            raise  # sempre relança

    def _log_exception(self, request, exc: Exception, duration_ms: float) -> None:
        request_id = getattr(request, 'audit_request_id', '-')
        user = '-'
        if hasattr(request, 'user') and request.user.is_authenticated:
            user = request.user.email

        try:
            from api.middleware import get_client_ip
            ip = get_client_ip(request) or '-'
        except Exception:
            ip = request.META.get('REMOTE_ADDR', '-')

        severity = self._get_severity(exc)
        log_fn = logger.critical if severity == 'CRITICAL' else logger.exception

        log_fn(
            f'[{severity}] {exc.__class__.__name__}: {exc} | '
            f'req={request_id} user={user} ip={ip} '
            f'{request.method} {request.path} ({duration_ms:.1f}ms)',
            exc_info=True,
            extra={
                'request_id': request_id,
                'user': user,
                'ip': ip,
                'method': request.method,
                'path': request.path,
            }
        )

    @staticmethod
    def _get_severity(exc: Exception) -> str:
        if isinstance(exc, (ProgrammingError, IntegrityError)):
            return 'CRITICAL'
        if isinstance(exc, (PermissionDenied, AuthenticationFailed)):
            return 'WARNING'
        if isinstance(exc, (ValidationError, ValueError, ObjectDoesNotExist)):
            return 'ERROR'
        return 'ERROR'
