from rest_framework import serializers
from api.models.techniques import Tecnica

class TecnicaSerializer(serializers.ModelSerializer):
    total_votos = serializers.SerializerMethodField()
    criada_por = serializers.StringRelatedField(read_only=True)  # novo campo

    class Meta:
        model = Tecnica
        fields = [
            'id',
            'titulo',
            'descricao',
            'criada_por',          # incluído
            'votos_aprovacao',
            'votos_rejeicao',
            'total_votos',
            'status'
        ]
        read_only_fields = [
            'criada_por',
            'votos_aprovacao',
            'votos_rejeicao',
            'status'
        ]
    
    def create(self, validated_data):
        user = self.context['request'].user  # usuário autenticado
        return Tecnica.objects.create(criada_por=user, **validated_data)

    def get_total_votos(self, obj):
        return obj.total_votos()
    