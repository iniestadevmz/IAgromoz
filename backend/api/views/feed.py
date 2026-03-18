from rest_framework import viewsets, permissions
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone
from datetime import timedelta
from api.models.feed import Post, Comment
from api.serializers.feed import PostSerializer, CommentSerializer, build_comment_tree
from api.permissions import IsOwnerOrAdminDelete

# Limite de edição
EDICAO_LIMITE = timedelta(minutes=10)



class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [IsOwnerOrAdminDelete]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return Post.objects.select_related('autor').all().order_by('-criado_em')

    def perform_create(self, serializer):
        serializer.save(autor=self.request.user)

    def perform_update(self, serializer):
        post = self.get_object()
        if post.autor != self.request.user:
            raise PermissionDenied("Você só pode editar seu próprio post.")
        if timezone.now() - post.criado_em > EDICAO_LIMITE:
            raise PermissionDenied("Prazo para editar expirado (10 minutos).")
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if instance.autor != user and getattr(user, 'tipos', '') != 'ADMIN':
            raise PermissionDenied("Você não tem permissão para deletar este post.")
        instance.delete()


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [IsOwnerOrAdminDelete]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return Comment.objects.select_related('autor', 'post').all().order_by('criado_em')

    def list(self, request, *args, **kwargs):
        # opcional: filtrar por post
        queryset = self.get_queryset()
        post_id = request.query_params.get('post')
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        tree = build_comment_tree(list(queryset))
        serializer = self.get_serializer(tree, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(autor=self.request.user)

    def perform_update(self, serializer):
        comment = self.get_object()
        prazo_edicao = timedelta(minutes=10)
        if self.request.user != comment.autor:
            raise PermissionDenied("Sem autorização para atualizar este comentário")
        if timezone.now() - comment.criado_em > EDICAO_LIMITE:
            raise PermissionDenied("Prazo para editar expirado (10 minutos).")
        serializer.save()

    def perform_destroy(self, instance):
        if self.request.user != instance.autor and not self.request.user.is_staff:
            raise PermissionDenied("Sem permissão para apagar este comentário")
        instance.delete()