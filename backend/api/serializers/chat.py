from rest_framework import serializers
from api.models.chat import ChatSession, ChatMessage


class ChatUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()


class ChatMessageSimpleSerializer(serializers.ModelSerializer):
    message_id = serializers.IntegerField(source='id', read_only=True)

    class Meta:
        model = ChatMessage
        fields = ['message_id', 'message', 'is_bot', 'timestamp']


class ChatMessageSerializer(serializers.ModelSerializer):
    message_id = serializers.IntegerField(source='id', read_only=True)
    user = ChatUserSerializer(read_only=True)
    session = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = ['message_id', 'message', 'is_bot', 'timestamp', 'user', 'session']

    def get_session(self, obj):
        if obj.session:
            return {'session_id': obj.session.id, 'title': obj.session.title}
        return None


class ChatSessionSerializer(serializers.ModelSerializer):
    session_id = serializers.IntegerField(source='id', read_only=True)
    user = ChatUserSerializer(read_only=True)
    messages = ChatMessageSimpleSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = ['session_id', 'title', 'user', 'created_at', 'messages']


class ChatSessionTitleSerializer(serializers.ModelSerializer):
    session_id = serializers.IntegerField(source='id', read_only=True)

    class Meta:
        model = ChatSession
        fields = ['session_id', 'title']
