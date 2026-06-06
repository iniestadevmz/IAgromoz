"""
Gateways de pagamento.

BasePaymentGateway  — contrato abstracto
MockPaymentGateway  — implementação de testes (sem chamadas externas)
PaymentGatewayFactory — escolhe o gateway correcto com base em settings.PAYMENT_MODE
"""
import random
import uuid
from abc import ABC, abstractmethod
from django.utils import timezone


# ---------------------------------------------------------------------------
# Contrato base
# ---------------------------------------------------------------------------

class BasePaymentGateway(ABC):
    """Todos os gateways devem implementar estes três métodos."""

    @abstractmethod
    def initiate_payment(self, payment) -> dict:
        """
        Inicia o pagamento junto do provider.
        Deve devolver um dict com pelo menos:
          {
            "success": bool,
            "status": "PENDING" | "PROCESSING" | "SUCCESS" | "FAILED",
            "external_reference": str | None,
            "provider_transaction_id": str | None,
            "raw_response": dict,
            "message": str,
          }
        """

    @abstractmethod
    def verify_payment(self, reference: str) -> dict:
        """
        Verifica o estado actual de um pagamento junto do provider.
        Devolve o mesmo formato de initiate_payment.
        """

    @abstractmethod
    def refund_payment(self, payment) -> dict:
        """
        Solicita reembolso ao provider.
        Devolve o mesmo formato de initiate_payment.
        """


# ---------------------------------------------------------------------------
# Mock Gateway — obrigatório para testes
# ---------------------------------------------------------------------------

class MockPaymentGateway(BasePaymentGateway):
    """
    Simula um provider real sem qualquer chamada externa.
    Comportamento controlado por MOCK_PAYMENT_RESULT em settings (opcional):
      "success"    → sempre sucesso
      "failed"     → sempre falha
      "processing" → fica em processamento (aguarda webhook)
    Por omissão usa resultado aleatório realista.
    """

    def _mock_result(self) -> str:
        from django.conf import settings
        forced = getattr(settings, 'MOCK_PAYMENT_RESULT', None)
        if forced:
            return forced
        # distribuição realista: 80% sucesso, 15% processing, 5% falha
        return random.choices(
            ['success', 'processing', 'failed'],
            weights=[80, 15, 5]
        )[0]

    def initiate_payment(self, payment) -> dict:
        result = self._mock_result()
        ext_ref = f"MOCK-{uuid.uuid4().hex[:12].upper()}"

        if result == 'success':
            return {
                "success": True,
                "status": "SUCCESS",
                "external_reference": ext_ref,
                "provider_transaction_id": f"TXN-{uuid.uuid4().hex[:8].upper()}",
                "raw_response": {
                    "mock": True,
                    "result": "success",
                    "ext_ref": ext_ref,
                    "amount": str(payment.amount),
                    "phone": payment.phone_number,
                    "timestamp": timezone.now().isoformat(),
                },
                "message": "Pagamento processado com sucesso (mock).",
            }

        if result == 'processing':
            return {
                "success": True,
                "status": "PROCESSING",
                "external_reference": ext_ref,
                "provider_transaction_id": None,
                "raw_response": {
                    "mock": True,
                    "result": "processing",
                    "ext_ref": ext_ref,
                    "timestamp": timezone.now().isoformat(),
                },
                "message": "Pagamento em processamento. Aguarda confirmação (mock).",
            }

        # failed
        return {
            "success": False,
            "status": "FAILED",
            "external_reference": None,
            "provider_transaction_id": None,
            "raw_response": {
                "mock": True,
                "result": "failed",
                "error_code": "INSUFFICIENT_FUNDS",
                "timestamp": timezone.now().isoformat(),
            },
            "message": "Pagamento recusado pelo provider (mock).",
        }

    def verify_payment(self, reference: str) -> dict:
        # No mock, uma verificação devolve sempre SUCCESS para referências válidas
        return {
            "success": True,
            "status": "SUCCESS",
            "external_reference": reference,
            "provider_transaction_id": f"TXN-{uuid.uuid4().hex[:8].upper()}",
            "raw_response": {
                "mock": True,
                "verified": True,
                "reference": reference,
                "timestamp": timezone.now().isoformat(),
            },
            "message": "Pagamento verificado com sucesso (mock).",
        }

    def refund_payment(self, payment) -> dict:
        return {
            "success": True,
            "status": "REFUNDED",
            "external_reference": str(payment.reference),
            "provider_transaction_id": payment.provider_transaction_id,
            "raw_response": {
                "mock": True,
                "refunded": True,
                "amount": str(payment.amount),
                "timestamp": timezone.now().isoformat(),
            },
            "message": "Reembolso processado com sucesso (mock).",
        }


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

class PaymentGatewayFactory:
    """
    Devolve o gateway correcto com base em settings.PAYMENT_MODE
    ou no provider do Payment.

    PAYMENT_MODE = "MOCK"  → MockPaymentGateway (sempre)
    PAYMENT_MODE = "LIVE"  → gateway baseado em payment.provider
    """

    @staticmethod
    def get_gateway(payment=None) -> BasePaymentGateway:
        from django.conf import settings
        mode = getattr(settings, 'PAYMENT_MODE', 'MOCK').upper()

        if mode == 'MOCK':
            return MockPaymentGateway()

        # Modo LIVE — escolhe pelo provider do payment
        if payment is None:
            return MockPaymentGateway()

        provider = getattr(payment, 'provider', 'MOCK')

        if provider in ('DIRECT_MPESA', 'PAYSUITE'):
            # from api.services.mpesa_gateway import MpesaGateway
            # return MpesaGateway()
            raise NotImplementedError(f"Gateway para '{provider}' ainda não implementado.")

        if provider in ('DIRECT_EMOLA', 'E2PAYMENTS'):
            # from api.services.emola_gateway import EMolaGateway
            # return EMolaGateway()
            raise NotImplementedError(f"Gateway para '{provider}' ainda não implementado.")

        # fallback seguro
        return MockPaymentGateway()
