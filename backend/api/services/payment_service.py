"""
PaymentService — orquestra o ciclo de vida de um Payment.

Responsabilidades:
  - criar Payment
  - iniciar pagamento via gateway
  - verificar pagamento
  - processar webhook
  - actualizar Transaction quando Payment é confirmado
"""
import logging
from django.db import transaction as db_transaction
from django.utils import timezone

from api.models.payment import Payment
from api.models.marketplace import Transaction
from api.services.payment_gateways import PaymentGatewayFactory

logger = logging.getLogger(__name__)


class PaymentService:

    # ------------------------------------------------------------------
    # Criar e iniciar pagamento
    # ------------------------------------------------------------------

    @staticmethod
    def create_payment(transaction: Transaction, method: str, provider: str,
                       phone_number: str = None) -> Payment:
        """
        Cria um Payment em estado PENDING para a transação dada.
        Não inicia o pagamento — use initiate() depois.
        """
        payment = Payment.objects.create(
            transaction=transaction,
            amount=transaction.amount,
            method=method,
            provider=provider,
            status='PENDING',
            phone_number=phone_number,
        )
        logger.info("Payment criado: %s | transação %s", payment.reference, transaction.id)
        return payment

    @staticmethod
    def initiate(payment: Payment) -> Payment:
        """
        Envia o pagamento ao gateway e actualiza o Payment com a resposta.
        Não altera a Transaction — isso só acontece na confirmação.
        """
        gateway = PaymentGatewayFactory.get_gateway(payment)

        try:
            result = gateway.initiate_payment(payment)
        except Exception as exc:
            logger.error("Erro ao iniciar pagamento %s: %s", payment.reference, exc)
            payment.status = 'FAILED'
            payment.raw_response = {"error": str(exc)}
            payment.save(update_fields=['status', 'raw_response', 'updated_at'])
            return payment

        payment.status = result['status']
        payment.external_reference = result.get('external_reference')
        payment.provider_transaction_id = result.get('provider_transaction_id')
        payment.raw_response = result.get('raw_response', {})

        if result['status'] == 'SUCCESS':
            payment.paid_at = timezone.now()

        payment.save(update_fields=[
            'status', 'external_reference', 'provider_transaction_id',
            'raw_response', 'paid_at', 'updated_at',
        ])

        # Se já confirmado, actualizar a Transaction
        if result['status'] == 'SUCCESS':
            PaymentService._confirm_transaction(payment)

        logger.info("Payment %s → %s", payment.reference, payment.status)
        return payment

    # ------------------------------------------------------------------
    # Verificar pagamento (polling ou chamada manual)
    # ------------------------------------------------------------------

    @staticmethod
    def verify(payment: Payment) -> Payment:
        """
        Consulta o provider sobre o estado actual do pagamento.
        Útil para polling quando o provider não envia webhook.
        """
        gateway = PaymentGatewayFactory.get_gateway(payment)

        try:
            result = gateway.verify_payment(str(payment.reference))
        except Exception as exc:
            logger.error("Erro ao verificar pagamento %s: %s", payment.reference, exc)
            return payment

        new_status = result.get('status', payment.status)
        if new_status == payment.status:
            return payment  # nada mudou

        payment.status = new_status
        payment.raw_response = result.get('raw_response', payment.raw_response)

        if new_status == 'SUCCESS' and not payment.paid_at:
            payment.paid_at = timezone.now()

        payment.save(update_fields=['status', 'raw_response', 'paid_at', 'updated_at'])

        if new_status == 'SUCCESS':
            PaymentService._confirm_transaction(payment)

        return payment

    # ------------------------------------------------------------------
    # Processar webhook (idempotente)
    # ------------------------------------------------------------------

    @staticmethod
    def process_webhook(reference: str, provider_status: str,
                        raw_payload: dict) -> Payment | None:
        """
        Processa callback de um provider.
        Idempotente: se o Payment já está em SUCCESS/FAILED, ignora.
        """
        try:
            payment = Payment.objects.select_for_update().get(reference=reference)
        except Payment.DoesNotExist:
            logger.warning("Webhook recebido para referência desconhecida: %s", reference)
            return None

        with db_transaction.atomic():
            # Idempotência — não reprocessar estados terminais
            if payment.status in ('SUCCESS', 'FAILED', 'REFUNDED'):
                logger.info(
                    "Webhook ignorado (já terminal): %s → %s",
                    reference, payment.status
                )
                return payment

            payment.status = provider_status
            payment.raw_response = {**payment.raw_response, "webhook": raw_payload}

            if provider_status == 'SUCCESS' and not payment.paid_at:
                payment.paid_at = timezone.now()

            payment.save(update_fields=['status', 'raw_response', 'paid_at', 'updated_at'])

            if provider_status == 'SUCCESS':
                PaymentService._confirm_transaction(payment)

        logger.info("Webhook processado: %s → %s", reference, provider_status)
        return payment

    # ------------------------------------------------------------------
    # Reembolso
    # ------------------------------------------------------------------

    @staticmethod
    def refund(payment: Payment) -> Payment:
        """Solicita reembolso ao provider e actualiza o Payment."""
        if payment.status != 'SUCCESS':
            raise ValueError("Só é possível reembolsar pagamentos com status SUCCESS.")

        gateway = PaymentGatewayFactory.get_gateway(payment)

        try:
            result = gateway.refund_payment(payment)
        except Exception as exc:
            logger.error("Erro ao reembolsar pagamento %s: %s", payment.reference, exc)
            raise

        payment.status = 'REFUNDED'
        payment.raw_response = {**payment.raw_response, "refund": result.get('raw_response', {})}
        payment.save(update_fields=['status', 'raw_response', 'updated_at'])

        logger.info("Payment %s reembolsado.", payment.reference)
        return payment

    # ------------------------------------------------------------------
    # Interno — confirmar Transaction
    # ------------------------------------------------------------------

    @staticmethod
    def _confirm_transaction(payment: Payment):
        """
        Marca a Transaction como PAID após confirmação real do pagamento.
        Separado intencionalmente: Payment SUCCESS ≠ Transaction concluída.
        A conclusão final (COMPLETED) continua a ser feita pelo vendedor.
        """
        txn = payment.transaction
        if txn.status not in ('PAID', 'COMPLETED', 'CANCELLED'):
            txn.status = 'PAID'
            txn.payment_method = payment.method
            txn.payment_reference = str(payment.reference)
            txn.payment_date = payment.paid_at
            txn.save(update_fields=['status', 'payment_method', 'payment_reference', 'payment_date'])
            logger.info("Transaction %s marcada como PAID via Payment %s", txn.id, payment.reference)
