# contas/api_urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_api # Importa o arquivo 'views_api.py'

# 1. Cria o roteador
router = DefaultRouter()

# 2. Registra os ViewSets que estarão em 'views_api.py'
router.register(r'notificacoes', views_api.NotificacaoViewSet, basename='api-notificacoes')

# 3. As URLs da API são determinadas automaticamente pelo roteador
urlpatterns = [
    # Rota para /api/v1/contas/me/ (para o usuário ver seus próprios dados)
    path('me/', views_api.MeView.as_view(), name='api-me'),
    
    # Inclui as rotas do roteador (ex: /api/v1/contas/notificacoes/)
    path('', include(router.urls)),
]