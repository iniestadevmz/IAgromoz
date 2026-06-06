from django.contrib import admin
from api.models import (
    User, SellerProfile, ProducerProfile, UpgradeRequest,
    Province, District,
    Product, Rating, Transaction,
    Technique, TechniqueVote,
    Notification,
    ChatSession, ChatMessage,
    Post, Comment,
    AuditLog,
    PageVisit,
)

admin.site.register(User)
admin.site.register(SellerProfile)
admin.site.register(ProducerProfile)
admin.site.register(UpgradeRequest)
admin.site.register(Province)
admin.site.register(District)
admin.site.register(Product)
admin.site.register(Rating)
admin.site.register(Transaction)
admin.site.register(Technique)
admin.site.register(TechniqueVote)
admin.site.register(Notification)
admin.site.register(ChatSession)
admin.site.register(ChatMessage)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(AuditLog)
admin.site.register(PageVisit)
