import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from api.models.payment import Payment
from api.models.marketplace import Transaction
from api.serializers.payment import (
    PaymentSerializer,
    InitiatePaymentSerializer,
    WebhookPayloadSerializer,
)
from api.services.payment_service import PaymentService

logger = logging.getLogger(__name__)


class InitiatePaymentView(APIView):
    """
    POST /api/payments/initiate/
    Cria e inicia um pagamento para uma transação existente.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = InitiatePaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        # Validar que a transação pertence ao comprador
        try:
            txn = Transaction.objects.get(
                id=data['transaction_id'],
                buyer=request.user,
            )
        except Transaction.DoesNotExist:
            return Response(
                {"detail": "Transação não encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if txn.status not in ('RESERVED', 'AWAITING_PAYMENT'):
            return Response(
                {"detail": f"Não é possível pagar uma transação com status '{txn.status}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Evitar pagamento duplicado activo
        if Payment.objects.filter(
            transaction=txn,
            status__in=('PENDING', 'PROCESSING', 'SUCCESS')
        ).exists():
            return Response(
                {"detail": "Já existe um pagamento activo para esta transação."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment = PaymentService.create_payment(
            transaction=txn,
            method=data['method'],
            provider=data['provider'],
            phone_number=data.get('phone_number'),
        )
        payment = PaymentService.initiate(payment)

        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


class PaymentDetailView(APIView):
    """
    GET /api/payments/<reference>/
    Detalhe de um pagamento. Apenas comprador ou vendedor da transação.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, reference):
        try:
            payment = Payment.objects.select_related('transaction').get(reference=reference)
        except Payment.DoesNotExist:
            return Response({"detail": "Pagamento não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        txn = payment.transaction
        if request.user not in (txn.buyer, txn.seller):
            return Response({"detail": "Sem permissão."}, status=status.HTTP_403_FORBIDDEN)

        return Response(PaymentSerializer(payment).data)


class VerifyPaymentView(APIView):
    """
    POST /api/payments/<reference>/verify/
    Força verificação do estado junto do provider (polling manual).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, reference):
        try:
            payment = Payment.objects.select_related('transaction').get(reference=reference)
        except Payment.DoesNotExist:
            return Response({"detail": "Pagamento não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        txn = payment.transaction
        if request.user not in (txn.buyer, txn.seller):
            return Response({"detail": "Sem permissão."}, status=status.HTTP_403_FORBIDDEN)

        payment = PaymentService.verify(payment)
        return Response(PaymentSerializer(payment).data)


class PaymentWebhookView(APIView):
    """
    POST /api/payments/webhook/
    Recebe callbacks dos providers de pagamento.
    Público mas validado por referência UUID.
    Idempotente — processa cada referência apenas uma vez.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = WebhookPayloadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        reference = str(data['reference'])
        provider_status = data['status']

        payment = PaymentService.process_webhook(
            reference=reference,
            provider_status=provider_status,
            raw_payload=request.data,
        )

        if payment is None:
            return Response(
                {"detail": "Referência desconhecida."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({"detail": "Webhook processado.", "status": payment.status})


class PaymentListView(APIView):
    """
    GET /api/payments/
    Lista os pagamentos do utilizador autenticado (como comprador ou vendedor).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payments = Payment.objects.filter(
            transaction__buyer=request.user
        ) | Payment.objects.filter(
            transaction__seller=request.user
        )
        payments = payments.select_related('transaction').order_by('-created_at')
        return Response(PaymentSerializer(payments, many=True).data)
