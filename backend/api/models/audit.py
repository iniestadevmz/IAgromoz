import uuid
from django.db import models
from django.conf import settings


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

    class Status(models.TextChoices):
        SUCCESS = 'SUCCESS', 'Success'
        FAILED  = 'FAILED', 'Failed'

    class Source(models.TextChoices):
        API   = 'API', 'API'
        WEB   = 'WEB', 'Web'
        ADMIN = 'ADMIN', 'Admin'

    class Severity(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        CRITICAL = 'CRITICAL', 'Critical'

    # WHO
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    user_email = models.EmailField(blank=True)

    # WHAT
    action = models.CharField(max_length=20, choices=Action.choices)
    resource = models.CharField(max_length=100, blank=True)

    resource_id = models.CharField(
        max_length=100,
        blank=True,
        db_index=True
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.SUCCESS
    )

    severity = models.CharField(
        max_length=10,
        choices=Severity.choices,
        default=Severity.LOW,
        db_index=True
    )

    detail = models.TextField(blank=True)

    # STATE
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)

    # CONTEXT
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        db_index=True
    )

    user_agent = models.TextField(blank=True)

    source = models.CharField(
        max_length=10,
        choices=Source.choices,
        default=Source.API
    )

    request_id = models.CharField(
        max_length=64,
        blank=True,
        db_index=True
    )

    # HTTP context (importante para debugging)
    http_method = models.CharField(max_length=10, blank=True)
    path = models.TextField(blank=True)
    query_params = models.JSONField(null=True, blank=True)

    # WHEN
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['resource', 'resource_id']),
            models.Index(fields=['severity', 'timestamp']),
        ]

    def __str__(self):
        return (
            f"[{self.timestamp:%Y-%m-%d %H:%M:%S}] "
            f"{self.user_email or 'anonymous'} | "
            f"{self.action} {self.resource} {self.resource_id} | "
            f"{self.status}"
        )