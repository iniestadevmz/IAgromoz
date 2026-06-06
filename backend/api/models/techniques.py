from django.db import models
from api.models.users import User


class Technique(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pendente'),
        ('VALIDATED', 'Validada'),
        ('DISCARDED', 'Descartada'),
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='techniques')
    approval_votes = models.PositiveIntegerField(default=0)
    rejection_votes = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='iagromoz/techniques/', null=True, blank=True)

    def total_votes(self):
        return self.approval_votes + self.rejection_votes

    def evaluate(self):
        total = self.total_votes()
        if total < 100:
            return
        approval_pct = (self.approval_votes / total) * 100
        rejection_pct = (self.rejection_votes / total) * 100
        if approval_pct >= 80:
            self.status = 'VALIDATED'
        elif rejection_pct >= 20:
            self.status = 'DISCARDED'
        self.save()

    def __str__(self):
        return self.title
