# ofertas/urls.py

from django.urls import path
from . import views

app_name = 'ofertas' 

urlpatterns = [
    # Página inicial (lista todas as ofertas ou por unidade)
    path('', views.lista_ofertas, name='lista_ofertas'), 
    
    # Lista de ofertas filtradas por categoria
    path('categoria/<slug:slug_categoria>/', views.lista_ofertas, name='ofertas_por_categoria'), 
    
    # Página específica para "Compre Junto"
    path('compre-junto/', views.compre_junto_view, name='compre_junto'), 
    
    # Detalhe de uma oferta específica
    path('<slug:slug_oferta>/', views.detalhe_oferta, name='detalhe_oferta'), 
]