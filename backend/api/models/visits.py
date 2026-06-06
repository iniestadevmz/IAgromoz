from django.db import models
from django.conf import settings


class PageVisit(models.Model):
    """
    Records a unique visit per (ip_address, date).
    One row per IP per day — avoids counting every single GET request.
    """
    ip_address = models.GenericIPAddressField()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='page_visits'
    )
    path = models.CharField(max_length=255, blank=True)
    date = models.DateField()
    visit_count = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('ip_address', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.ip_address} — {self.date} ({self.visit_count} hits)"
