from django.apps import AppConfig


class ApiConfig(AppConfig):
    name = 'api'

    def ready(self):
        
        import api.signals.audit_signals
        import api.signals.notifications_signals
