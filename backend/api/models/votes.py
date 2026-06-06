from django.db import models
from api.models.users import User
from api.models.techniques import Technique


class TechniqueVote(models.Model):
    VOTE_CHOICES = (
        ('APPROVE', 'Aprova'),
        ('REJECT', 'Reprova'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    technique = models.ForeignKey(Technique, on_delete=models.CASCADE)
    vote = models.CharField(max_length=10, choices=VOTE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'technique')
