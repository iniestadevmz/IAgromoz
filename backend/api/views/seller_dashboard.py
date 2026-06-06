"""
Dashboard do Vendedor / Produtor
GET /api/seller-dashboard/

Acessível a utilizadores com role = SELLER ou PRODUCER (can_sell = True).
Devolve apenas dados relativos ao próprio utilizador autenticado.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta

from api.models.marketplace import Product, Transaction, Rating
from api.models.payment import Payment


class SellerDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if not getattr(user, 'can_sell', False):
            raise PermissionDenied("Apenas vendedores e produtores têm acesso a este dashboard.")

        now = timezone.now()
        last_30 = now - timedelta(days=30)
        last_7  = now - timedelta(days=7)

        products     = Product.objects.filter(seller=user)
        transactions = Transaction.objects.filter(seller=user)
        payments     = Payment.objects.filter(transaction__seller=user)

        # ── Produtos ──────────────────────────────────────────────────
        products_data = {
            "total": products.count(),
            "new_last_30_days": products.filter(created_at__gte=last_30).count(),
            "low_stock": list(
                products.filter(stock_quantity__lte=10)
                .values('id', 'name', 'stock_quantity', 'base_unit')
            ),
        }

        # ── Transações ────────────────────────────────────────────────
        transactions_data = {
            "total": transactions.count(),
            "by_status": {
                s: transactions.filter(status=s).count()
                for s, _ in Transaction.STATUS_CHOICES
            },
            "new_last_7_days":  transactions.filter(created_at__gte=last_7).count(),
            "new_last_30_days": transactions.filter(created_at__gte=last_30).count(),
            "revenue_completed": float(
                transactions.filter(status='COMPLETED')
                .aggregate(total=Sum('amount'))['total'] or 0
            ),
            "revenue_last_30_days": float(
                transactions.filter(status='COMPLETED', created_at__gte=last_30)
                .aggregate(total=Sum('amount'))['total'] or 0
            ),
            "recent": [
                {
                    "id": t.id,
                    "status": t.status,
                    "amount": t.amount,
                    "created_at": t.created_at,
                    "product_name": t.product.name,
                    "buyer_name": t.buyer.get_full_name() or t.buyer.email,
                }
                for t in transactions.select_related('buyer', 'product').order_by('-created_at')[:10]
            ],
        }

        # ── Pagamentos ────────────────────────────────────────────────
        payments_data = {
            "total": payments.count(),
            "by_status": {
                s: payments.filter(status=s).count()
                for s, _ in Payment.STATUS_CHOICES
            },
            "by_method": {
                m: payments.filter(method=m, status='SUCCESS').count()
                for m, _ in Payment.METHOD_CHOICES
            },
            "total_received": float(
                payments.filter(status='SUCCESS')
                .aggregate(total=Sum('amount'))['total'] or 0
            ),
            "received_last_30_days": float(
                payments.filter(status='SUCCESS', paid_at__gte=last_30)
                .aggregate(total=Sum('amount'))['total'] or 0
            ),
        }

        # ── Avaliações ────────────────────────────────────────────────
        ratings_data = {
            "average_as_seller": round(
                user.ratings_received.aggregate(avg=Avg('score'))['avg'] or 0, 1
            ),
            "total_as_seller": user.ratings_received.count(),
            "average_products": round(
                Rating.objects.filter(product__seller=user)
                .aggregate(avg=Avg('score'))['avg'] or 0, 1
            ),
            "total_products_rated": Rating.objects.filter(product__seller=user).count(),
        }

        return Response({
            "seller": {
                "id": user.id,
                "name": user.get_full_name(),
                "email": user.email,
                "role": user.role,
            },
            "products":     products_data,
            "transactions": transactions_data,
            "payments":     payments_data,
            "ratings":      ratings_data,
        })
