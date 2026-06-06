from django.db import models
from django.conf import settings


class Post(models.Model):
    CATEGORY_CHOICES = [
        ('AGRICULTURE', 'Agricultura'),
        ('LIVESTOCK', 'Pecuária'),
    ]

    title = models.CharField(max_length=200)
    content = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='iagromoz/feed/', blank=True, null=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='liked_posts',
        blank=True
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.author.email}"


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
