"""
URL configuration for iagromoz project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse, Http404
from django.conf import settings
from django.conf.urls.static import static




def admin_404(request, *args, **kwargs):
    """Esconde o painel de admin Django do URL padrão."""
    raise Http404


urlpatterns = [
    # Painel Django Admin acessível apenas via URL configurável no .env
    # Em produção define DJANGO_ADMIN_URL=gestao-interna/ (ou outro valor não óbvio)
    # Por defeito mantém /admin/ em desenvolvimento
    path(
        __import__('os').getenv('DJANGO_ADMIN_URL', 'vital/'),
        admin.site.urls
    ),
    path('api/', include('api.urls')),
]
