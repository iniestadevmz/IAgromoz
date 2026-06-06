from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from django.db.models import Count, Avg, Sum, Q
from django.db.models.functions import  TruncDate, TruncMonth, TruncWeek
from django.utils import timezone
from datetime import timedelta, date

from api.permissions import IsAdmin
from api.models.marketplace import Product, Transaction, Rating
from api.models.payment import Payment
from api.models.feed import Post, Comment
from api.models.techniques import Technique
from api.models.notifications import Notification
from api.models.audit import AuditLog
from api.models.visits import PageVisit
from api.models.users import UpgradeRequest
from api.serializers.users import UserSerializer, UpgradeRequestSerializer
from api.serializers.marketplace import ProductSerializer, TransactionSerializer
from api.serializers.feed import PostSerializer
from api.serializers.techniques import TechniqueSerializer
from api.serializers.audit import AuditLogSerializer

User = get_user_model()


def _daily_series(queryset, date_field, days=30):
    """Returns a list of {date, count} for the last N days."""
    now = timezone.now()
    start = now - timedelta(days=days)
    data = (
        queryset.filter(**{f"{date_field}__gte": start})
        .annotate(day=TruncDate(date_field))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    return [{"date": str(r['day']), "count": r['count']} for r in data]


def _monthly_series(queryset, date_field, months=12):
    """Returns a list of {month, count} for the last N months."""
    now = timezone.now()
    start = now - timedelta(days=months * 30)
    data = (
        queryset.filter(**{f"{date_field}__gte": start})
        .annotate(month=TruncMonth(date_field))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    return [{"month": r['month'].strftime('%Y-%m'), "count": r['count']} for r in data]


class AdminDashboardView(APIView):
    """
    GET /admin-dashboard/
    Returns a full system overview for admins.
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        now = timezone.now()
        last_30 = now - timedelta(days=30)
        last_7 = now - timedelta(days=7)

        users = User.objects.all()
        products = Product.objects.all()
        transactions = Transaction.objects.all()
        posts = Post.objects.all()
        comments = Comment.objects.all()
        techniques = Technique.objects.all()
        upgrade_requests = UpgradeRequest.objects.all()

        revenue_completed = transactions.filter(status='COMPLETED').aggregate(
            total=Sum('amount')
        )['total'] or 0

        return Response({

            # ── Users ──────────────────────────────────────────────────────
            "users": {
                "total": users.count(),
                "active": users.filter(is_active=True).count(),
                "inactive": users.filter(is_active=False).count(),
                "by_role": {
                    role: users.filter(role=role).count()
                    for role in ['NORMAL', 'PRODUCER', 'SELLER', 'ADMIN']
                },
                "new_last_7_days": users.filter(audit_logs__timestamp__gte=last_7).distinct().count(),
                "new_last_30_days": users.filter(audit_logs__timestamp__gte=last_30).distinct().count(),
            },

            # ── Marketplace ────────────────────────────────────────────────
            "marketplace": {
                "total_products": products.count(),
                "products_last_30_days": products.filter(created_at__gte=last_30).count(),
                "total_transactions": transactions.count(),
                "transactions_by_status": {
                    s: transactions.filter(status=s).count()
                    for s, _ in Transaction.STATUS_CHOICES
                },
                "completed_revenue": float(revenue_completed),
                "revenue_last_30_days": float(
                    transactions.filter(status='COMPLETED', created_at__gte=last_30)
                    .aggregate(total=Sum('amount'))['total'] or 0
                ),
                "total_ratings": Rating.objects.count(),
                "average_product_rating": round(
                    Rating.objects.filter(product__isnull=False)
                    .aggregate(avg=Avg('score'))['avg'] or 0, 2
                ),
                "payments": {
                    "total": Payment.objects.count(),
                    "by_status": {
                        s: Payment.objects.filter(status=s).count()
                        for s, _ in Payment.STATUS_CHOICES
                    },
                    "by_method": {
                        m: Payment.objects.filter(method=m, status='SUCCESS').count()
                        for m, _ in Payment.METHOD_CHOICES
                    },
                    "total_paid": float(
                        Payment.objects.filter(status='SUCCESS')
                        .aggregate(total=Sum('amount'))['total'] or 0
                    ),
                    "paid_last_30_days": float(
                        Payment.objects.filter(status='SUCCESS', paid_at__gte=last_30)
                        .aggregate(total=Sum('amount'))['total'] or 0
                    ),
                },
            },

            # ── Feed ───────────────────────────────────────────────────────
            "feed": {
                "total_posts": posts.count(),
                "total_comments": comments.count(),
                "posts_last_7_days": posts.filter(created_at__gte=last_7).count(),
                "posts_last_30_days": posts.filter(created_at__gte=last_30).count(),
                "comments_last_30_days": comments.filter(created_at__gte=last_30).count(),
                "posts_by_category": {
                    cat: posts.filter(category=cat).count()
                    for cat, _ in Post.CATEGORY_CHOICES
                },
            },

            # ── Techniques ─────────────────────────────────────────────────
            "techniques": {
                "total": techniques.count(),
                "by_status": {
                    s: techniques.filter(status=s).count()
                    for s, _ in Technique.STATUS_CHOICES
                },
            },

            # ── Upgrade requests ───────────────────────────────────────────
            "upgrade_requests": {
                "total": upgrade_requests.count(),
                "pending": upgrade_requests.filter(status='PENDING').count(),
                "approved": upgrade_requests.filter(status='APPROVED').count(),
                "rejected": upgrade_requests.filter(status='REJECTED').count(),
            },

            # ── Activity ───────────────────────────────────────────────────
            "activity": {
                "logs_last_7_days": AuditLog.objects.filter(timestamp__gte=last_7).count(),
                "logs_last_30_days": AuditLog.objects.filter(timestamp__gte=last_30).count(),
                "logins_last_30_days": AuditLog.objects.filter(
                    action='LOGIN', timestamp__gte=last_30
                ).count(),
                "unique_visitors_today": PageVisit.objects.filter(
                    date=timezone.now().date()
                ).count(),
                "unique_visitors_last_7_days": PageVisit.objects.filter(
                    date__gte=last_7.date()
                ).count(),
                "unique_visitors_last_30_days": PageVisit.objects.filter(
                    date__gte=last_30.date()
                ).count(),
            },
        })


def _visits_series(days=30, monthly=False):
    """Returns unique visitor counts from PageVisit."""
    now = timezone.now()
    start = now - timedelta(days=days)
    qs = PageVisit.objects.filter(date__gte=start.date())
    if monthly:
        data = (
            qs.annotate(month=TruncMonth('date'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )
        return [{"month": r['month'].strftime('%Y-%m'), "count": r['count']} for r in data]
    data = (
        qs.values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )
    return [{"date": str(r['date']), "count": r['count']} for r in data]


class AdminMetricsView(APIView):
    """
    GET /admin-dashboard/metrics/
    Returns time-series growth data for charts.

    Query params:
      ?period=daily|monthly   (default: daily)
      ?days=7|30|90           (for daily, default: 30)
      ?months=3|6|12          (for monthly, default: 12)
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        period = request.query_params.get('period', 'daily')
        days = int(request.query_params.get('days', 30))
        months = int(request.query_params.get('months', 12))

        if period == 'monthly':
            fn = lambda qs, field: _monthly_series(qs, field, months)
        else:
            fn = lambda qs, field: _daily_series(qs, field, days)

        return Response({
            "period": period,
            "new_users":        fn(User.objects.all(),        'date_joined') if hasattr(User, 'date_joined') else [],
            "new_products":     fn(Product.objects.all(),     'created_at'),
            "new_posts":        fn(Post.objects.all(),        'created_at'),
            "new_comments":     fn(Comment.objects.all(),     'created_at'),
            "new_transactions": fn(Transaction.objects.all(), 'created_at'),
            "new_techniques":   fn(Technique.objects.all(),   'created_at'),
            "daily_accesses":   fn(AuditLog.objects.all(), 'timestamp'),
            "logins":           fn(AuditLog.objects.filter(action='LOGIN'), 'timestamp'),
            "unique_visitors":  _visits_series(days if period == 'daily' else months * 30, period == 'monthly'),
        })


class AdminUserManagementViewSet(viewsets.ViewSet):
    """
    Admin-only user management endpoints.
    GET    /admin-dashboard/users/              — list all users
    GET    /admin-dashboard/users/{id}/         — user detail
    POST   /admin-dashboard/users/{id}/deactivate/ — deactivate user
    POST   /admin-dashboard/users/{id}/activate/   — activate user
    DELETE /admin-dashboard/users/{id}/delete/     — delete user
    GET    /admin-dashboard/users/upgrade-requests/ — list pending upgrade requests
    """
    permission_classes = [IsAdmin]

    def list(self, request):
        role = request.query_params.get('role')
        is_active = request.query_params.get('is_active')
        qs = User.objects.all().order_by('-id')
        if role:
            qs = qs.filter(role=role.upper())
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == 'true')
        return Response(UserSerializer(qs, many=True).data)

    def retrieve(self, request, pk=None):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=404)
        return Response(UserSerializer(user).data)

    @action(detail=True, methods=['post'], url_path='deactivate')
    def deactivate(self, request, pk=None):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=404)
        if user.role == 'ADMIN':
            return Response({"detail": "Cannot deactivate another admin."}, status=400)
        user.is_active = False
        user.save()
        return Response({"detail": f"User '{user.email}' deactivated."})

    @action(detail=True, methods=['post'], url_path='activate')
    def activate(self, request, pk=None):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=404)
        user.is_active = True
        user.save()
        return Response({"detail": f"User '{user.email}' activated."})

    @action(detail=True, methods=['delete'], url_path='delete')
    def delete_user(self, request, pk=None):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=404)
        if user.role == 'ADMIN':
            return Response({"detail": "Cannot delete another admin."}, status=400)
        user.delete()
        return Response({"detail": "User deleted."}, status=204)

    @action(detail=False, methods=['get'], url_path='upgrade-requests')
    def upgrade_requests(self, request):
        status_filter = request.query_params.get('status', 'PENDING')
        qs = UpgradeRequest.objects.filter(
            status=status_filter.upper()
        ).select_related('user').order_by('-created_at')
        return Response(UpgradeRequestSerializer(qs, many=True).data)


class AdminProductManagementViewSet(viewsets.ViewSet):
    """
    Admin-only product management.
    GET    /admin-dashboard/products/       — list all products
    DELETE /admin-dashboard/products/{id}/  — delete a product
    """
    permission_classes = [IsAdmin]

    def list(self, request):
        category = request.query_params.get('category')
        seller_id = request.query_params.get('seller')
        qs = Product.objects.select_related('seller', 'district').order_by('-created_at')
        if category:
            qs = qs.filter(category=category.upper())
        if seller_id:
            qs = qs.filter(seller_id=seller_id)
        return Response(ProductSerializer(qs, many=True, context={'request': request}).data)

    def destroy(self, request, pk=None):
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=404)
        product.delete()
        return Response({"detail": "Product deleted."}, status=204)


class AdminPostManagementViewSet(viewsets.ViewSet):
    """
    Admin-only post management.
    GET    /admin-dashboard/posts/       — list all posts
    DELETE /admin-dashboard/posts/{id}/  — delete a post
    """
    permission_classes = [IsAdmin]

    def list(self, request):
        category = request.query_params.get('category')
        qs = Post.objects.select_related('author').order_by('-created_at')
        if category:
            qs = qs.filter(category=category.upper())
        return Response(PostSerializer(qs, many=True, context={'request': request}).data)

    def destroy(self, request, pk=None):
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response({"detail": "Post not found."}, status=404)
        post.delete()
        return Response({"detail": "Post deleted."}, status=204)


class AdminTechniqueManagementViewSet(viewsets.ViewSet):
    """
    Admin-only technique management.
    GET    /admin-dashboard/techniques/              — list all techniques
    POST   /admin-dashboard/techniques/{id}/validate/ — force validate
    POST   /admin-dashboard/techniques/{id}/discard/  — force discard
    DELETE /admin-dashboard/techniques/{id}/          — delete
    """
    permission_classes = [IsAdmin]

    def list(self, request):
        status_filter = request.query_params.get('status')
        qs = Technique.objects.select_related('created_by').order_by('-created_at')
        if status_filter:
            qs = qs.filter(status=status_filter.upper())
        return Response(TechniqueSerializer(qs, many=True, context={'request': request}).data)

    def destroy(self, request, pk=None):
        try:
            technique = Technique.objects.get(pk=pk)
        except Technique.DoesNotExist:
            return Response({"detail": "Technique not found."}, status=404)
        technique.delete()
        return Response({"detail": "Technique deleted."}, status=204)

    @action(detail=True, methods=['post'], url_path='validate')
    def validate_technique(self, request, pk=None):
        try:
            technique = Technique.objects.get(pk=pk)
        except Technique.DoesNotExist:
            return Response({"detail": "Technique not found."}, status=404)
        technique.status = 'VALIDATED'
        technique.save()
        return Response({"detail": "Technique validated."})

    @action(detail=True, methods=['post'], url_path='discard')
    def discard_technique(self, request, pk=None):
        try:
            technique = Technique.objects.get(pk=pk)
        except Technique.DoesNotExist:
            return Response({"detail": "Technique not found."}, status=404)
        technique.status = 'DISCARDED'
        technique.save()
        return Response({"detail": "Technique discarded."})


class AdminTransactionManagementViewSet(viewsets.ViewSet):
    """
    Admin-only transaction overview.
    GET /admin-dashboard/transactions/       — list all transactions
    GET /admin-dashboard/transactions/{id}/  — detail
    """
    permission_classes = [IsAdmin]

    def list(self, request):
        status_filter = request.query_params.get('status')
        qs = Transaction.objects.select_related('buyer', 'seller', 'product').order_by('-created_at')
        if status_filter:
            qs = qs.filter(status=status_filter.upper())
        return Response(TransactionSerializer(qs, many=True).data)

    def retrieve(self, request, pk=None):
        try:
            tx = Transaction.objects.get(pk=pk)
        except Transaction.DoesNotExist:
            return Response({"detail": "Transaction not found."}, status=404)
        return Response(TransactionSerializer(tx).data)
