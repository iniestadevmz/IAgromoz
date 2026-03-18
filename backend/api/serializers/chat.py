from rest_framework import serializers
from api.models.chat import ChatSession, ChatMessage

# User resumido
class ChatUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()

# simplified message serializer without user/session, used within session listing
class ChatMessageSimpleSerializer(serializers.ModelSerializer):
    message_id = serializers.IntegerField(source='id', read_only=True)

    class Meta:
        model = ChatMessage
        fields = ['message_id', 'mensagem', 'is_bot', 'timestamp']


class ChatMessageSerializer(serializers.ModelSerializer):
    message_id = serializers.IntegerField(source='id', read_only=True)
    user = ChatUserSerializer(read_only=True)
    session = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = ['message_id', 'mensagem', 'is_bot', 'timestamp', 'user', 'session']

    def get_session(self, obj):
        # only include session_id and title for the session
        if obj.session:
            return {
                'session_id': obj.session.id,
                'titulo': obj.session.titulo
            }
        return None


class ChatSessionSerializer(serializers.ModelSerializer):
    session_id = serializers.IntegerField(source='id', read_only=True)
    user = ChatUserSerializer(read_only=True)
    mensagens = ChatMessageSimpleSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = ['session_id', 'titulo', 'user', 'criado_em', 'mensagens']


# serializer used for listing sessions with only their titles (and session_id)
class ChatSessionTitleSerializer(serializers.ModelSerializer):
    session_id = serializers.IntegerField(source='id', read_only=True)

    class Meta:
        model = ChatSession
        fields = ['session_id', 'titulo']
