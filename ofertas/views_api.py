# ofertas/views_api.py

from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from django.db.models import Avg
from django.core.files.uploadedfile import InMemoryUploadedFile
import logging

from .models import Oferta, Categoria, Vendedor, Banner
from .serializers import (
    OfertaListSerializer, 
    OfertaDetailSerializer, 
    CategoriaSerializer, 
    VendedorSerializer,
    BannerSerializer
)

logger = logging.getLogger(__name__)


class OfertaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint (Apenas Leitura) para Ofertas.
    """
    queryset = Oferta.objects.filter(
        publicada=True, 
        status__in=['ativa', 'sucesso']
    ).select_related('vendedor', 'categoria').annotate(
        media_avaliacoes=Avg('avaliacoes__nota')
    ).order_by('-destaque', '-data_inicio')
    
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return OfertaDetailSerializer
        return OfertaListSerializer


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


class BannerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint (Apenas Leitura) para Banners (Ativos).
    """
    queryset = Banner.objects.filter(ativo=True).order_by('ordem')
    serializer_class = BannerSerializer
    permission_classes = [permissions.AllowAny]


# ============================================================
# NOVAS VIEWS DE OCR PARA SCANNER DE PRODUTOS
# ============================================================

class ScanFlyerAPIView(APIView):
    """
    API para escanear encarte de supermercado e extrair produtos.
    
    POST /api/v1/ofertas/scan-flyer/
    - Enviar imagem do encarte como multipart/form-data (campo: image)
    - Retorna lista de produtos identificados com preços
    
    Exemplo de uso (curl):
    curl -X POST http://localhost:8000/api/v1/ofertas/scan-flyer/ \
         -H "Authorization: Bearer {TOKEN}" \
         -F "image=@/path/to/flyer.jpg"
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser]
    
    ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/jpg']
    MAX_SIZE_MB = 5
    
    def post(self, request):
        # Validar presença da imagem
        if 'image' not in request.FILES:
            return Response(
                {'error': 'Nenhuma imagem enviada. Use o campo "image".'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        image_file: InMemoryUploadedFile = request.FILES['image']
        
        # Validar tipo de arquivo
        if image_file.content_type not in self.ALLOWED_TYPES:
            return Response(
                {'error': f'Tipo de imagem inválido ({image_file.content_type}). Permitidos: JPEG, PNG, WebP.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar tamanho
        max_size = self.MAX_SIZE_MB * 1024 * 1024
        if image_file.size > max_size:
            return Response(
                {'error': f'Imagem muito grande ({image_file.size / 1024 / 1024:.1f}MB). Máximo: {self.MAX_SIZE_MB}MB.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from .product_scanner import ProductScannerService
            scanner = ProductScannerService()
            result = scanner.extract_product_info(image_file.read())
            
            return Response({
                'success': True,
                'products_count': len(result['products']),
                'products': result['products'],
                'validity_date': result.get('validity_date'),
                'raw_text_preview': result['raw_text'][:500] if result['raw_text'] else '',
            })
            
        except ValueError as e:
            logger.warning(f"OCR não configurado: {e}")
            return Response(
                {'error': str(e), 'code': 'OCR_NOT_CONFIGURED'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"Erro ao processar imagem de encarte: {e}", exc_info=True)
            return Response(
                {'error': 'Erro ao processar imagem. Tente novamente.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ScanProductAPIView(APIView):
    """
    API para escanear foto de produto individual.
    
    POST /api/v1/ofertas/scan-product/
    - Enviar foto do produto como multipart/form-data (campo: image)
    - Retorna informações extraídas (nome sugerido, data de validade se visível)
    
    Exemplo de uso (curl):
    curl -X POST http://localhost:8000/api/v1/ofertas/scan-product/ \
         -H "Authorization: Bearer {TOKEN}" \
         -F "image=@/path/to/product.jpg"
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser]
    
    ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/jpg']
    MAX_SIZE_MB = 5
    
    def post(self, request):
        # Validar presença da imagem
        if 'image' not in request.FILES:
            return Response(
                {'error': 'Nenhuma imagem enviada. Use o campo "image".'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        image_file = request.FILES['image']
        
        # Validar tipo de arquivo
        if image_file.content_type not in self.ALLOWED_TYPES:
            return Response(
                {'error': f'Tipo de imagem inválido ({image_file.content_type}). Permitidos: JPEG, PNG, WebP.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar tamanho
        max_size = self.MAX_SIZE_MB * 1024 * 1024
        if image_file.size > max_size:
            return Response(
                {'error': f'Imagem muito grande ({image_file.size / 1024 / 1024:.1f}MB). Máximo: {self.MAX_SIZE_MB}MB.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from .product_scanner import ProductScannerService
            scanner = ProductScannerService()
            
            image_bytes = image_file.read()
            text = scanner.extract_text_from_image(image_bytes)
            validity_date = scanner.extract_validity_date(text)
            store_name = scanner.extract_store_name(text)
            
            # Tenta extrair nome do produto
            lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 3]
            # Filtra linhas que parecem ser nomes de produtos (não só números)
            product_name = None
            for line in lines:
                if not line.replace(' ', '').isdigit() and len(line) > 5:
                    product_name = line[:100]
                    break
            
            return Response({
                'success': True,
                'suggested_name': product_name,
                'validity_date': validity_date,
                'store_name': store_name,
                'raw_text_preview': text[:500] if text else '',
            })
            
        except ValueError as e:
            logger.warning(f"OCR não configurado: {e}")
            return Response(
                {'error': str(e), 'code': 'OCR_NOT_CONFIGURED'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"Erro ao processar imagem do produto: {e}", exc_info=True)
            return Response(
                {'error': 'Erro ao processar imagem. Tente novamente.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )