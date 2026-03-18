from django.db import models
from django.conf import settings

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
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    foto = models.ImageField(upload_to='produtos/')
    vendedor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='produtos')
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome} - {self.vendedor}"

