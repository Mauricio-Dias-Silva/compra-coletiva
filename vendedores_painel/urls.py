# vendedores_painel/urls.py

from django.urls import path
from . import views

app_name = 'vendedores_painel'

urlpatterns = [
    # Dashboard principal do vendedor
    path('', views.dashboard_vendedor, name='dashboard'),
    
    # Gerenciamento de Ofertas
    path('ofertas/nova/', views.criar_oferta, name='criar_oferta'),
    path('ofertas/nova-ia/', views.nova_oferta_ia, name='nova_oferta_ia'), # <--- NOVA ROTA IA
    path('ofertas/<int:pk>/editar/', views.editar_oferta, name='editar_oferta'),
    
    # Expedição e Logística
    path('expedicao/', views.expedition_list, name='expedition_list'),
    path('expedicao/<int:oferta_id>/chamar-motoboy/', views.request_courier, name='request_courier'),
    
    # Gerenciamento de Cupons
    path('cupons/', views.gerenciar_cupons, name='gerenciar_cupons'),
    
    # Fluxo de Resgate de Cupom
    path('cupons/buscar/', views.buscar_cupom_para_resgate, name='buscar_cupom'), 
    path('cupons/resgatar/<int:cupom_id>/', views.resgatar_cupom, name='resgatar_cupom'),
]