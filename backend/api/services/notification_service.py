"""
Notification Service
====================
Arquitectura Strategy/Adapter para envio de alertas.
Actualmente apenas log — sem integrações externas.

Para adicionar um canal (ex: Slack):
1. Criar SlackNotificationChannel(BaseNotificationChannel)
2. Registar em settings.NOTIFICATION_CHANNELS
"""
import logging
from typing import List
from dataclasses import dataclass

logger = logging.getLogger('api.notifications')


@dataclass
class NotificationEvent:
    event_type: str
    title: str
    detail: str
    user_email: str = ''
    ip_address: str = ''
    severity: str = 'LOW'
    extra: dict = None


class BaseNotificationChannel:
    """Interface base. Implementar para cada canal."""

    def send(self, event: NotificationEvent) -> None:
        raise NotImplementedError


class LogNotificationChannel(BaseNotificationChannel):
    """Canal de log — activo por defeito. Regista em vez de enviar."""

    def send(self, event: NotificationEvent) -> None:
        logger.info(
            f'[Notification] {event.severity} | {event.event_type} | '
            f'{event.user_email} | {event.detail}'
        )


# Canais preparados para implementação futura:
# class EmailNotificationChannel(BaseNotificationChannel): ...
# class SlackNotificationChannel(BaseNotificationChannel): ...
# class TelegramNotificationChannel(BaseNotificationChannel): ...
# class WebhookNotificationChannel(BaseNotificationChannel): ...
# class SMSNotificationChannel(BaseNotificationChannel): ...
# class PushNotificationChannel(BaseNotificationChannel): ...


def _get_channels() -> List[BaseNotificationChannel]:
    """Carrega canais configurados ou usa LogNotificationChannel."""
    try:
        from django.conf import settings
        channel_paths = getattr(settings, 'NOTIFICATION_CHANNELS', [])
        if not channel_paths:
            return [LogNotificationChannel()]
        from django.utils.module_loading import import_string
        return [import_string(p)() for p in channel_paths]
    except Exception:
        return [LogNotificationChannel()]


def dispatch_alert(event: NotificationEvent) -> None:
    """
    Dispara alerta para todos os canais configurados.
    Fail-safe — nunca bloqueia o request.
    """
    for channel in _get_channels():
        try:
            channel.send(event)
        except Exception as exc:
            logger.warning(f'[Notification] Channel {channel.__class__.__name__} failed: {exc}')


# ─────────────────────────────────────────────────────────────────────────────
# Helpers para eventos específicos
# ─────────────────────────────────────────────────────────────────────────────

def alert_login_failed(user_email: str, ip: str, count: int = 1) -> None:
    dispatch_alert(NotificationEvent(
        event_type='LOGIN_FAILED',
        title='Tentativa de login falhada',
        detail=f'{count} tentativa(s) falhada(s) para {user_email}',
        user_email=user_email,
        ip_address=ip,
        severity='MEDIUM',
    ))


def alert_role_changed(user_email: str, old_role: str, new_role: str, by_email: str) -> None:
    dispatch_alert(NotificationEvent(
        event_type='ROLE_CHANGED',
        title='Role alterado',
        detail=f'{user_email}: {old_role} → {new_role} por {by_email}',
        user_email=user_email,
        severity='HIGH',
    ))


def alert_permission_denied(user_email: str, ip: str, path: str) -> None:
    dispatch_alert(NotificationEvent(
        event_type='PERMISSION_DENIED',
        title='Acesso negado',
        detail=f'{user_email} tentou aceder {path}',
        user_email=user_email,
        ip_address=ip,
        severity='MEDIUM',
    ))
