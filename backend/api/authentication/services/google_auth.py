"""
GoogleAuthService
=================
Valida Google ID Token e cria/associa utilizador.
Nunca confia em dados enviados pelo frontend — valida sempre via google-auth.
"""
from django.db import transaction
from django.utils import timezone
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from google.auth.exceptions import TransportError
import logging

logger = logging.getLogger('api.auth')

VALID_ISSUERS = {'accounts.google.com', 'https://accounts.google.com'}


class GoogleTokenError(Exception):
    """Erros tipados de validação do token Google."""
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class GoogleAuthService:

    @classmethod
    def authenticate(cls, id_token_str: str, client_id: str, request=None) -> dict:
        """
        Valida o Google ID Token e retorna ou cria o utilizador + JWT.

        Raises GoogleTokenError com códigos:
          - invalid_google_token
          - expired_google_token
          - invalid_audience
          - email_not_verified
        """
        payload = cls._verify_token(id_token_str, client_id)
        user = cls._get_or_create_user(payload, request)
        tokens = cls._generate_jwt(user)
        return user, tokens

    @classmethod
    def _verify_token(cls, id_token_str: str, client_id: str) -> dict:
        try:
            payload = id_token.verify_oauth2_token(
                id_token_str,
                google_requests.Request(),
                client_id,
            )
        except ValueError as e:
            msg = str(e).lower()
            if 'expired' in msg:
                raise GoogleTokenError('expired_google_token', 'Google token expirado.')
            if 'audience' in msg:
                raise GoogleTokenError('invalid_audience', 'Audience inválida.')
            raise GoogleTokenError('invalid_google_token', f'Token Google inválido: {e}')
        except TransportError as e:
            raise GoogleTokenError('invalid_google_token', f'Erro de transporte Google: {e}')

        if payload.get('iss') not in VALID_ISSUERS:
            raise GoogleTokenError('invalid_google_token', 'Issuer inválido.')

        if not payload.get('email_verified', False):
            raise GoogleTokenError('email_not_verified', 'Email Google não verificado.')

        return payload

    @classmethod
    @transaction.atomic
    def _get_or_create_user(cls, payload: dict, request=None):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        google_id = payload['sub']
        email = payload['email']
        name_parts = payload.get('name', '').split(' ', 1)
        first_name = name_parts[0] if name_parts else ''
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        avatar = payload.get('picture', '')

        # IP para auditoria
        ip = cls._get_ip(request)

        # 1. Já existe utilizador com este google_id
        try:
            user = User.objects.get(google_id=google_id)
            user.last_login = timezone.now()
            user.last_login_ip = ip
            user.save(update_fields=['last_login', 'last_login_ip', 'updated_at'])
            return user
        except User.DoesNotExist:
            pass

        # 2. Existe utilizador com este email mas sem google_id
        try:
            user = User.objects.get(email=email)
            user.google_id = google_id
            user.provider = User.PROVIDER_GOOGLE
            user.email_verified = True
            user.last_login = timezone.now()
            user.last_login_ip = ip
            if not user.avatar and avatar:
                user.avatar = avatar
            user.save(update_fields=[
                'google_id', 'provider', 'email_verified',
                'avatar', 'last_login', 'last_login_ip', 'updated_at'
            ])
            return user
        except User.DoesNotExist:
            pass

        # 3. Novo utilizador
        user = User.objects.create_google_user(
            email=email,
            google_id=google_id,
            first_name=first_name,
            last_name=last_name,
            avatar=avatar,
        )
        user.last_login = timezone.now()
        user.last_login_ip = ip
        user.save(update_fields=['last_login', 'last_login_ip'])
        logger.info(f'[GoogleAuth] Novo utilizador criado: {email}')
        return user

    @staticmethod
    def _generate_jwt(user) -> dict:
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        refresh['role'] = user.role
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }

    @staticmethod
    def _get_ip(request) -> str:
        if not request:
            return ''
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[-1].strip()
        return request.META.get('REMOTE_ADDR', '')
