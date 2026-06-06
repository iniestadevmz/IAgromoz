from rest_framework import serializers
from api.models.users import User, SellerProfile, ProducerProfile, UpgradeRequest
from api.models.location import District
from .location import DistrictSerializer
from api.models.marketplace import average_seller_rating, total_seller_ratings


# ── Base user fields shared across registration serializers ──────────────────

class BaseRegisterSerializer(serializers.ModelSerializer):
    district_id = serializers.PrimaryKeyRelatedField(
        queryset=District.objects.all(), source='district', required=False, allow_null=True
    )
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'first_name', 'last_name', 'district_id', 'gender']

    def _create_user(self, validated_data, role):
        password = validated_data.pop('password')
        validated_data['role'] = role
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


# ── Registration serializers (one per role) ───────────────────────────────────

class NormalRegisterSerializer(BaseRegisterSerializer):
    def create(self, validated_data):
        return self._create_user(validated_data, role='NORMAL')


class ProducerRegisterSerializer(BaseRegisterSerializer):
    contact = serializers.CharField(write_only=True)
    farm_address = serializers.CharField(write_only=True)

    class Meta(BaseRegisterSerializer.Meta):
        fields = BaseRegisterSerializer.Meta.fields + ['contact', 'farm_address']

    def create(self, validated_data):
        contact = validated_data.pop('contact')
        farm_address = validated_data.pop('farm_address')
        user = self._create_user(validated_data, role='PRODUCER')
        ProducerProfile.objects.create(user=user, contact=contact, farm_address=farm_address)
        return user


class SellerRegisterSerializer(BaseRegisterSerializer):
    seller_type = serializers.ChoiceField(choices=SellerProfile.SELLER_TYPE_CHOICES, write_only=True)
    store_name = serializers.CharField(write_only=True)
    nuit = serializers.CharField(write_only=True, required=False, allow_blank=True)
    contact = serializers.CharField(write_only=True)
    store_address = serializers.CharField(write_only=True)

    class Meta(BaseRegisterSerializer.Meta):
        fields = BaseRegisterSerializer.Meta.fields + [
            'seller_type', 'store_name', 'nuit', 'contact', 'store_address'
        ]

    def create(self, validated_data):
        profile_data = {
            'seller_type': validated_data.pop('seller_type'),
            'store_name': validated_data.pop('store_name'),
            'nuit': validated_data.pop('nuit', ''),
            'contact': validated_data.pop('contact'),
            'store_address': validated_data.pop('store_address'),
        }
        user = self._create_user(validated_data, role='SELLER')
        SellerProfile.objects.create(user=user, **profile_data)
        return user


# ── Profile view/update serializers ──────────────────────────────────────────

class UserSerializer(serializers.ModelSerializer):
    district = DistrictSerializer(read_only=True)
    district_id = serializers.PrimaryKeyRelatedField(
        queryset=District.objects.all(), source='district', write_only=True, required=False
    )
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    total_ratings = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'district', 'district_id',
                  'role', 'can_sell', 'gender', 'full_name', 'profile_photo',
                  'total_ratings', 'average_rating']
        read_only_fields = ['id', 'role', 'can_sell']

    def get_total_ratings(self, obj):
        return total_seller_ratings(obj) if obj.can_sell else None

    def get_average_rating(self, obj):
        return average_seller_rating(obj) if obj.can_sell else None


from rest_framework import serializers

class PublicProfileSerializer(serializers.Serializer):
    user = serializers.SerializerMethodField()
    producer_profile = serializers.SerializerMethodField()
    seller_profile = serializers.SerializerMethodField()
    profile_photo = serializers.SerializerMethodField()

    def get_profile_photo(self, obj):
        if obj.profile_photo and hasattr(obj.profile_photo, 'url'):
            return obj.profile_photo.url
        return None

    def get_user(self, obj):
        return {
            "id": obj.id,
            "full_name": obj.get_full_name(),
            "first_name": obj.first_name,
            "last_name": obj.last_name,
            # "profile_photo": self.get_profile_photo(obj),
            "district": obj.district.name if obj.district else None,
            "role": obj.role,
        }

    def get_producer_profile(self, obj):
        if obj.role == 'PRODUCER' and hasattr(obj, 'producer_profile'):
            return {
                "contact": obj.producer_profile.contact,
                "farm_address": obj.producer_profile.farm_address,
            }
        return None

    def get_seller_profile(self, obj):
        if obj.role == 'SELLER' and hasattr(obj, 'seller_profile'):
            return {
                "store_name": obj.seller_profile.store_name,
                "seller_type": obj.seller_profile.seller_type,
                "store_address": obj.seller_profile.store_address,
                "contact": obj.seller_profile.contact,
            }
        return None

class SellerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerProfile
        fields = ['id', 'seller_type', 'store_name', 'nuit', 'contact', 'store_address']


class ProducerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProducerProfile
        fields = ['id', 'contact', 'farm_address']


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_old_password(self, value):
        if not self.context['request'].user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value


class UpgradeRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = UpgradeRequest
        fields = ['id', 'contact', 'farm_address', 'status', 'created_at', 'reviewed_at']
        read_only_fields = ['id', 'status', 'created_at', 'reviewed_at']
