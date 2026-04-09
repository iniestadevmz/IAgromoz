from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated,IsAdminUser,IsAuthenticatedOrReadOnly
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import status
from api.models.marketplace import PedidoVendedor, Produto
from api.serializers.marketplace import PedidoVendedorSerializer
from rest_framework import viewsets
from api.models.marketplace import Produto as Product
from api.serializers.marketplace import ProductSerializer
from api.permissions import IsAdminOrOwner, IsAdminUserCustom, IsAdminOrPodeVender
from rest_framework.decorators import action
from api.models.marketplace import Avaliacao
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model

User = get_user_model()

class PedidoVendedorCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.pode_vender:
            return Response(
                {"detail": "Você já está autorizado a vender."},
                status=400
            )

        if PedidoVendedor.objects.filter(user=request.user).exists():
            return Response(
                {"detail": "Você já possui um pedido em análise."},
                status=400
            )

        serializer = PedidoVendedorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        PedidoVendedor.objects.create(
            user=request.user,
            contacto=serializer.validated_data['contacto'],
            mensagem=serializer.validated_data.get('mensagem', '')
        )

        return Response(
            {"detail": "Pedido enviado com sucesso."},
            status=status.HTTP_201_CREATED
        )

class MeuPedidoVendedorView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            pedido = PedidoVendedor.objects.get(user=request.user)
        except PedidoVendedor.DoesNotExist:
            return Response(
                {"detail": "Você ainda não solicitou autorização."},
                status=404
            )

        return Response({
            "status": pedido.status,
            "contacto": pedido.contacto,
            "mensagem": pedido.mensagem,
            "criado_em": pedido.criado_em,
        })


class AprovarVendedorView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pedido_id):
        try:
            pedido = PedidoVendedor.objects.get(id=pedido_id)
        except PedidoVendedor.DoesNotExist:
            return Response({"detail": "Pedido não encontrado"}, status=404)

        status_decisao = request.data.get("status")
        if status_decisao not in ['APROVADO', 'REJEITADO']:
            return Response(
                {"detail": "Status inválido. Use 'APROVADO' ou 'REJEITADO'."},
                status=400
            )

        # Atualiza status do pedido
        pedido.status = status_decisao
        pedido.analisado_em = timezone.now()
        pedido.save()

        # Atualiza autorização do usuário
        pedido.user.pode_vender = True if status_decisao == 'APROVADO' else False
        pedido.user.save()

        return Response({
            "detail": f"Pedido {status_decisao.lower()} com sucesso",
            "pedido_id": pedido.id,
            "status": pedido.status
        })

class ListPedidosVendedorView(APIView):
    permission_classes = [IsAdminUser]


    def get(self, request):
        pedidos = PedidoVendedor.objects.all().order_by('-criado_em')
        serializer = PedidoVendedorSerializer(pedidos, many=True)
        return Response(serializer.data)




class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by('-criado_em')
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAdminOrPodeVender]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated(), IsAdminOrPodeVender()]
        elif self.action in ['avaliar']:
            return [IsAuthenticated()]
        return [IsAdminOrOwner()]

    def perform_create(self, serializer):
        if not self.request.user.pode_vender:
            raise PermissionDenied("Você não está autorizado a vender produtos.")

        serializer.save(vendedor=self.request.user)

    @action(detail=False, methods=['get'])
    def categorias(self, request):
        categorias = [
            {"value": value, "label": label}
            for value, label in Produto.CATEGORIAS
        ]
        return Response(categorias)




class AvaliacaoViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def avaliar_produto(self, request, pk=None):
        produto = Produto.objects.filter(pk=pk).first()
        if not produto:
            return Response({"detail": "Produto não encontrado"}, status=404)
        return self._criar_avaliacao(request,usuario=request.user, produto=produto)

    @action(detail=True, methods=['post'])
    def avaliar_vendedor(self, request, pk=None):
        vendedor = User.objects.filter(pk=pk).first()
        if vendedor.pode_vender == False:
            return Response({"detail": "Usuário não é um vendedor"}, status=400)
        
        if not vendedor:
            return Response({"detail": "Vendedor não encontrado"}, status=404)
        return self._criar_avaliacao(request,usuario=request.user, vendedor=vendedor)

    def _criar_avaliacao(self, request, usuario, produto=None, vendedor=None):
        
        nota = request.data.get('nota')
        comentario = request.data.get('comentario', '')

        # valida nota
        try:
            nota = float(nota)
        except:
            return Response({"detail": "Nota inválida"}, status=400)
        if nota < 1 or nota > 5:
            return Response({"detail": "Nota deve estar entre 1 e 5"}, status=400)

        # impedir auto-avaliação
        if produto and produto.vendedor == usuario:
            return Response({"detail": "Você não pode avaliar seu próprio produto"}, status=400)
        if vendedor and vendedor == usuario:
            return Response({"detail": "Você não pode avaliar a si mesmo"}, status=400)

        # impedir duplicação
        if Avaliacao.objects.filter(usuario=usuario, produto=produto, vendedor=vendedor).exists():
            return Response({"detail": "Você já avaliou este item"}, status=400)

        # criar avaliação
        Avaliacao.objects.create(usuario=usuario, produto=produto, vendedor=vendedor,
                                nota=nota, comentario=comentario)

        return Response({"detail": "Avaliação enviada com sucesso"}, status=201)