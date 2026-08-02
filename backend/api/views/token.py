from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework import status
from api.serializers.token import CustomTokenObtainPairSerializer
from api.throttles import login_rate_limit
from api.services.account_lockout import is_locked, record_failed_attempt, clear_lockout, lockout_error_response
import logging

logger = logging.getLogger("api.audit")


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    JWT login endpoint com audit trail, rate limiting e bloqueio de conta.
    - Rate limit: 5 tentativas/min por IP
    - Bloqueio de conta: 5 tentativas falhadas → 10 minutos de bloqueio
    """
    serializer_class = CustomTokenObtainPairSerializer

    @login_rate_limit
    def post(self, request, *args, **kwargs):
        email = request.data.get('email', '').strip().lower()

        # Verificar bloqueio antes de processar
        if email:
            lock_status = is_locked(email)
            if lock_status['locked']:
                return Response(
                    lockout_error_response(lock_status['retry_after']),
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )

        response = super().post(request, *args, **kwargs)

        try:
            from api.services.audit_logger import log_action
            from api.models.audit import AuditLog
            from django.contrib.auth import get_user_model
            User = get_user_model()

            if response.status_code == 200:
                user = User.objects.filter(email=email).first()
                # Login bem-sucedido — limpar bloqueio
                if email:
                    clear_lockout(email)
                log_action(
                    user=user,
                    action=AuditLog.Action.LOGIN,
                    resource='Auth',
                    resource_id=str(user.pk) if user else '',
                    status=AuditLog.Status.SUCCESS,
                    detail=f"User '{email}' logged in successfully.",
                    request=request,
                )
            else:
                # Falha — registar tentativa e verificar bloqueio
                if email:
                    lock_result = record_failed_attempt(email)
                    if lock_result['locked']:
                        log_action(
                            user=None,
                            action='LOGIN_FAILED',
                            resource='Auth',
                            resource_id='',
                            status='FAILED',
                            severity='HIGH',
                            detail=f"Account locked after {lock_result['attempts']} failed attempts for '{email}'.",
                            request=request,
                        )
                        return Response(
                            lockout_error_response(lock_result['retry_after']),
                            status=status.HTTP_429_TOO_MANY_REQUESTS,
                        )

                log_action(
                    user=None,
                    action=AuditLog.Action.LOGIN_FAILED,
                    resource='Auth',
                    resource_id='',
                    status=AuditLog.Status.FAILED,
                    detail=f"Failed login attempt for '{email}'.",
                    request=request,
                )
        except Exception as e:
            logger.warning(f"[AuditLog] token view log failed: {e}")

        return response
