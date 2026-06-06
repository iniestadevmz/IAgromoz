from rest_framework_simplejwt.views import TokenObtainPairView
from api.serializers.token import CustomTokenObtainPairSerializer
import logging

logger = logging.getLogger("api.audit")


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    JWT login endpoint with audit trail.
    LOGIN and LOGIN_FAILED are logged here because at middleware level
    request.user is AnonymousUser — the token is being created.
    """
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        try:
            from api.services.audit_logger import log_action
            from api.models.audit import AuditLog
            from django.contrib.auth import get_user_model
            User = get_user_model()

            email = request.data.get("email", "")

            if response.status_code == 200:
                user = User.objects.filter(email=email).first()
                log_action(
                    user=user,
                    action=AuditLog.Action.LOGIN,
                    resource="Auth",
                    resource_id=str(user.pk) if user else "",
                    status=AuditLog.Status.SUCCESS,
                    detail=f"User '{email}' logged in successfully.",
                    request=request,
                )
                logger.info(f"[AuditLog] LOGIN SUCCESS: {email}")
            else:
                log_action(
                    user=None,
                    action=AuditLog.Action.LOGIN_FAILED,
                    resource="Auth",
                    resource_id="",
                    status=AuditLog.Status.FAILED,
                    detail=f"Failed login attempt for '{email}'.",
                    request=request,
                )
                logger.warning(f"[AuditLog] LOGIN FAILED: {email}")
        except Exception as e:
            logger.warning(f"[AuditLog] token view log failed: {e}")

        return response
