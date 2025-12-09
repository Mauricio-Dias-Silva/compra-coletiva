
# pedidos_coletivos/api_urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_api 

router = DefaultRouter()

# --- CORREÇÃO AQUI ---
# Usando os nomes corretos e ordem correta
router.register(r'meu-credito', views_api.CreditoUsuarioViewSet, basename='api-credito')
router.register(r'meu-historico-credito', views_api.HistoricoCreditoViewSet, basename='api-historico-credito')

# Rota genérica (r'') por ÚLTIMO
router.register(r'', views_api.PedidoColetivoViewSet, basename='api-pedidos')
# ---------------------

urlpatterns = [
    path('', include(router.urls)),
]