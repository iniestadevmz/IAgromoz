from rest_framework import serializers
from api.models.audit import AuditLog, SecurityLog


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = [
            'id', 'user_email', 'action', 'resource', 'resource_id',
            'status', 'severity', 'detail', 'before', 'after',
            'ip_address', 'user_agent', 'source', 'request_id',
            'http_method', 'path',
            'browser', 'operating_system', 'device_type',
            'current_hash', 'previous_hash',
            'timestamp',
        ]


class SecurityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecurityLog
        fields = [
            'id', 'user_email', 'event_type', 'ip_address',
            'user_agent', 'detail', 'extra', 'request_id',
            'source', 'timestamp',
        ]
