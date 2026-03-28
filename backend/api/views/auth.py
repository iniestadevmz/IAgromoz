
from rest_framework.permissions import AllowAny,IsAuthenticated
from api.models.users import User
from api.serializers.users import UserSerializer
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.serializers.users import ChangePasswordSerializer
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        if self.action =='create' :
            return [AllowAny()]        # cadastro
        return [IsAuthenticated()]    # resto
    
    # Endpoint para retornar o perfil do usuário logado
    @action(detail=False, methods=['get'], url_path='me', permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['put'], url_path='alterar-senha')
    def alterar_senha(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({"detail": "Palavra-passe atualizada com sucesso."}, status=status.HTTP_200_OK)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "Refresh token é obrigatório."}, status=400)
        
        try:
           
            token = RefreshToken(refresh_token)
            token.blacklist()  # precisa ativar Blacklist app
            return Response({"detail": "Logout realizado com sucesso."}, status=200)
        except Exception as e:
            return Response({"detail": "Token inválido ou expirado."}, status=400)





