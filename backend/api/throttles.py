"""
Rate limiting usando django-ratelimit.

Instalar: pip install django-ratelimit==4.1.0

Fornece decoradores para aplicar limites por IP ou utilizador.
O estado é guardado no cache do Django (memory em dev, Redis em prod).
"""
from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited
from rest_framework.response import Response
from rest_framework import status
import functools


def rate_limit(key='ip', rate='5/m', method='POST', block=True):
    """
    Decorador reutilizável que envolve uma view DRF com django-ratelimit.

    Parâmetros:
        key    — 'ip' (por IP) ou 'user' (por utilizador autenticado)
        rate   — ex: '5/m' (5/min), '100/h' (100/hora), '1000/d' (1000/dia)
        method — método HTTP a limitar ('POST', 'GET', 'ALL')
        block  — True devolve 429 automaticamente; False só marca request.limited
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapped(instance, request, *args, **kwargs):
            # django-ratelimit espera um HttpRequest normal do Django
            limited_func = ratelimit(key=key, rate=rate, method=method, block=block)(
                lambda req: None
            )
            try:
                limited_func(request)
            except Ratelimited:
                return Response(
                    {"detail": "Demasiadas tentativas. Tente novamente mais tarde."},
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )
            return view_func(instance, request, *args, **kwargs)
        return wrapped
    return decorator


# Atalhos prontos a usar nas views
login_rate_limit      = rate_limit(key='ip', rate='5/m',   method='POST')
chat_ai_rate_limit    = rate_limit(key='ip', rate='20/m',  method='POST')
google_auth_rate_limit = rate_limit(key='ip', rate='10/m', method='POST')
api_anon_rate_limit   = rate_limit(key='ip', rate='30/m',  method='ALL')
api_user_rate_limit   = rate_limit(key='user', rate='120/m', method='ALL')
