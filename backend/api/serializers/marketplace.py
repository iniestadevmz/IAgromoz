from rest_framework import serializers
from api.models.marketplace import PedidoVendedor, Produto
from api.models.marketplace import Produto, Avaliacao
from django.contrib.auth import get_user_model
from django.db.models import Avg


User = get_user_model()

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
    vendedor = serializers.CharField(source='autor.get_full_name', read_only=True)
    media_avaliacao = serializers.SerializerMethodField()
    total_avaliacoes = serializers.SerializerMethodField()
    user_avaliou = serializers.SerializerMethodField()

    class Meta:
        model = Produto
        fields = [
            "id",
            "vendedor",
            "nome",
            "descricao",
            "preco",
            "foto",
            "criado_em",
            "categoria",
            "media_avaliacao",
            "total_avaliacoes",
            "user_avaliou",
        ]
        read_only_fields = ["vendedor", "criado_em", "media_avaliacao", "total_avaliacoes", "user_avaliou"]

  

    def get_media_avaliacao(self, obj):
        media = obj.avaliacoes_produto.aggregate(media=Avg('nota'))['media'] or 0
        return round(media, 1)  # ex: 4.5

    def get_total_avaliacoes(self, obj):
        return obj.avaliacoes_produto.count()

    def get_user_avaliou(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.avaliacoes_produto.filter(usuario=request.user).exists()
        return False
    

class VendedorSerializer(serializers.ModelSerializer):
    media_avaliacao = serializers.SerializerMethodField()
    total_avaliacoes = serializers.SerializerMethodField()
    user_avaliou = serializers.SerializerMethodField()
    vendedor=serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'vendedor', 'media_avaliacao', 'total_avaliacoes', 'user_avaliou']
        read_only_fields = ['media_avaliacao', 'total_avaliacoes', 'user_avaliou']
    
    def get_media_avaliacao(self, obj):
        media = obj.avaliacoes_vendedor.aggregate(media=Avg('nota'))['media'] or 0
        return round(media, 1)  # ex: 4.5 estrelas
    
    def get_total_avaliacoes(self, obj):
        return obj.avaliacoes_vendedor.count()
    
    def get_user_avaliou(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.avaliacoes_vendedor.filter(usuario=request.user).exists()
        return False