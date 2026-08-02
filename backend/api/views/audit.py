from rest_framework.views import APIView
from rest_framework.response import Response
from api.models.audit import AuditLog, SecurityLog
from api.serializers.audit import AuditLogSerializer, SecurityLogSerializer
from api.permissions import IsAdmin


class AuditLogListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = AuditLog.objects.select_related('user').all()

        filters = {
            'user_email__icontains': request.query_params.get('user_email'),
            'action': request.query_params.get('action'),
            'resource__iexact': request.query_params.get('resource'),
            'resource_id': request.query_params.get('resource_id'),
            'status': request.query_params.get('status'),
            'source': request.query_params.get('source'),
            'request_id': request.query_params.get('request_id'),
            'severity': request.query_params.get('severity'),
            'ip_address': request.query_params.get('ip_address'),
        }

        for k, v in filters.items():
            if v:
                if k in ('action', 'status', 'source', 'severity'):
                    qs = qs.filter(**{k: v.upper()})
                else:
                    qs = qs.filter(**{k: v})

        if v := request.query_params.get('date'):
            qs = qs.filter(timestamp__date=v)
        if v := request.query_params.get('date_from'):
            qs = qs.filter(timestamp__date__gte=v)
        if v := request.query_params.get('date_to'):
            qs = qs.filter(timestamp__date__lte=v)

        serializer = AuditLogSerializer(qs[:500], many=True)
        return Response(serializer.data)


class SecurityLogListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = SecurityLog.objects.select_related('user').all()

        if v := request.query_params.get('event_type'):
            qs = qs.filter(event_type=v.upper())
        if v := request.query_params.get('user_email'):
            qs = qs.filter(user_email__icontains=v)
        if v := request.query_params.get('ip_address'):
            qs = qs.filter(ip_address=v)
        if v := request.query_params.get('date_from'):
            qs = qs.filter(timestamp__date__gte=v)
        if v := request.query_params.get('date_to'):
            qs = qs.filter(timestamp__date__lte=v)

        serializer = SecurityLogSerializer(qs[:500], many=True)
        return Response(serializer.data)


class AuditStatsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        from api.services.audit_stats import get_audit_stats
        return Response(get_audit_stats())
