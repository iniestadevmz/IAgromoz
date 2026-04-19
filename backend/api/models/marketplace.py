from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg

User = settings.AUTH_USER_MODEL

class PedidoVendedor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    contacto = models.CharField(max_length=50)
    mensagem = models.TextField(blank=True)
    
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('APROVADO', 'Aprovado'),
        ('REJEITADO', 'Rejeitado'),
    ]

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='PENDENTE'
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    analisado_em = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.status}"



class Produto(models.Model):
    CATEGORIAS = [
        ('insumos', 'Insumos'),
        ('equipamentos', 'Equipamentos'),
        ('sementes', 'Sementes'),
        ('fertilizantes', 'Fertilizantes'),
        ('defensivos', 'Defensivos'),
        ('animais', 'Animais'),
        ('frescos', 'Produtos Frescos'),
    ]

    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    foto = models.ImageField(upload_to='iagromoz/produtos/')
    vendedor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='produtos')
    criado_em = models.DateTimeField(auto_now_add=True)
    categoria = models.CharField(max_length=100, choices=CATEGORIAS, blank=True)

    def __str__(self):
        return f"{self.nome} - {self.vendedor}"

    # Avaliação do Produto
    def media_avaliacao_produto(self):
        return self.avaliacoes_produto.aggregate(media=Avg('nota'))['media'] or 0

    def total_avaliacoes_produto(self):
        return self.avaliacoes_produto.count()


class Avaliacao(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)

    produto = models.ForeignKey(
        Produto,
        on_delete=models.CASCADE,
        related_name='avaliacoes_produto',
        null=True,
        blank=True
    )
    vendedor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='avaliacoes_vendedor',
        null=True,
        blank=True
    )

    nota = models.FloatField(validators=[MinValueValidator(1.0), MaxValueValidator(5.0)])
    comentario = models.TextField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'produto', 'vendedor')  # evita duplicadas

    def __str__(self):
        if self.produto:
            return f"{self.usuario} avaliou Produto {self.produto} - {self.nota}★"
        if self.vendedor:
            return f"{self.usuario} avaliou Vendedor {self.vendedor} - {self.nota}★"
        return f"Avaliação {self.id} sem alvo definido"


def media_avaliacao_vendedor(user):
    return user.avaliacoes_vendedor.aggregate(media=Avg('nota'))['media'] or 0

def total_avaliacoes_vendedor(user):
    return user.avaliacoes_vendedor.count()