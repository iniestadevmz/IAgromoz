from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated,IsAdminUser,IsAuthenticatedOrReadOnly
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import status
from api.models.marketplace import PedidoVendedor
from api.serializers.marketplace import PedidoVendedorSerializer
from rest_framework import viewsets
from api.models.marketplace import Produto as Product
from api.serializers.marketplace import ProductSerializer
from api.permissions import IsAdminOrOwner, IsAdminUserCustom, IsAdminOrPodeVender

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
    parser_classes = [MultiPartParser, FormParser]  # allow uploading `foto` with request

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated()]  # qualquer usuário logado pode criar
        return [IsAdminOrOwner()]  # update/delete só para admin ou dono

    def perform_create(self, serializer):
        if not self.request.user.pode_vender:
            raise PermissionDenied("Você não está autorizado a vender produtos.")
              
         
        # Define automaticamente o vendedor como o usuário logado
        serializer.save(vendedor=self.request.user)





