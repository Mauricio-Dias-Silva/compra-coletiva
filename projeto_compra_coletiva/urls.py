from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap

# Imports para Sitemap
from ofertas.sitemaps import OfertaSitemap, CategoriaSitemap, StaticViewSitemap

# --- Imports para JWT ---
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
# -----------------------

# Dicionário de sitemaps
sitemaps = {
    'ofertas': OfertaSitemap,
    'categorias': CategoriaSitemap,
    'static': StaticViewSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # ---- Apps Principais (Site HTML) ----
    path('contas/', include('contas.urls')), 
    path('contas/', include('allauth.urls')), # Inclui as URLs do allauth (login, cadastro, etc. do site)
    path('painel-vendedor/', include('vendedores_painel.urls')), # Painel do Vendedor (Site)
    path('compras/', include('compras.urls')), 
    path('pagamentos/', include('pagamentos.urls')),
    path('pedidos-coletivos/', include('pedidos_coletivos.web_urls')), # Pedidos Coletivos (Site)

    # ---- URLS DE AUTENTICAÇÃO DA API (JWT) ----
    # O Flutter usará estas para login/refresh
    path('api/v1/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/token/verify/', TokenVerifyView.as_view(), name='token_verify'), # Opcional
    # ------------------------------------------

    # ---- URLS DA API (RESTO DO PROJETO) ----
    # Inclui os endpoints que criamos para cada app
    path('api/v1/pedidos/', include('pedidos_coletivos.api_urls')),
    path('api/v1/ofertas/', include('ofertas.api_urls')),
    path('api/v1/contas/', include('contas.api_urls')),
    path('api/v1/painel/', include('vendedores_painel.api_urls')), # <--- Garantindo que esta está incluída
    # ----------------------------------------

    # ---- URL DO SITEMAP ----
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),

    # ---- URL Raiz (App 'ofertas' - DEVE SER A ÚLTIMA) ----
    # Captura a homepage e URLs de ofertas/categorias do site
    path('', include('ofertas.urls')), 
]

# Configuração para servir arquivos de mídia e estáticos em DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
