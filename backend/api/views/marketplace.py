from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import action
from django.db import transaction as db_transaction
from django.db.models import Q
from django.contrib.auth import get_user_model
from api.models.marketplace import Product, ProductUnit, Rating, Transaction
from api.serializers.marketplace import ProductSerializer, ProductUnitSerializer, TransactionSerializer
from api.permissions import IsAdminOrCanSell, IsAdminOrOwner, IsAdminOrBuyerOrSeller

User = get_user_model()


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by('-created_at')
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAdminOrCanSell]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated(), IsAdminOrCanSell()]
        
        if self.action in ['categories', 'base_units']:
            return []
       
        if self.action=='buy':
            return [IsAuthenticated()]
        
        if self.action=="transactions":
            return [IsAdminOrBuyerOrSeller]
        
        return [IsAdminOrOwner()]
        

    def perform_create(self, serializer):
        if not self.request.user.can_sell:
            raise PermissionDenied("You are not authorized to sell products.")
        serializer.save(seller=self.request.user)

    def perform_update(self, serializer):
        product = self.get_object()
        if product.seller != self.request.user:
            raise PermissionDenied("You can only edit your own products.")
        serializer.save()

    @action(detail=False, methods=['get'], permission_classes=[])
    def categories(self, request):
        """GET /marketplace/products/categories/"""
        data = [
            {
                "value": "AGRICULTURE",
                "label": "Agricultura",
                "subcategories": [
                    {"value": v, "label": l}
                    for v, l in Product.AGRICULTURE_SUBCATEGORY_CHOICES
                ]
            },
            {
                "value": "LIVESTOCK",
                "label": "Pecuária",
                "subcategories": [
                    {"value": v, "label": l}
                    for v, l in Product.LIVESTOCK_SUBCATEGORY_CHOICES
                ]
            },
        ]
        return Response(data)

    @action(detail=False, methods=['get'], permission_classes=[])
    def base_units(self, request):
        """GET /marketplace/products/base_units/ — lista unidades base do sistema."""
        return Response([
            {"value": v, "label": l}
            for v, l in Product.BASE_UNIT_CHOICES
        ])

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def buy(self, request, pk=None):
        """
        POST /marketplace/products/{id}/buy/
        Body: {"unit_id": <int>, "quantity": <number>}
        Se unit_id omitido, usa price base do produto (quantidade em unidade base).
        """
        product = self.get_object()

        if product.seller == request.user:
            return Response({"detail": "You cannot buy your own product."}, status=400)

        unit_id = request.data.get('unit_id')
        try:
            quantity = float(request.data.get('quantity', 1))
            if quantity <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return Response({"detail": "Quantidade inválida."}, status=400)

        unit = None
        if unit_id:
            try:
                unit = ProductUnit.objects.get(id=unit_id, product=product, is_active=True)
            except ProductUnit.DoesNotExist:
                return Response({"detail": "Unidade de venda não encontrada ou inativa."}, status=400)

        # Calcular quantidades e preço
        if unit:
            from decimal import Decimal
            qty = Decimal(str(quantity))
            total_base = qty * unit.multiplier
            total_price = qty * unit.price
        else:
            from decimal import Decimal
            qty = Decimal(str(quantity))
            total_base = qty  # sem unit → 1:1 com unidade base
            total_price = qty * product.price

        # Validar stock
        if product.stock_quantity < total_base:
            return Response(
                {"detail": f"Stock insuficiente. Disponível: {product.stock_quantity} {product.base_unit}."},
                status=400
            )

        with db_transaction.atomic():
            # Deduzir stock
            product.stock_quantity -= total_base
            product.save(update_fields=['stock_quantity'])

            txn = Transaction.objects.create(
                buyer=request.user,
                seller=product.seller,
                product=product,
                unit=unit,
                quantity=qty,
                total_base_quantity=total_base,
                amount=total_price,
                status='RESERVED',
            )

        return Response({"detail": "Reservation created.", "id": txn.id}, status=201)

    @action(detail=True, methods=['get'], permission_classes=[IsAdminOrCanSell])
    def transactions(self, request, pk=None):
        product = self.get_object()
        if product.seller != request.user:
            return Response({"detail": "Not authorized."}, status=403)
        return Response([
            {
                "id": t.id, "buyer": t.buyer.id, "status": t.status,
                "amount": t.amount, "quantity": t.quantity,
                "unit": t.unit.name if t.unit else None,
                "total_base_quantity": t.total_base_quantity,
            }
            for t in product.transactions.all()
        ])


class ProductUnitViewSet(viewsets.ModelViewSet):
    """
    CRUD de unidades de venda de um produto.
    Apenas o vendedor do produto pode gerir as suas units.
    """
    serializer_class = ProductUnitSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], permission_classes=[])
    def sale_unit_choices(self, request):
        """GET /marketplace/product-units/sale_unit_choices/ — lista tipos de unidade de venda."""
        return Response([
            {"value": v, "label": l}
            for v, l in ProductUnit.SALE_UNIT_CHOICES
        ])

    def get_queryset(self):
        return ProductUnit.objects.filter(product__seller=self.request.user)

    def perform_create(self, serializer):
        product_id = self.request.data.get('product_id')
        try:
            product = Product.objects.get(id=product_id, seller=self.request.user)
        except Product.DoesNotExist:
            raise PermissionDenied("Produto não encontrado ou não é seu.")
        serializer.save(product=product)

    def perform_update(self, serializer):
        unit = self.get_object()
        if unit.product.seller != self.request.user:
            raise PermissionDenied("Não pode editar unidades de produtos de outros vendedores.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.product.seller != self.request.user:
            raise PermissionDenied("Não pode eliminar unidades de produtos de outros vendedores.")
        instance.delete()


class RatingViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def rate_product(self, request, pk=None):
        product = Product.objects.filter(pk=pk).first()
        if not product:
            return Response({"detail": "Product not found."}, status=404)
        return self._create_rating(request, user=request.user, product=product)

    @action(detail=True, methods=['post'])
    def rate_seller(self, request, pk=None):
        seller = User.objects.filter(pk=pk).first()
        if not seller:
            return Response({"detail": "Seller not found."}, status=404)
        if not seller.can_sell:
            return Response({"detail": "User is not a seller."}, status=400)
        return self._create_rating(request, user=request.user, seller=seller)

    def _create_rating(self, request, user, product=None, seller=None):
        try:
            score = float(request.data.get('score'))
        except (TypeError, ValueError):
            return Response({"detail": "Invalid score."}, status=400)
        if score < 1 or score > 5:
            return Response({"detail": "Score must be between 1 and 5."}, status=400)
        if product and product.seller == user:
            return Response({"detail": "You cannot rate your own product."}, status=400)
        if seller and seller == user:
            return Response({"detail": "You cannot rate yourself."}, status=400)
        if Rating.objects.filter(user=user, product=product, seller=seller).exists():
            return Response({"detail": "You have already rated this item."}, status=400)
        Rating.objects.create(user=user, product=product, seller=seller,
                              score=score, comment=request.data.get('comment', ''))
        return Response({"detail": "Rating submitted successfully."}, status=201)


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Transaction.objects.filter(Q(buyer=user) | Q(seller=user))

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        transaction = self.get_object()
        if transaction.seller != request.user:
            return Response({"detail": "Not authorized."}, status=403)
        transaction.status = 'AWAITING_PAYMENT'
        transaction.save()
        return Response({"detail": "Transaction confirmed."})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        transaction = self.get_object()
        if transaction.seller != request.user:
            return Response({"detail": "Not authorized."}, status=403)
        # Devolver stock ao produto
        if transaction.total_base_quantity:
            with db_transaction.atomic():
                transaction.product.stock_quantity += transaction.total_base_quantity
                transaction.product.save(update_fields=['stock_quantity'])
                transaction.status = 'CANCELLED'
                transaction.save()
        else:
            transaction.status = 'CANCELLED'
            transaction.save()
        return Response({"detail": "Transaction cancelled."})

    @action(detail=True, methods=['post'])
    def conclude(self, request, pk=None):
        transaction = self.get_object()
        if transaction.seller != request.user:
            return Response({"detail": "Only the seller can conclude a transaction."}, status=403)
        transaction.status = 'COMPLETED'
        transaction.save()
        return Response({"detail": "Transaction completed."})
