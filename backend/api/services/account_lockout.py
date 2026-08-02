"""
AccountLockoutService
=====================
Bloqueia contas após N tentativas de login falhadas.

Compatível com:
- LocMemCache (desenvolvimento)
- RedisCache (produção)

Se o backend suportar TTL (Redis), o tempo restante é devolvido.
Caso contrário, utiliza o tempo de bloqueio configurado.
"""

import logging
import time

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger("api.security")

LOCKOUT_MAX_ATTEMPTS = getattr(
    settings,
    "ACCOUNT_LOCKOUT_MAX_ATTEMPTS",
    5,
)

LOCKOUT_DURATION = getattr(
    settings,
    "ACCOUNT_LOCKOUT_DURATION_SECONDS",
    600,
)


def _attempts_key(email: str) -> str:
    return f"login_attempts:{email.lower()}"


def _lockout_key(email: str) -> str:
    return f"login_lockout:{email.lower()}"


def _lockout_time_key(email: str) -> str:
    return f"login_lockout_time:{email.lower()}"


def _get_retry_after(email: str) -> int:
    """
    Obtém os segundos restantes do bloqueio.

    Redis:
        usa TTL nativo.

    Outros caches:
        calcula pelo timestamp armazenado.
    """

    key = _lockout_key(email)

    if hasattr(cache, "ttl"):
        try:
            ttl = cache.ttl(key)
            if ttl and ttl > 0:
                return ttl
        except Exception:
            pass

    started = cache.get(_lockout_time_key(email))

    if not started:
        return 0

    remaining = LOCKOUT_DURATION - int(time.time() - started)

    return max(remaining, 0)


def record_failed_attempt(email: str) -> dict:
    """
    Regista tentativa falhada.
    """

    retry_after = _get_retry_after(email)

    if retry_after > 0:
        return {
            "locked": True,
            "attempts": LOCKOUT_MAX_ATTEMPTS,
            "retry_after": retry_after,
        }

    key_attempts = _attempts_key(email)
    key_lockout = _lockout_key(email)
    key_time = _lockout_time_key(email)

    attempts = cache.get(key_attempts, 0) + 1

    cache.set(
        key_attempts,
        attempts,
        timeout=LOCKOUT_DURATION,
    )

    if attempts >= LOCKOUT_MAX_ATTEMPTS:

        cache.set(
            key_lockout,
            True,
            timeout=LOCKOUT_DURATION,
        )

        cache.set(
            key_time,
            int(time.time()),
            timeout=LOCKOUT_DURATION,
        )

        cache.delete(key_attempts)

        logger.warning(
            "[AccountLockout] Account locked: %s for %ss",
            email,
            LOCKOUT_DURATION,
        )

        return {
            "locked": True,
            "attempts": attempts,
            "retry_after": LOCKOUT_DURATION,
        }

    return {
        "locked": False,
        "attempts": attempts,
        "retry_after": 0,
    }


def is_locked(email: str) -> dict:
    """
    Verifica se a conta está bloqueada.
    """

    retry_after = _get_retry_after(email)

    return {
        "locked": retry_after > 0,
        "retry_after": retry_after,
    }


def clear_lockout(email: str) -> None:
    """
    Remove o bloqueio após login com sucesso.
    """

    cache.delete(_attempts_key(email))
    cache.delete(_lockout_key(email))
    cache.delete(_lockout_time_key(email))


def lockout_error_response(retry_after: int) -> dict:

    minutes = retry_after // 60
    seconds = retry_after % 60

    if minutes:
        time_str = f"{minutes} minuto(s) e {seconds} segundo(s)"
    else:
        time_str = f"{seconds} segundo(s)"

    return {
        "error": "account_locked",
        "detail": (
            "Conta temporariamente bloqueada por demasiadas "
            f"tentativas falhadas. Tente novamente em {time_str}."
        ),
        "retry_after": retry_after,
    }