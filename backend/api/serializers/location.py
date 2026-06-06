from rest_framework import serializers
from api.models.location import Province, District


class ProvinceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Province
        fields = ['id', 'name']


class DistrictSerializer(serializers.ModelSerializer):
    province = ProvinceSerializer(read_only=True)
    province_id = serializers.PrimaryKeyRelatedField(
        queryset=Province.objects.all(),
        source='province',
        write_only=True,
        required=True
    )

    class Meta:
        model = District
        fields = ['id', 'name', 'province', 'province_id']
