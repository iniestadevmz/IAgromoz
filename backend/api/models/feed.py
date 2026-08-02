from django.db import models
from django.conf import settings


class Post(models.Model):
    CATEGORY_CHOICES = [
        ('AGRICULTURE', 'Agricultura'),
        ('LIVESTOCK', 'Pecuária'),
    ]

    title = models.CharField(max_length=200)
    content = models.TextField(blank=True, null=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='liked_posts',
        blank=True
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, null=True, blank=True)
    district = models.ForeignKey(
        'api.District', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='posts'
    )

    def __str__(self):
        return f"{self.title} - {self.author.email}"


class PostPhoto(models.Model):
    """Fotos adicionais de um post (máx. 5)."""
    post = models.ForeignKey(Post, related_name='photos', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='iagromoz/feed/')
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Photo {self.id} — {self.post.title}"


class PostProduct(models.Model):
    """Liga um post do feed a um produto do marketplace."""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_products')
    product = models.ForeignKey(
        'api.Product', on_delete=models.CASCADE, related_name='feed_posts'
    )
    label = models.CharField(max_length=100, blank=True, default='Ver produto')

    class Meta:
        unique_together = ('post', 'product')

    def __str__(self):
        return f"Post #{self.post_id} → Product #{self.product_id}"


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.author.email} - {self.message[:30]}"
