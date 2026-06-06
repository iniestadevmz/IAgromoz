from rest_framework import serializers
from api.models.audit import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = [
            'id', 'user_email', 'action', 'resource', 'resource_id',
            'status', 'detail', 'before', 'after','severity',
            'ip_address', 'user_agent', 'source', 'request_id', 'timestamp',
        ]
