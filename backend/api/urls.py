from django.urls import path
from api.views.auth import  LogoutView, UserViewSet
from api.views.location import ProvinciaViewSet, DistritoViewSet
from api.views.marketplace import (AprovarVendedorView, ListPedidosVendedorView, 
                                   MeuPedidoVendedorView, PedidoVendedorCreateView, ProductViewSet, AvaliacaoViewSet)
from api.views.techniques import VotarTecnicaView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.routers import DefaultRouter
from api.views.chat import ChatMessageListCreateView,ChatSessionListCreateView
from api.views.techniques import TecnicaViewSet
from api.views.feed import CommentViewSet, PostViewSet


rote =DefaultRouter()
rote.register(r'usuarios',UserViewSet)
rote.register(r'provincias',ProvinciaViewSet)
rote.register(r'distritos',DistritoViewSet)
rote.register(r'tecnicas',TecnicaViewSet)
rote.register(r'feed/posts', PostViewSet, basename='posts')
rote.register(r'feed/comments', CommentViewSet, basename='comments')
rote.register(r'marketplace/produtos',ProductViewSet)
rote.register(r'marketplace/avaliacoes',AvaliacaoViewSet, basename='avaliacoes')

urlpatterns = [
    path('chat/sessoes/', ChatSessionListCreateView.as_view(), name='chat_secssoes'),
    path('chat/mensagens/', ChatMessageListCreateView.as_view(), name='chat_mensagens'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('tecnicas/<int:tecnica_id>/votar/', VotarTecnicaView.as_view()),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("marketplace/pedido-vendedor/", PedidoVendedorCreateView.as_view()),
    path("marketplace/meu-pedido/", MeuPedidoVendedorView.as_view()),
    path("marketplace/pedidos/<int:pedido_id>/", AprovarVendedorView.as_view()),
    path("marketplace/pedidos/", ListPedidosVendedorView.as_view()),


]

urlpatterns += rote.urls
