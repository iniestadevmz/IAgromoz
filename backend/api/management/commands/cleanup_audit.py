"""
python manage.py cleanup_audit

Retention policy:
  Request/HTTP logs  → 90 days
  Security logs      → 365 days
  Critical logs      → never deleted
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Remove audit logs according to retention policy'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Show counts without deleting')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()

        from api.models.audit import AuditLog, SecurityLog

        # REQUEST logs — 90 days
        cutoff_request = now - timedelta(days=90)
        request_qs = AuditLog.objects.filter(
            action='REQUEST',
            timestamp__lt=cutoff_request,
        )
        self._delete(request_qs, 'REQUEST logs (90d)', dry_run)

        # Non-critical AuditLog — 180 days
        cutoff_audit = now - timedelta(days=180)
        audit_qs = AuditLog.objects.filter(
            timestamp__lt=cutoff_audit,
        ).exclude(severity='CRITICAL')
        self._delete(audit_qs, 'Non-critical AuditLog (180d)', dry_run)

        # SecurityLog — 365 days
        cutoff_security = now - timedelta(days=365)
        security_qs = SecurityLog.objects.filter(
            timestamp__lt=cutoff_security,
        ).exclude(event_type__in=['ROLE_CHANGED', 'ACCOUNT_LOCKED'])
        self._delete(security_qs, 'SecurityLog (365d)', dry_run)

        self.stdout.write(self.style.SUCCESS('cleanup_audit complete'))

    def _delete(self, qs, label, dry_run):
        count = qs.count()
        if dry_run:
            self.stdout.write(f'[DRY-RUN] Would delete {count} {label}')
        else:
            qs.delete()
            self.stdout.write(f'Deleted {count} {label}')
