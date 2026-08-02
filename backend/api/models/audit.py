import uuid
import hashlib
import json
from django.db import models
from django.conf import settings


# ─────────────────────────────────────────────────────────────────────────────
# Sensitive fields excluded from snapshots
# ─────────────────────────────────────────────────────────────────────────────
SENSITIVE_FIELDS = {
    'password', 'token', 'jwt', 'secret', 'api_key',
    'refresh_token', 'access_token', 'id_token', 'google_id',
}


class AuditLog(models.Model):

    class Action(models.TextChoices):
        CREATE           = 'CREATE', 'Create'
        UPDATE           = 'UPDATE', 'Update'
        DELETE           = 'DELETE', 'Delete'
        LOGIN            = 'LOGIN', 'Login'
        LOGOUT           = 'LOGOUT', 'Logout'
        LOGIN_FAILED     = 'LOGIN_FAILED', 'Login Failed'
        UPGRADE_REQUEST  = 'UPGRADE_REQUEST', 'Upgrade Request'
        UPGRADE_APPROVED = 'UPGRADE_APPROVED', 'Upgrade Approved'
        UPGRADE_REJECTED = 'UPGRADE_REJECTED', 'Upgrade Rejected'
        VIEW             = 'VIEW', 'View'
        SECURITY_EVENT   = 'SECURITY_EVENT', 'Security Event'
        REQUEST          = 'REQUEST', 'HTTP Request'
        ROLE_CHANGED     = 'ROLE_CHANGED', 'Role Changed'
        PASSWORD_CHANGED = 'PASSWORD_CHANGED', 'Password Changed'
        PERMISSION_DENIED = 'PERMISSION_DENIED', 'Permission Denied'

    class Status(models.TextChoices):
        SUCCESS = 'SUCCESS', 'Success'
        FAILED  = 'FAILED', 'Failed'

    class Source(models.TextChoices):
        API   = 'API', 'API'
        WEB   = 'WEB', 'Web'
        ADMIN = 'ADMIN', 'Admin'

    class Severity(models.TextChoices):
        LOW      = 'LOW',      'Low'
        MEDIUM   = 'MEDIUM',   'Medium'
        HIGH     = 'HIGH',     'High'
        CRITICAL = 'CRITICAL', 'Critical'

    # WHO
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='audit_logs'
    )
    user_email = models.EmailField(blank=True)

    # WHAT
    action     = models.CharField(max_length=30, choices=Action.choices)
    resource   = models.CharField(max_length=100, blank=True)
    resource_id = models.CharField(max_length=100, blank=True, db_index=True)
    status     = models.CharField(max_length=10, choices=Status.choices, default=Status.SUCCESS)
    severity   = models.CharField(max_length=10, choices=Severity.choices, default=Severity.LOW, db_index=True)
    detail     = models.TextField(blank=True)

    # STATE — sensitive fields auto-excluded
    before = models.JSONField(null=True, blank=True)
    after  = models.JSONField(null=True, blank=True)

    # CONTEXT
    ip_address  = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    user_agent  = models.TextField(blank=True)
    source      = models.CharField(max_length=10, choices=Source.choices, default=Source.API)
    request_id  = models.CharField(max_length=64, blank=True, db_index=True)
    http_method = models.CharField(max_length=10, blank=True)
    path        = models.TextField(blank=True)
    query_params = models.JSONField(null=True, blank=True)

    # DEVICE
    browser          = models.CharField(max_length=100, blank=True)
    operating_system = models.CharField(max_length=100, blank=True)
    device_type      = models.CharField(max_length=20, blank=True)  # mobile/tablet/desktop

    # INTEGRITY — chained hash
    previous_hash = models.CharField(max_length=64, blank=True)
    current_hash  = models.CharField(max_length=64, blank=True, db_index=True)

    # WHEN
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['resource', 'resource_id']),
            models.Index(fields=['severity', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
        ]

    def __str__(self):
        return (
            f"[{self.timestamp:%Y-%m-%d %H:%M:%S}] "
            f"{self.user_email or 'anonymous'} | "
            f"{self.action} {self.resource} {self.resource_id} | "
            f"{self.status}"
        )

    def compute_hash(self) -> str:
        payload = json.dumps({
            'id': self.pk,
            'user_email': self.user_email,
            'action': self.action,
            'resource': self.resource,
            'resource_id': self.resource_id,
            'status': self.status,
            'ip_address': str(self.ip_address or ''),
            'timestamp': str(self.timestamp),
            'previous_hash': self.previous_hash,
        }, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()


class SecurityLog(models.Model):
    """
    Dedicated log for security-sensitive events.
    Separate from AuditLog to allow different retention and alerting policies.
    """

    class EventType(models.TextChoices):
        LOGIN              = 'LOGIN', 'Login'
        LOGIN_FAILED       = 'LOGIN_FAILED', 'Login Failed'
        LOGOUT             = 'LOGOUT', 'Logout'
        TOKEN_INVALID      = 'TOKEN_INVALID', 'Token Invalid'
        TOKEN_EXPIRED      = 'TOKEN_EXPIRED', 'Token Expired'
        PERMISSION_DENIED  = 'PERMISSION_DENIED', 'Permission Denied'
        ACCOUNT_LOCKED     = 'ACCOUNT_LOCKED', 'Account Locked'
        PASSWORD_CHANGED   = 'PASSWORD_CHANGED', 'Password Changed'
        PASSWORD_RESET     = 'PASSWORD_RESET', 'Password Reset'
        GOOGLE_LOGIN       = 'GOOGLE_LOGIN', 'Google Login'
        GOOGLE_LINKED      = 'GOOGLE_LINKED', 'Google Linked'
        SESSION_REVOKED    = 'SESSION_REVOKED', 'Session Revoked'
        ROLE_CHANGED       = 'ROLE_CHANGED', 'Role Changed'
        SUSPICIOUS_ACTIVITY = 'SUSPICIOUS_ACTIVITY', 'Suspicious Activity'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='security_logs'
    )
    user_email    = models.EmailField(blank=True, db_index=True)
    event_type    = models.CharField(max_length=30, choices=EventType.choices, db_index=True)
    ip_address    = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    user_agent    = models.TextField(blank=True)
    detail        = models.TextField(blank=True)
    extra         = models.JSONField(null=True, blank=True)
    request_id    = models.CharField(max_length=64, blank=True)
    source        = models.CharField(max_length=10, default='API')
    timestamp     = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user_email', 'timestamp']),
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
        ]

    def __str__(self):
        return f"[{self.timestamp:%Y-%m-%d %H:%M:%S}] {self.event_type} — {self.user_email or 'anonymous'}"
