from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_api # Importa o novo arquivo de views da API

# 1. Cria o roteador
router = DefaultRouter()

# 2. Registra os ViewSets
# Linha com ERRO
# Linha CORRIGIDA
router.register(r'dashboard', views_api.DashboardViewSet, basename='api-dashboard') # <= Mudei aqui e no basename
router.register(r'minhas-ofertas', views_api.MinhasOfertasViewSet, basename='api-minhas-ofertas')
router.register(r'cupons', views_api.PainelCupomViewSet, basename='api-painel-cupons') # <= Corrigido aqui

# 3. As URLs da API são determinadas automaticamente pelo roteador
urlpatterns = [
    path('', include(router.urls)),
]