"""
AccountLockoutService
=====================
Bloqueia contas após N tentativas de login falhadas.
Usa Django cache (memória local em dev, Redis em prod).
Duração configurável via settings.ACCOUNT_LOCKOUT_DURATION_SECONDS (default 600s = 10 min).
"""
import logging
from datetime import datetime
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger('api.security')

LOCKOUT_MAX_ATTEMPTS = getattr(settings, 'ACCOUNT_LOCKOUT_MAX_ATTEMPTS', 5)
LOCKOUT_DURATION = getattr(settings, 'ACCOUNT_LOCKOUT_DURATION_SECONDS', 600)


def _attempts_key(email: str) -> str:
    return f'login_attempts:{email.lower()}'


def _lockout_key(email: str) -> str:
    return f'login_lockout:{email.lower()}'


def record_failed_attempt(email: str) -> dict:
    """
    Regista uma tentativa falhada para o email.
    Retorna {'locked': bool, 'attempts': int, 'retry_after': int}.
    retry_after: segundos até poder tentar novamente.
    """
    key_attempts = _attempts_key(email)
    key_lockout = _lockout_key(email)

    # Já está bloqueado?
    ttl = cache.ttl(key_lockout)
    if ttl and ttl > 0:
        return {'locked': True, 'attempts': LOCKOUT_MAX_ATTEMPTS, 'retry_after': ttl}

    # Incrementar tentativas
    attempts = cache.get(key_attempts, 0) + 1
    cache.set(key_attempts, attempts, timeout=LOCKOUT_DURATION)

    if attempts >= LOCKOUT_MAX_ATTEMPTS:
        cache.set(key_lockout, True, timeout=LOCKOUT_DURATION)
        cache.delete(key_attempts)
        logger.warning(f'[AccountLockout] Account locked: {email} for {LOCKOUT_DURATION}s')
        return {'locked': True, 'attempts': attempts, 'retry_after': LOCKOUT_DURATION}

    return {'locked': False, 'attempts': attempts, 'retry_after': 0}


def is_locked(email: str) -> dict:
    """
    Verifica se o email está bloqueado.
    Retorna {'locked': bool, 'retry_after': int (segundos restantes)}.
    """
    key_lockout = _lockout_key(email)
    ttl = cache.ttl(key_lockout)
    if ttl and ttl > 0:
        return {'locked': True, 'retry_after': ttl}
    return {'locked': False, 'retry_after': 0}


def clear_lockout(email: str) -> None:
    """Limpa o bloqueio após login bem-sucedido."""
    cache.delete(_attempts_key(email))
    cache.delete(_lockout_key(email))


def lockout_error_response(retry_after: int) -> dict:
    """Mensagem de erro padronizada com tempo restante."""
    minutes = retry_after // 60
    seconds = retry_after % 60
    if minutes > 0:
        time_str = f'{minutes} minuto(s) e {seconds} segundo(s)'
    else:
        time_str = f'{seconds} segundo(s)'
    return {
        'error': 'account_locked',
        'detail': f'Conta temporariamente bloqueada por demasiadas tentativas falhadas. '
                  f'Tente novamente em {time_str}.',
        'retry_after': retry_after,
    }
