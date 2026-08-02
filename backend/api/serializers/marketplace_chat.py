from rest_framework import serializers
from api.models.marketplace_chat import MarketplaceChat, MarketplaceMessage, MarketplaceChatReservation


class MarketplaceMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)

    class Meta:
        model = MarketplaceMessage
        fields = ['id', 'chat', 'sender', 'sender_name', 'content', 'is_read', 'created_at']
        read_only_fields = ['id', 'chat', 'sender', 'sender_name', 'is_read', 'created_at']


class MarketplaceChatReservationSerializer(serializers.ModelSerializer):
    transaction_status = serializers.CharField(source='transaction.status', read_only=True)
    product_name = serializers.CharField(source='transaction.product.name', read_only=True)

    class Meta:
        model = MarketplaceChatReservation
        fields = ['id', 'transaction', 'transaction_status', 'product_name', 'created_at']
        read_only_fields = fields


class MarketplaceChatSerializer(serializers.ModelSerializer):
    buyer_name = serializers.CharField(source='buyer.get_full_name', read_only=True)
    seller_name = serializers.CharField(source='seller.get_full_name', read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = MarketplaceChat
        fields = [
            'id', 'buyer', 'buyer_name', 'seller', 'seller_name',
            'status', 'created_at', 'closed_at',
            'last_message', 'unread_count',
        ]
        read_only_fields = fields

    def get_last_message(self, obj):
        msg = obj.messages.last()
        if msg:
            return {'content': msg.content, 'created_at': msg.created_at}
        return None

    def get_unread_count(self, obj):
        user = self.context['request'].user
        return obj.messages.filter(is_read=False).exclude(sender=user).count()
