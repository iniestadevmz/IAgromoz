from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone
from datetime import timedelta
from api.models.feed import Post, PostPhoto, PostProduct, Comment
from api.models.marketplace import Product
from api.serializers.feed import PostSerializer, PostPhotoSerializer, CommentSerializer, build_comment_tree
from api.serializers.marketplace import ProductSerializer
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
        qs = (
            Post.objects
            .select_related('author', 'district__province')
            .prefetch_related('post_products__product__district__province')
            .all()
            .order_by('-created_at')
        )
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)
        author = self.request.query_params.get('author')
        if author:
            qs = qs.filter(author__id=author)
        # ?mine=true — retorna apenas os posts do utilizador autenticado
        if self.request.query_params.get('mine') == 'true' and self.request.user.is_authenticated:
            qs = qs.filter(author=self.request.user)
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

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated],
            url_path='my-products')
    def my_products(self, request):
        """
        GET /feed/posts/my-products/
        Retorna os produtos do utilizador autenticado no marketplace.
        Só disponível para utilizadores com can_sell=True.
        """
        if not request.user.can_sell:
            return Response(
                {"detail": "Só vendedores e produtores têm produtos no marketplace."},
                status=403
            )
        products = (
            Product.objects
            .filter(seller=request.user)
            .select_related('district__province')
            .order_by('-created_at')
        )
        serializer = ProductSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated],
            url_path='link-product')
    def link_product(self, request, pk=None):
        """
        POST /feed/posts/{id}/link-product/
        Body: {"product_id": <int>, "label": "Ver produto"}
        Liga um produto do marketplace ao post.
        """
        post = self.get_object()
        if post.author != request.user:
            return Response({"detail": "Apenas o autor pode linkar produtos."}, status=403)

        product_id = request.data.get('product_id')
        if not product_id:
            return Response({"detail": "product_id é obrigatório."}, status=400)

        try:
            product = Product.objects.get(id=product_id, seller=request.user)
        except Product.DoesNotExist:
            return Response({"detail": "Produto não encontrado ou não é seu."}, status=404)

        label = request.data.get('label', 'Ver produto')
        pp, created = PostProduct.objects.get_or_create(
            post=post, product=product,
            defaults={'label': label}
        )
        if not created:
            pp.label = label
            pp.save(update_fields=['label'])

        return Response({
            "detail": "Produto linkado com sucesso.",
            "product_id": product.id,
            "product_name": product.name,
            "label": pp.label,
        }, status=200 if not created else 201)

    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated],
            url_path=r'unlink-product/(?P<product_id>\d+)')
    def unlink_product(self, request, pk=None, product_id=None):
        """
        DELETE /feed/posts/{id}/unlink-product/{product_id}/
        Remove a ligação entre post e produto.
        """
        post = self.get_object()
        if post.author != request.user:
            return Response({"detail": "Apenas o autor pode gerir produtos linkados."}, status=403)

        deleted, _ = PostProduct.objects.filter(post=post, product_id=product_id).delete()
        if not deleted:
            return Response({"detail": "Ligação não encontrada."}, status=404)
        return Response(status=204)

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

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated],
            parser_classes=[MultiPartParser, FormParser])
    def add_photo(self, request, pk=None):
        """POST /feed/posts/{id}/add_photo/ — adiciona até 5 fotos."""
        post = self.get_object()
        if post.author != request.user:
            return Response({"detail": "Not authorized."}, status=403)
        if post.photos.count() >= 5:
            return Response({"detail": "Máximo de 5 fotos atingido."}, status=400)
        image = request.FILES.get('image')
        if not image:
            return Response({"detail": "Nenhuma imagem enviada."}, status=400)
        photo = PostPhoto.objects.create(
            post=post,
            image=image,
            order=post.photos.count(),
        )
        return Response(PostPhotoSerializer(photo).data, status=201)

    @action(detail=True, methods=['delete'], url_path=r'remove_photo/(?P<photo_id>\d+)',
            permission_classes=[IsAuthenticated])
    def remove_photo(self, request, pk=None, photo_id=None):
        """DELETE /feed/posts/{id}/remove_photo/{photo_id}/"""
        post = self.get_object()
        if post.author != request.user:
            return Response({"detail": "Not authorized."}, status=403)
        try:
            photo = post.photos.get(id=photo_id)
        except PostPhoto.DoesNotExist:
            return Response({"detail": "Foto não encontrada."}, status=404)
        photo.delete()
        return Response(status=204)



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
