from django.db import models
from api.models.users import User

class Tecnica(models.Model):
    STATUS_CHOICES = (
        ('PENDENTE', 'Pendente'),
        ('VALIDADA', 'Validada'),
        ('DESCARTADA', 'Descartada'),
    )

    titulo = models.CharField(max_length=200)
    descricao = models.TextField()

    criada_por = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tecnicas'
    )

    votos_aprovacao = models.PositiveIntegerField(default=0)
    votos_rejeicao = models.PositiveIntegerField(default=0)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDENTE'
    )

    criada_em = models.DateTimeField(auto_now_add=True)

    def total_votos(self):
        return self.votos_aprovacao + self.votos_rejeicao

    def avaliar_tecnica(self):
        """
        Aplica a regra 80/20 quando total >= 100
        """
        total = self.total_votos()

        if total < 100:
            return  # ainda não decide

        percent_aprovacao = (self.votos_aprovacao / total) * 100
        percent_rejeicao = (self.votos_rejeicao / total) * 100

        if percent_aprovacao >= 80:
            self.status = 'VALIDADA'
        elif percent_rejeicao >= 20:
            self.status = 'DESCARTADA'

        self.save()

    def __str__(self):
        return self.titulo
