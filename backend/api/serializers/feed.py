from rest_framework import serializers
from api.models.feed import Post, Comment

# 🔹 Função para montar árvore
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
    nome_completo = serializers.CharField(source='autor.get_full_name', read_only=True)  # Aqui

    class Meta:
        model = Comment
        fields = ['id', 'post', 'autor', 'mensagem', 'parent', 'criado_em', 'atualizado_em', 'replies', 'nome_completo']
        read_only_fields = ['autor']

    def get_replies(self, obj):
        return CommentSerializer(getattr(obj, 'replies_list', []), many=True, context=self.context).data

    def create(self, validated_data):
        validated_data['autor'] = self.context['request'].user
        return super().create(validated_data)


class PostSerializer(serializers.ModelSerializer):
    comments = serializers.SerializerMethodField(read_only=True)
    nome_completo = serializers.CharField(source='autor.get_full_name', read_only=True)  

    class Meta:
        model = Post
        fields = ['id', 'titulo', 'conteudo', 'imagem', 'autor', 'criado_em', 'atualizado_em', 'comments', 'nome_completo']
        read_only_fields = ['autor']

    def get_comments(self, obj):
        all_comments = obj.comments.select_related('autor').all().order_by('criado_em')
        tree = build_comment_tree(list(all_comments))
        return CommentSerializer(tree, many=True, context=self.context).data

    def create(self, validated_data):
        validated_data['autor'] = self.context['request'].user
        return super().create(validated_data)