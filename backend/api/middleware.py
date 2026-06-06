"""
Middleware
==========
AuditMiddleware:
  - Stores request in thread-local (so signals can access IP/user-agent/user)
  - Attaches audit_request_id to every request
  - Tracks unique daily page visits per IP in PageVisit (GET requests only)

LOGIN/LOGOUT audit logs → handled in views (token.py / auth.py)
CREATE/UPDATE/DELETE audit logs → handled by signals (post_save / pre_delete)
"""

import uuid
import threading
import logging

logger = logging.getLogger("api.audit")

_thread_local = threading.local()

SKIP_PATHS = ["/admin/", "/static/", "/media/"]


def get_current_request():
    """Return the current HTTP request stored by AuditMiddleware, or None."""
    return getattr(_thread_local, "request", None)


def get_client_ip(request):
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class AuditMiddleware:
    """
    1. Stores request in thread-local so signals can read IP/user-agent/user.
    2. Attaches audit_request_id to every request.
    3. Tracks unique daily visits per IP in PageVisit (GET requests only).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Store request BEFORE processing so signals have access
        _thread_local.request = request
        request.audit_request_id = str(uuid.uuid4())

        try:
            response = self.get_response(request)
        finally:
            # Always clean up to prevent leaking to next request on same thread
            _thread_local.request = None

        if any(request.path.startswith(p) for p in SKIP_PATHS):
            return response

        if response.status_code >= 400:
            return response

        # Track unique daily page visits (GET only)
        if request.method == "GET":
            try:
                from api.models.visits import PageVisit
                from django.db.models import F
                from django.utils.timezone import now as tz_now

                ip = get_client_ip(request)
                user = request.user if request.user.is_authenticated else None
                today = tz_now().date()

                obj, created = PageVisit.objects.get_or_create(
                    ip_address=ip,
                    date=today,
                    defaults={"user": user, "path": request.path}
                )
                if not created:
                    PageVisit.objects.filter(pk=obj.pk).update(
                        visit_count=F("visit_count") + 1
                    )
            except Exception as e:
                logger.debug(f"[PageVisit] Failed to record visit: {e}")

        return response
