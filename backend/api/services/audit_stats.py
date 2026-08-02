"""
AuditStatsService
=================
Estatísticas para o dashboard de auditoria.
"""
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count


def get_audit_stats() -> dict:
    from api.models.audit import AuditLog, SecurityLog

    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total_requests = AuditLog.objects.filter(action='REQUEST').count()
    total_logins = AuditLog.objects.filter(action='LOGIN').count()
    failed_logins = AuditLog.objects.filter(action='LOGIN_FAILED').count()
    requests_today = AuditLog.objects.filter(action='REQUEST', timestamp__gte=today_start).count()
    security_events = SecurityLog.objects.count()

    top_ips = (
        AuditLog.objects
        .exclude(ip_address=None)
        .values('ip_address')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )

    top_endpoints = (
        AuditLog.objects
        .filter(action='REQUEST')
        .exclude(path='')
        .values('path')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )

    recent_security = SecurityLog.objects.order_by('-timestamp')[:20]
    recent_data = [
        {
            'event_type': s.event_type,
            'user_email': s.user_email,
            'ip_address': str(s.ip_address or ''),
            'timestamp': s.timestamp.isoformat(),
        }
        for s in recent_security
    ]

    return {
        'total_requests': total_requests,
        'total_logins': total_logins,
        'failed_logins': failed_logins,
        'requests_today': requests_today,
        'security_events': security_events,
        'top_ips': list(top_ips),
        'top_endpoints': list(top_endpoints),
        'recent_security_events': recent_data,
    }
