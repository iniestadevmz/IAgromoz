from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone
from datetime import timedelta
from api.models.feed import Post, Comment
from api.serializers.feed import PostSerializer, CommentSerializer, build_comment_tree
from api.permissions import IsOwnerOrAdminDelete, IsFeedPublic, IsNotSeller
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

EDIT_LIMIT = timedelta(minutes=10)


class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [IsNotSeller, IsFeedPublic]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        qs = Post.objects.select_related('author').all().order_by('-created_at')
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)
        return qs

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        post = self.get_object()
        if post.author != self.request.user:
            raise PermissionDenied("You can only edit your own post.")
        if timezone.now() - post.created_at > EDIT_LIMIT:
            raise PermissionDenied("Edit window expired (10 minutes).")
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if instance.author != user and getattr(user, 'role', '') != 'ADMIN':
            raise PermissionDenied("You do not have permission to delete this post.")
        instance.delete()

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        post = self.get_object()
        user = request.user
        if user in post.likes.all():
            post.likes.remove(user)
            return Response({"status": "unliked"})
        else:
            post.likes.add(user)
            return Response({"status": "liked"})


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsNotSeller()]  # leitura bloqueada para SELLER
        return [IsAuthenticated(), IsNotSeller(), IsOwnerOrAdminDelete()]

    def get_queryset(self):
        return Comment.objects.select_related('author', 'post').all().order_by('created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        post_id = request.query_params.get('post')
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        tree = build_comment_tree(list(queryset))
        serializer = self.get_serializer(tree, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        comment = self.get_object()
        if self.request.user != comment.author:
            raise PermissionDenied("Not authorized to update this comment.")
        if timezone.now() - comment.created_at > EDIT_LIMIT:
            raise PermissionDenied("Edit window expired (10 minutes).")
        serializer.save()

    def perform_destroy(self, instance):
        if self.request.user != instance.author and not self.request.user.is_staff:
            raise PermissionDenied("Not authorized to delete this comment.")
        instance.delete()
