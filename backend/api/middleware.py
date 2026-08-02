"""
Middleware
==========
AuditMiddleware:

- Stores request in thread-local
- Generates request_id
- Captures real client IP
- Captures User-Agent
- Logs all HTTP requests
- Tracks unique daily visits

Authentication events:
    handled by Django signals

CRUD events:
    handled by model signals
"""


import uuid
import threading
import logging
import ipaddress


logger = logging.getLogger("api.audit")


_thread_local = threading.local()


# Não ignorar admin para auditoria
SKIP_PATHS = [
    "/static/",
    "/media/",
]



def get_current_request():
    return getattr(
        _thread_local,
        "request",
        None
    )



def get_client_ip(request):

    """
    Resolve client IP.

    Priority:

    1. X-Real-IP (Nginx)
    2. X-Forwarded-For
    3. REMOTE_ADDR

    """

    if request is None:
        return None



    real_ip = request.META.get(
        "HTTP_X_REAL_IP"
    )

    if real_ip:
        return real_ip.strip()



    forwarded = request.META.get(
        "HTTP_X_FORWARDED_FOR"
    )


    if forwarded:

        ips = [
            ip.strip()
            for ip in forwarded.split(",")
        ]


        for ip in reversed(ips):

            try:

                addr = ipaddress.ip_address(ip)


                if (
                    not addr.is_private
                    and not addr.is_loopback
                ):
                    return ip


            except ValueError:
                continue



        return ips[0]



    return request.META.get(
        "REMOTE_ADDR",
        ""
    )




class AuditMiddleware:


    def __init__(self, get_response):

        self.get_response = get_response



    def __call__(self, request):


        request.audit_request_id = str(
            uuid.uuid4()
        )


        _thread_local.request = request



        try:

            response = self.get_response(request)



        finally:

            _thread_local.request = None




        # ================================
        # Audit HTTP Request
        # ================================


        if not any(
            request.path.startswith(path)
            for path in SKIP_PATHS
        ):

            try:

                from api.services.audit_logger import log_action



                user = None


                if (
                    hasattr(request, "user")
                    and request.user.is_authenticated
                ):
                    user = request.user



                log_action(

                    action="REQUEST",

                    user=user,

                    resource="HTTP",

                    request=request,

                    status=(

                        "SUCCESS"

                        if response.status_code < 400

                        else "FAILED"

                    ),

                    severity=(

                        "LOW"

                        if response.status_code < 400

                        else "MEDIUM"

                    ),


                    detail=(

                        f"{request.method} "
                        f"{request.path} "
                        f"{response.status_code}"

                    ),


                    source=(

                        "ADMIN"

                        if request.path.startswith(
                            "/admin/"
                        )

                        else "API"

                    )

                )


            except Exception as e:

                logger.debug(
                    f"[AuditRequest] Failed: {e}"
                )



        # ================================
        # Page Visit Tracking
        # ================================


        if (
            response.status_code < 400
            and request.method == "GET"
            and not any(
                request.path.startswith(p)
                for p in SKIP_PATHS
            )
        ):

            try:

                from api.models.visits import PageVisit
                from django.db.models import F
                from django.utils.timezone import now


                ip = get_client_ip(request)


                user = (

                    request.user

                    if request.user.is_authenticated

                    else None

                )


                today = now().date()



                obj, created = PageVisit.objects.get_or_create(

                    ip_address=ip,

                    date=today,

                    defaults={

                        "user": user,

                        "path": request.path

                    }

                )



                if not created:

                    PageVisit.objects.filter(
                        pk=obj.pk
                    ).update(

                        visit_count=F(
                            "visit_count"
                        ) + 1

                    )


            except Exception as e:

                logger.debug(
                    f"[PageVisit] Failed: {e}"
                )



        return response