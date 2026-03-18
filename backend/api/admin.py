from django.contrib import admin
from api.models.marketplace import PedidoVendedor
from api.models.users import User
from api.models.location import Provincia, Distrito
from api.models.chat import ChatSession, ChatMessage

admin.site.register(User)
admin.site.register(Provincia)
admin.site.register(Distrito)
admin.site.register(ChatSession)
admin.site.register(ChatMessage)
admin.site.register(PedidoVendedor)

