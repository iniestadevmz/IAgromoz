from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from api.views.auth import UserViewSet
from api.views.location import ProvinceViewSet, DistrictViewSet
from api.views.marketplace import ProductViewSet, ProductUnitViewSet, RatingViewSet, TransactionViewSet
from api.views.techniques import TechniqueViewSet, TechniqueVoteView
from api.views.token import CustomTokenObtainPairView
from api.views.chat import ChatMessageListCreateView, ChatSessionListCreateView
from api.views.feed import CommentViewSet, PostViewSet
from api.views.notifications import NotificationListView, NotificationMarkReadView
from api.views.enums import EnumsView
from api.views.audit import AuditLogListView
from api.views.visits import PageVisitListView
from api.views.dashboard import (
    AdminDashboardView, AdminMetricsView,
    AdminUserManagementViewSet, AdminProductManagementViewSet,
    AdminPostManagementViewSet, AdminTechniqueManagementViewSet,
    AdminTransactionManagementViewSet,
)
from api.views.seller_dashboard import SellerDashboardView
from api.views.payment import (
    InitiatePaymentView, PaymentDetailView,
    VerifyPaymentView, PaymentWebhookView, PaymentListView,
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'provinces', ProvinceViewSet)
router.register(r'districts', DistrictViewSet)
router.register(r'techniques', TechniqueViewSet)
router.register(r'feed/posts', PostViewSet, basename='posts')
router.register(r'feed/comments', CommentViewSet, basename='comments')
router.register(r'marketplace/products', ProductViewSet)
router.register(r'marketplace/product-units', ProductUnitViewSet, basename='product-units')
router.register(r'marketplace/ratings', RatingViewSet, basename='ratings')
router.register(r'marketplace/transactions', TransactionViewSet, basename='transactions')

admin_router = DefaultRouter()
admin_router.register(r'admin-dashboard/users',        AdminUserManagementViewSet,        basename='admin-users')
admin_router.register(r'admin-dashboard/products',     AdminProductManagementViewSet,     basename='admin-products')
admin_router.register(r'admin-dashboard/posts',        AdminPostManagementViewSet,        basename='admin-posts')
admin_router.register(r'admin-dashboard/techniques',   AdminTechniqueManagementViewSet,   basename='admin-techniques')
admin_router.register(r'admin-dashboard/transactions', AdminTransactionManagementViewSet, basename='admin-transactions')

# ---------------------------------------------------------------------------
# URL patterns
# ---------------------------------------------------------------------------
urlpatterns = [
    # Auth
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Chat
    path('chat/sessions/', ChatSessionListCreateView.as_view(), name='chat_sessions'),
    path('chat/messages/', ChatMessageListCreateView.as_view(), name='chat_messages'),

    # Techniques voting
    path('techniques/<int:technique_id>/vote/', TechniqueVoteView.as_view(), name='technique_vote'),

    # Notifications
    path('notifications/', NotificationListView.as_view(), name='notifications_list'),
    path('notifications/<int:pk>/read/', NotificationMarkReadView.as_view(), name='notification_read'),

    # Enums
    path('enums/', EnumsView.as_view(), name='enums'),

    # Audit trail
    path('audit-logs/', AuditLogListView.as_view(), name='audit_logs'),

    # Page visits
    path('page-visits/', PageVisitListView.as_view(), name='page_visits'),

    # Admin dashboard
    path('admin-dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('admin-dashboard/metrics/', AdminMetricsView.as_view(), name='admin_metrics'),

    # Seller / Producer dashboard
    path('seller-dashboard/', SellerDashboardView.as_view(), name='seller_dashboard'),

    # Payments
    path('payments/', PaymentListView.as_view(), name='payment_list'),
    path('payments/initiate/', InitiatePaymentView.as_view(), name='payment_initiate'),
    path('payments/webhook/', PaymentWebhookView.as_view(), name='payment_webhook'),
    path('payments/<uuid:reference>/', PaymentDetailView.as_view(), name='payment_detail'),
    path('payments/<uuid:reference>/verify/', VerifyPaymentView.as_view(), name='payment_verify'),
]

urlpatterns += router.urls
urlpatterns += admin_router.urls
