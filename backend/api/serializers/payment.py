from rest_framework import serializers
from api.models.payment import Payment


class PaymentSerializer(serializers.ModelSerializer):
    reference = serializers.UUIDField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    method_display = serializers.CharField(source='get_method_display', read_only=True)
    provider_display = serializers.CharField(source='get_provider_display', read_only=True)
    transaction_id = serializers.IntegerField(source='transaction.id', read_only=True)
    product_name = serializers.CharField(source='transaction.product.name', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'reference', 'transaction_id', 'product_name',
            'amount', 'method', 'method_display',
            'provider', 'provider_display',
            'status', 'status_display',
            'phone_number',
            'external_reference', 'provider_transaction_id',
            'paid_at', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'reference', 'status', 'external_reference', 'provider_transaction_id',
            'paid_at', 'created_at', 'updated_at',
        ]


class InitiatePaymentSerializer(serializers.Serializer):
    """Usado no endpoint POST /payments/initiate/"""
    transaction_id = serializers.IntegerField()
    method = serializers.ChoiceField(choices=Payment.METHOD_CHOICES)
    provider = serializers.ChoiceField(choices=Payment.PROVIDER_CHOICES)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)


class WebhookPayloadSerializer(serializers.Serializer):
    """Payload esperado no endpoint POST /payments/webhook/"""
    reference = serializers.UUIDField()
    status = serializers.ChoiceField(choices=['SUCCESS', 'FAILED', 'PROCESSING'])
    provider_transaction_id = serializers.CharField(required=False, allow_blank=True)
