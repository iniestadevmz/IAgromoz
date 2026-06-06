from rest_framework.views import APIView
from rest_framework.response import Response
from api.models.audit import AuditLog
from api.serializers.audit import AuditLogSerializer
from api.permissions import IsAdmin


class AuditLogListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = AuditLog.objects.select_related('user').all()

        filters = {
            "user_email__icontains": request.query_params.get("user_email"),
            "action": request.query_params.get("action"),
            "resource__iexact": request.query_params.get("resource"),
            "resource_id": request.query_params.get("resource_id"),
            "status": request.query_params.get("status"),
            "source": request.query_params.get("source"),
            "request_id": request.query_params.get("request_id"),
        }

        for k, v in filters.items():
            if v:
                if k in ["action", "status", "source"]:
                    qs = qs.filter(**{k: v.upper()})
                else:
                    qs = qs.filter(**{k: v})

        if v := request.query_params.get("date"):
            qs = qs.filter(timestamp__date=v)

        if v := request.query_params.get("date_from"):
            qs = qs.filter(timestamp__date__gte=v)

        if v := request.query_params.get("date_to"):
            qs = qs.filter(timestamp__date__lte=v)

        serializer = AuditLogSerializer(qs[:500], many=True)
        return Response(serializer.data)