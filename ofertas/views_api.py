# ofertas/views_api.py

from rest_framework import viewsets, permissions
from django.db.models import Avg
from .models import Oferta, Categoria, Vendedor, Banner # <-- Banner importado
from .serializers import (
    OfertaListSerializer, 
    OfertaDetailSerializer, 
    CategoriaSerializer, 
    VendedorSerializer,
    BannerSerializer # <-- BannerSerializer importado
)
# (Se você usa o django-filters, mantenha esta linha)
# from .filters import OfertaFilterSet 


class OfertaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint (Apenas Leitura) para Ofertas.
    """
    queryset = Oferta.objects.filter(
        publicada=True, 
        status__in=['ativa', 'sucesso']
    ).select_related('vendedor', 'categoria').annotate(
        media_avaliacoes=Avg('avaliacoes__nota') # Calcula a média
    ).order_by('-destaque', '-data_inicio')
    
    permission_classes = [permissions.AllowAny]
    # filterset_class = OfertaFilterSet # Descomente se você usa django-filters

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return OfertaDetailSerializer # Detalhes (com avaliações)
        return OfertaListSerializer # Lista


class CategoriaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint (Apenas Leitura) para Categorias.
    """
    queryset = Categoria.objects.filter(ativa=True)
    serializer_class = CategoriaSerializer
    permission_classes = [permissions.AllowAny]


class VendedorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint (Apenas Leitura) para Vendedores (Aprovados).
    """
    queryset = Vendedor.objects.filter(ativo=True, status_aprovacao='aprovado')
    serializer_class = VendedorSerializer
    permission_classes = [permissions.AllowAny]


# --- NOVO VIEWSET (Atualização) ---
class BannerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint (Apenas Leitura) para Banners (Ativos).
    """
    queryset = Banner.objects.filter(ativo=True).order_by('ordem')
    serializer_class = BannerSerializer
    permission_classes = [permissions.AllowAny]