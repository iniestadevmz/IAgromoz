from rest_framework import serializers
from api.models.feed import Post, PostPhoto, PostProduct, Comment
from api.models.location import District

ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/webp'}
MAX_IMAGE_SIZE_MB = 5


def validate_image_file(image):
    if hasattr(image, 'content_type') and image.content_type not in ALLOWED_IMAGE_TYPES:
        raise serializers.ValidationError(
            f"Tipo de ficheiro não suportado. Use: {', '.join(ALLOWED_IMAGE_TYPES)}"
        )
    if image.size > MAX_IMAGE_SIZE_MB * 1024 * 1024:
        raise serializers.ValidationError(
            f"A imagem não pode exceder {MAX_IMAGE_SIZE_MB}MB."
        )
    return image


class PostPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostPhoto
        fields = ['id', 'image', 'order']

    def validate_image(self, value):
        return validate_image_file(value)


class PostProductSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(source='product.id', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(
        source='product.price', max_digits=10, decimal_places=2, read_only=True
    )
    product_district = serializers.SerializerMethodField()
    product_province = serializers.SerializerMethodField()

    class Meta:
        model = PostProduct
        fields = ['id', 'product_id', 'product_name', 'product_price',
                  'product_district', 'product_province', 'label']

    def get_product_district(self, obj):
        return obj.product.district.name if obj.product.district else None

    def get_product_province(self, obj):
        if obj.product.district:
            return obj.product.district.province.name
        return None


def build_comment_tree(comments):
    tree = []
    lookup = {}
    for c in comments:
        c.replies_list = []
        lookup[c.id] = c
    for c in comments:
        if c.parent_id:
            parent = lookup.get(c.parent_id)
            if parent:
                parent.replies_list.append(c)
        else:
            tree.append(c)
    return tree


class CommentSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()
    full_name = serializers.CharField(source='author.get_full_name', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'message', 'parent', 'created_at', 'updated_at', 'replies', 'full_name']
        read_only_fields = ['author']

    def get_replies(self, obj):
        return CommentSerializer(getattr(obj, 'replies_list', []), many=True, context=self.context).data

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class PostSerializer(serializers.ModelSerializer):
    comments = serializers.SerializerMethodField(read_only=True)
    full_name = serializers.CharField(source='author.get_full_name', read_only=True)
    total_likes = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    photos = PostPhotoSerializer(many=True, read_only=True)
    district = serializers.PrimaryKeyRelatedField(
        queryset=District.objects.all(), allow_null=True, required=False
    )
    province = serializers.SerializerMethodField()
    district_name = serializers.SerializerMethodField()
    linked_products = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'content', 'photos', 'author', 'full_name',
            'created_at', 'updated_at', 'category',
            'district', 'district_name', 'province',
            'linked_products',
            'comments', 'total_likes', 'liked',
        ]
        read_only_fields = ['author', 'photos', 'province', 'district_name', 'linked_products']

    def get_province(self, obj):
        if obj.district:
            return obj.district.province.name
        return None

    def get_district_name(self, obj):
        return obj.district.name if obj.district else None

    def get_total_likes(self, obj):
        return obj.likes.count()

    def get_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(id=request.user.id).exists()
        return False

    def get_comments(self, obj):
        all_comments = obj.comments.select_related('author').all().order_by('created_at')
        tree = build_comment_tree(list(all_comments))
        return CommentSerializer(tree, many=True, context=self.context).data

    def get_linked_products(self, obj):
        qs = obj.post_products.select_related('product__district__province')
        return PostProductSerializer(qs, many=True).data

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)
