from rest_framework import serializers
from api.models.marketplace import PedidoVendedor, Produto

class PedidoVendedorSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = PedidoVendedor
        fields = [
            'id',
            'user',
            'contacto',
            'mensagem',
            'status',
            'criado_em'
        ]
        read_only_fields = ['criado_em']



class ProductSerializer(serializers.ModelSerializer):
    vendedor = serializers.SerializerMethodField()  # Mostra email/nome, não permite setar

   

    class Meta:
        model = Produto
        fields = ["id", "vendedor", "nome", "descricao", "preco", "foto", "criado_em"]
        read_only_fields = ["vendedor", "criado_em"]
    
    def get_vendedor(self, obj):
        # Verifica se o vendedor existe e retorna o nome completo concatenado
        if obj.vendedor:
            return f"{obj.vendedor.first_name} {obj.vendedor.last_name}"
        return None
    
