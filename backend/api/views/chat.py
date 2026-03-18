from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from api.models.chat import ChatSession, ChatMessage
from api.serializers.chat import ChatSessionSerializer, ChatMessageSerializer, ChatSessionTitleSerializer
from api.ia.service import processar_chat

class ChatSessionListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatSessionSerializer
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        # when listing sessions we only return identifier and title
        if self.request.method == 'GET':
            return ChatSessionTitleSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return ChatSession.objects.filter(user=self.request.user)
        return ChatSession.objects.none()

    def create(self, request, *args, **kwargs):
        # explicit session creation is allowed but title is not supplied by client
        # to keep things simple we always use a generic placeholder.  actual
        # titles are generated automatically when the first message is sent.
        if request.user.is_authenticated:
            session = ChatSession.objects.create(user=request.user, titulo="Chat sem título")
            serializer = self.get_serializer(session)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            # anonymous sessions simply return a stub; title not important
            session = {"titulo": "Chat Anônimo", "mensagens": []}
            return Response(session, status=status.HTTP_201_CREATED)

class ChatMessageListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatMessageSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        # only used when listing messages for a specific session
        session_id = self.request.query_params.get("session_id")
        if session_id:
            # return all messages for the session (ordered by time)
            return ChatMessage.objects.filter(session_id=session_id).order_by("timestamp")
        # otherwise queryset not used by our custom list
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
        mensagem_usuario = request.data.get("mensagem")

        # Validar campo obrigatório
        if not mensagem_usuario or not str(mensagem_usuario).strip():
            return Response({"error": "O campo 'mensagem' não pode estar vazio"}, status=status.HTTP_400_BAD_REQUEST)

        if request.user.is_authenticated:
            # Se session_id não for fornecido, criar uma nova sessão automaticamente
            if not session_id:
                # Gerar título a partir das primeiras 10 palavras da mensagem
                palavras = str(mensagem_usuario).strip().split()[:10]
                titulo = " ".join(palavras)
                
                session = ChatSession.objects.create(
                    user=request.user, 
                    titulo=titulo
                )
            else:
                try:
                    session = ChatSession.objects.get(id=session_id, user=request.user)
                except ChatSession.DoesNotExist:
                    return Response({"error": "Sessão não encontrada"}, status=status.HTTP_404_NOT_FOUND)

            msg_usuario = ChatMessage.objects.create(
                session=session,
                mensagem=mensagem_usuario,
                is_bot=False,
                user=request.user,
            )

            resposta_bot = processar_chat(mensagem_usuario, user=session.user, session=session)
            msg_bot = ChatMessage.objects.create(
                session=session,
                mensagem=resposta_bot,
                is_bot=True,
                user=session.user,
            )

            serializer = self.get_serializer([msg_usuario, msg_bot], many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            resposta_bot = processar_chat(mensagem_usuario, user=None, session=None)
            session = {
                "titulo": "Chat Anônimo",
                "mensagens": [
                    {"mensagem": mensagem_usuario, "is_bot": False},
                    {"mensagem": resposta_bot, "is_bot": True}
                ]
            }
            return Response(session, status=status.HTTP_201_CREATED)
