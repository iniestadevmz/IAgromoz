

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminUserCustom(BasePermission):
    """
    Permite acesso apenas para usuários com role='ADMIN'.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, 'tipos', '') == 'ADMIN')


class IsAdminOrPodeVender(BasePermission):
    """
    Permite operações de escrita a usuários com `pode_vender=True` ou administradores.
    Leitura fica permitida para todos (quando combinada com `IsAuthenticatedOrReadOnly`).
    """
    def has_permission(self, request, view):
        # Permite sempre ações de leitura (delegue ao IsAuthenticatedOrReadOnly se for usado)
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True

        user = request.user
        if not (user and user.is_authenticated):
            return False

        # Administrador (tipos == 'ADMIN') ou usuário com permissão para vender
        return bool(getattr(user, 'tipos', '') == 'ADMIN' or getattr(user, 'pode_vender', False))





class IsOwnerOrAdminDelete(BasePermission):
    """
    Permissão para Post/Comment:
    - Autor pode fazer qualquer ação no próprio objeto
    - Admin só pode deletar objetos de outros usuários
    - Leitura permitida para todos usuários autenticados
    """

    # def has_permission(self, request, view):
    #     # Apenas usuários autenticados podem acessar
    #     return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Leitura sempre permitida
        if request.method in SAFE_METHODS:
            return True

        # Autor pode fazer qualquer ação (PUT, PATCH, DELETE)
        if obj.autor == request.user:
            return True

        # Admin só pode deletar
        if getattr(request.user, 'tipos', '') == 'ADMIN' and request.method == 'DELETE':
            return True

        # Qualquer outro caso → negar
        return False

class IsAdminOrOwner(BasePermission): 
    """ Permite acesso somente ao admin ou ao usuário que criou o objeto. """
    def has_permission(self, request, view):
        # Apenas usuários autenticados podem acessar
        return request.user and request.user.is_authenticate 
    def has_object_permission(self, request, view, obj): 
        # Métodos de leitura sempre permitidos (GET, HEAD, OPTIONS) 
        
        if request.method in SAFE_METHODS:
            return True 
        # Permitir se o usuário for admin 
        if request.user.is_staff: 
            return True 
        # Permitir se o usuário for o criador do produto
        return obj.vendedor == request.user