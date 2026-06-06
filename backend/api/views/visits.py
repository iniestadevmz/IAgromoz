from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers
from django.db.models import Sum, Count
from django.utils.timezone import now
from datetime import timedelta
from api.models.visits import PageVisit
from api.permissions import IsAdmin


class PageVisitSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True, allow_null=True)

    class Meta:
        model = PageVisit
        fields = ['id', 'ip_address', 'user_email', 'path', 'date', 'visit_count']


class PageVisitListView(APIView):
    """
    GET /page-visits/
    Returns page visit records. Admin only.

    Query filters:
      ?date=YYYY-MM-DD          — exact date
      ?date_from=YYYY-MM-DD     — from date
      ?date_to=YYYY-MM-DD       — to date
      ?ip=<ip_address>          — filter by IP
      ?summary=true             — return daily totals instead of raw rows

    Summary response (?summary=true):
      [{"date": "2026-04-01", "unique_ips": 45, "total_hits": 320}, ...]

    Raw response:
      [{"id": 1, "ip_address": "...", "user_email": "...",
        "path": "/api/...", "date": "2026-04-01", "visit_count": 7}, ...]
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = PageVisit.objects.select_related('user').all()

        if v := request.query_params.get('date'):
            qs = qs.filter(date=v)
        if v := request.query_params.get('date_from'):
            qs = qs.filter(date__gte=v)
        if v := request.query_params.get('date_to'):
            qs = qs.filter(date__lte=v)
        if v := request.query_params.get('ip'):
            qs = qs.filter(ip_address=v)

        # Summary mode — aggregate by day
        if request.query_params.get('summary') == 'true':
            summary = (
                qs.values('date')
                .annotate(
                    unique_ips=Count('ip_address'),
                    total_hits=Sum('visit_count'),
                )
                .order_by('-date')
            )
            return Response([
                {
                    "date": str(r['date']),
                    "unique_ips": r['unique_ips'],
                    "total_hits": r['total_hits'],
                }
                for r in summary
            ])

        serializer = PageVisitSerializer(qs[:500], many=True)
        return Response(serializer.data)
