from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Avg
from api.models.marketplace import Product, ProductUnit, Rating, Transaction
from api.models.location import District

User = get_user_model()


class ProductUnitSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = ProductUnit
        fields = ['id', 'unit_type', 'custom_unit_name', 'name', 'multiplier', 'price', 'is_active']

    def get_name(self, obj):
        return obj.name

    def validate(self, data):
        unit_type = data.get('unit_type', getattr(self.instance, 'unit_type', 'UNIT'))
        custom = data.get('custom_unit_name', getattr(self.instance, 'custom_unit_name', None))
        if unit_type == 'OTHER' and not custom:
            raise serializers.ValidationError(
                {"custom_unit_name": "Este campo é obrigatório quando unit_type é OTHER."}
            )
        return data

    def validate_multiplier(self, value):
        if value <= 0:
            raise serializers.ValidationError("O multiplicador deve ser maior que zero.")
        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("O preço deve ser maior que zero.")
        return value


class ProductSerializer(serializers.ModelSerializer):
    seller = serializers.CharField(source='seller.get_full_name', read_only=True)
    average_rating = serializers.SerializerMethodField()
    total_ratings = serializers.SerializerMethodField()
    user_rated = serializers.SerializerMethodField()
    province = serializers.SerializerMethodField()
    district = serializers.PrimaryKeyRelatedField(
        queryset=District.objects.all(), allow_null=True, required=False
    )
    units = ProductUnitSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'seller', 'name', 'description', 'price', 'photo', 'created_at',
            'category', 'subcategory', 'subcategory_description',
            'district', 'province',
            'stock_quantity', 'base_unit',
            'units',
            'average_rating', 'total_ratings', 'user_rated',
        ]
        read_only_fields = [
            'seller', 'created_at', 'average_rating', 'total_ratings',
            'user_rated', 'province', 'units',
        ]

    def get_province(self, obj):
        if obj.district:
            return obj.district.province.name
        return None

    def get_average_rating(self, obj):
        avg = obj.ratings.aggregate(avg=Avg('score'))['avg'] or 0
        return round(avg, 1)

    def get_total_ratings(self, obj):
        return obj.ratings.count()

    def get_user_rated(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.ratings.filter(user=request.user).exists()
        return False

    def validate(self, data):
        category = data.get('category') or (self.instance.category if self.instance else '')
        subcategory = data.get('subcategory') or (self.instance.subcategory if self.instance else '')
        subcategory_description = data.get('subcategory_description') or (self.instance.subcategory_description if self.instance else '')

        LIVESTOCK = ['POULTRY', 'EGGS', 'SWINE', 'FISH', 'CATTLE', 'GOATS', 'SHEEP', 'BEEKEEPING', 'OTHER']
        AGRICULTURE = ['CITRUS', 'TUBERS', 'FRUITS', 'CEREALS', 'LEGUMES', 'VEGETABLES', 'OTHER']

        if category == 'LIVESTOCK' and subcategory and subcategory not in LIVESTOCK:
            raise serializers.ValidationError(
                {"subcategory": f"Invalid subcategory for LIVESTOCK. Must be one of: {', '.join(LIVESTOCK)}"}
            )
        if category == 'AGRICULTURE' and subcategory and subcategory not in AGRICULTURE:
            raise serializers.ValidationError(
                {"subcategory": f"Invalid subcategory for AGRICULTURE. Must be one of: {', '.join(AGRICULTURE)}"}
            )
        if subcategory == 'OTHER' and not subcategory_description:
            raise serializers.ValidationError(
                {"subcategory_description": "This field is required when subcategory is OTHER."}
            )
        return data


class TransactionSerializer(serializers.ModelSerializer):
    buyer_name = serializers.CharField(source='buyer.get_full_name', read_only=True)
    seller_name = serializers.CharField(source='seller.get_full_name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    unit_name = serializers.CharField(source='unit.name', read_only=True, default=None)

    class Meta:
        model = Transaction
        fields = [
            'id', 'buyer_name', 'seller_name', 'product_name',
            'unit_name', 'quantity', 'total_base_quantity',
            'amount', 'status', 'created_at',
        ]
        read_only_fields = [
            'amount', 'status', 'created_at',
            'total_base_quantity', 'unit_name',
        ]
