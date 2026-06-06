import uuid
from django.db import models
from api.models.marketplace import Transaction


class Payment(models.Model):
    METHOD_CHOICES = [
        ('MPESA', 'M-Pesa'),
        ('EMOLA', 'e-Mola'),
        ('CARD',  'Cartão'),
        ('BANK',  'Transferência Bancária'),
    ]
    PROVIDER_CHOICES = [
        ('PAYSUITE',      'PaySuite'),
        ('E2PAYMENTS',    'E2Payments'),
        ('DIRECT_MPESA',  'M-Pesa Direto'),
        ('DIRECT_EMOLA',  'e-Mola Direto'),
        ('MOCK',          'Mock (Testes)'),
    ]
    STATUS_CHOICES = [
        ('PENDING',    'Pendente'),
        ('PROCESSING', 'Em processamento'),
        ('SUCCESS',    'Sucesso'),
        ('FAILED',     'Falhado'),
        ('REFUNDED',   'Reembolsado'),
    ]

    transaction = models.ForeignKey(
        Transaction, on_delete=models.CASCADE, related_name='payments'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=10, choices=METHOD_CHOICES)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')

    # referência interna única — nunca muda
    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    # referência devolvida pelo provider externo
    external_reference = models.CharField(max_length=200, blank=True, null=True)
    # ID da transação no sistema do provider
    provider_transaction_id = models.CharField(max_length=200, blank=True, null=True)
    # resposta bruta do provider (para auditoria e debug)
    raw_response = models.JSONField(default=dict, blank=True)

    phone_number = models.CharField(max_length=20, blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.reference} | {self.method} | {self.status}"
