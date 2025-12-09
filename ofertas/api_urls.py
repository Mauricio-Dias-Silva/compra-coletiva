# ofertas/api_urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_api 

router = DefaultRouter()

# --- CORREÇÃO AQUI ---
# Rotas específicas PRIMEIRO
router.register(r'categorias', views_api.CategoriaViewSet, basename='api-categorias')
router.register(r'vendedores', views_api.VendedorViewSet, basename='api-vendedores')
router.register(r'banners', views_api.BannerViewSet, basename='api-banners')

# Rota genérica (r'') por ÚLTIMO
router.register(r'', views_api.OfertaViewSet, basename='api-ofertas')
# ---------------------

urlpatterns = [
    path('', include(router.urls)),
]