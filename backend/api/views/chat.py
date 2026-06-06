from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from api.models.chat import ChatSession, ChatMessage
from api.serializers.chat import ChatSessionSerializer, ChatMessageSerializer, ChatSessionTitleSerializer
from api.ia.service import processar_chat

DEFAULT_TITLE = "Nova conversa"


class ChatSessionListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatSessionSerializer
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ChatSessionTitleSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return ChatSession.objects.filter(user=self.request.user)
        return ChatSession.objects.none()

    def create(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            session = ChatSession.objects.create(user=request.user, title=DEFAULT_TITLE)
            serializer = self.get_serializer(session)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response({"title": "Anonymous Chat", "messages": []}, status=status.HTTP_201_CREATED)


class ChatMessageListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatMessageSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        session_id = self.request.query_params.get("session_id")
        if session_id:
            return ChatMessage.objects.filter(session_id=session_id).order_by("timestamp")
        return ChatMessage.objects.none()

    def list(self, request, *args, **kwargs):
        session_id = request.query_params.get("session_id")
        if session_id:
            return super().list(request, *args, **kwargs)
        if request.user.is_authenticated:
            sessions = ChatSession.objects.filter(user=request.user)
            serializer = ChatSessionSerializer(sessions, many=True)
            return Response(serializer.data)
        return Response([], status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        session_id = request.data.get("session_id")
        user_message = request.data.get("message")

        if not user_message or not str(user_message).strip():
            return Response({"error": "The 'message' field cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)

        if request.user.is_authenticated:
            if not session_id:
                words = str(user_message).strip().split()[:6]
                session = ChatSession.objects.create(user=request.user, title=" ".join(words))
            else:
                try:
                    session = ChatSession.objects.get(id=session_id, user=request.user)
                except ChatSession.DoesNotExist:
                    return Response({"error": "Session not found."}, status=status.HTTP_404_NOT_FOUND)

                if session.title == DEFAULT_TITLE:
                    words = str(user_message).strip().split()[:6]
                    session.title = " ".join(words)
                    session.save(update_fields=['title'])

            msg_user = ChatMessage.objects.create(
                session=session, message=user_message, is_bot=False, user=request.user
            )
            bot_response = processar_chat(user_message, user=session.user, session=session)
            msg_bot = ChatMessage.objects.create(
                session=session, message=bot_response, is_bot=True, user=session.user
            )

            serializer = self.get_serializer([msg_user, msg_bot], many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            bot_response = processar_chat(user_message, user=None, session=None)
            return Response({
                "title": "Anonymous Chat",
                "messages": [
                    {"message": user_message, "is_bot": False},
                    {"message": bot_response, "is_bot": True},
                ]
            }, status=status.HTTP_201_CREATED)
