from api.serializers.techniques import TecnicaSerializer
from rest_framework.views import APIView
from rest_framework.viewsets  import ModelViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

from api.models.techniques import Tecnica
from api.models.votes import VotoTecnica

class TecnicaViewSet(ModelViewSet):
    queryset = Tecnica.objects.all()
    serializer_class = TecnicaSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]  
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_destroy(self, instance):
        user = self.request.user
        if user != instance.criada_por and not user.is_staff:
            return Response({"detail": "Sem permissão para apagar esta mensagem"}, status=status.HTTP_403_FORBIDDEN)
        instance.delete()

class VotarTecnicaView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, tecnica_id):
        voto = request.data.get('voto') 

        if voto not in ['APROVA', 'REPROVA']:
            return Response(
                {"erro": "Voto inválido"},
                status=status.HTTP_400_BAD_REQUEST
            )

        tecnica = Tecnica.objects.get(id=tecnica_id)

        # impede voto duplicado
        if VotoTecnica.objects.filter(usuario=request.user, tecnica=tecnica).exists():
            return Response(
                {"erro": "Você já votou nesta técnica"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # registra voto
        VotoTecnica.objects.create(
            usuario=request.user,
            tecnica=tecnica,
            voto=voto
        )

        if voto == 'APROVA':
            tecnica.votos_aprovacao += 1
        else:
            tecnica.votos_rejeicao += 1

        tecnica.save()
        tecnica.avaliar_tecnica() 

        return Response(
            {"status_tecnica": tecnica.status},
            status=status.HTTP_200_OK
        )
