from django.db import models
from api.models.users import User
from api.models.techniques import Tecnica

class VotoTecnica(models.Model):
    VOTO_CHOICES = (
        ('APROVA', 'Aprova'),
        ('REPROVA', 'Reprova'),
    )

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    tecnica = models.ForeignKey(Tecnica, on_delete=models.CASCADE)
    voto = models.CharField(max_length=10, choices=VOTO_CHOICES)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'tecnica')  # 1 voto por usuário
