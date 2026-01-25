from django.urls import path
from . import views

app_name = 'logistica_app'

urlpatterns = [
    path('painel/', views.painel_motoboy, name='painel_motoboy'),
    path('aceitar/<int:entrega_id>/', views.aceitar_entrega, name='aceitar_entrega'),
    path('atualizar/<int:entrega_id>/', views.atualizar_status, name='atualizar_status'),
]
