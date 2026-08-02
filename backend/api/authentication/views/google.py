from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from decouple import config

from api.authentication.services.google_auth import GoogleAuthService, GoogleTokenError
from api.authentication.services.profile_completion import ProfileCompletionService
from api.throttles import google_auth_rate_limit


GOOGLE_CLIENT_ID = config('GOOGLE_CLIENT_ID', default='')


class GoogleAuthView(APIView):
    """
    POST /api/auth/google/
    Recebe o Google ID Token do frontend, valida, cria/associa utilizador
    e devolve JWT próprio da aplicação.
    """
    permission_classes = [AllowAny]

    @google_auth_rate_limit
    def post(self, request):
        id_token_str = request.data.get('id_token', '').strip()
        if not id_token_str:
            return Response(
                {'error': 'invalid_google_token', 'detail': 'id_token é obrigatório.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not GOOGLE_CLIENT_ID:
            return Response(
                {'error': 'server_misconfiguration', 'detail': 'GOOGLE_CLIENT_ID não configurado.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            user, tokens = GoogleAuthService.authenticate(
                id_token_str=id_token_str,
                client_id=GOOGLE_CLIENT_ID,
                request=request,
            )
        except GoogleTokenError as e:
            return Response(
                {'error': e.code, 'detail': e.message},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except Exception as e:
            return Response(
                {'error': 'server_error', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        completion = ProfileCompletionService.check(user)

        return Response({
            'access': tokens['access'],
            'refresh': tokens['refresh'],
            'profile_completed': completion['profile_completed'],
            'missing_fields': completion['missing_fields'],
            'required_profile': completion['required_profile'],
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.get_full_name(),
                'avatar': user.avatar,
                'provider': user.provider,
            },
        }, status=status.HTTP_200_OK)
