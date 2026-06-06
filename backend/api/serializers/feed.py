from rest_framework import serializers
from api.models.feed import Post, Comment


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

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'image', 'author', 'created_at', 'updated_at',
                  'category', 'comments', 'full_name', 'total_likes', 'liked']
        read_only_fields = ['author']

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

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)
