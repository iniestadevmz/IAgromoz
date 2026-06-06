from rest_framework import serializers
from api.models.techniques import Technique


class TechniqueSerializer(serializers.ModelSerializer):
    total_votes = serializers.SerializerMethodField()
    created_by = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = Technique
        fields = ['id', 'title', 'description', 'created_by', 'approval_votes',
                  'rejection_votes', 'total_votes', 'status', 'image']
        read_only_fields = ['created_by', 'approval_votes', 'rejection_votes', 'status']

    def create(self, validated_data):
        user = self.context['request'].user
        return Technique.objects.create(created_by=user, **validated_data)

    def get_total_votes(self, obj):
        return obj.total_votes()
