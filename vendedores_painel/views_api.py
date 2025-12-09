# vendedores_painel/views_api.py

from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Sum, Count
from django.utils import timezone
from ofertas.models import Oferta
from compras.models import Cupom
from pedidos_coletivos.models import PedidoColetivo
from compras.models import Compra

# --- VERIFIQUE ESTA IMPORTAÇÃO ---
from .serializers import (
    DashboardStatsSerializer, 
    MinhaOfertaWriteSerializer,
    PainelCupomResgateSerializer # <-- O nome que estava dando erro
)
# --------------------------------

from compras.serializers import CupomSerializer 
from .permissions import IsVendedorAprovado

# (Restante do código das Views - DashboardViewSet, MinhasOfertasViewSet, PainelCupomViewSet)
# ... (O código das classes aqui provavelmente está correto)...

class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, IsVendedorAprovado]
    def list(self, request):
        # ... (lógica do dashboard) ...
        vendedor = request.user.vendedor
        total_cupons_vendidos = Cupom.objects.filter(
            Q(oferta__vendedor=vendedor) & (
                Q(compra__status_pagamento='aprovada') |
                Q(pedido_coletivo__status_pagamento='aprovado_mp', pedido_coletivo__status_lote='concretizado')
            )
        ).count()
        total_cupons_resgatados = Cupom.objects.filter(oferta__vendedor=vendedor, status='resgatado').count()
        receita_bruta_compras = Compra.objects.filter(oferta__vendedor=vendedor, status_pagamento='aprovada').aggregate(Sum('valor_total'))['valor_total__sum'] or 0.00
        receita_bruta_pedidos = PedidoColetivo.objects.filter(oferta__vendedor=vendedor, status_pagamento='aprovado_mp', status_lote='concretizado').aggregate(Sum('valor_total'))['valor_total__sum'] or 0.00
        receita_bruta_total = receita_bruta_compras + receita_bruta_pedidos
        stats = {
            'total_cupons_vendidos': total_cupons_vendidos,
            'total_cupons_resgatados': total_cupons_resgatados,
            'receita_bruta_total': receita_bruta_total,
        }
        serializer = DashboardStatsSerializer(stats)
        return Response(serializer.data)

class MinhasOfertasViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsVendedorAprovado]
    serializer_class = MinhaOfertaWriteSerializer
    def get_queryset(self):
        return Oferta.objects.filter(vendedor=self.request.user.vendedor).order_by('-data_criacao')
    def perform_create(self, serializer):
        serializer.save(
            vendedor=self.request.user.vendedor, 
            status='pendente', 
            publicada=False
        )

class PainelCupomViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsVendedorAprovado]
    serializer_class = CupomSerializer 
    def get_queryset(self):
        # ... (lógica do queryset) ...
        vendedor = self.request.user.vendedor
        queryset = Cupom.objects.filter(
            Q(oferta__vendedor=vendedor) & (
                Q(compra__isnull=False, compra__status_pagamento='aprovada') |
                Q(pedido_coletivo__isnull=False, pedido_coletivo__status_pagamento='aprovado_mp', pedido_coletivo__status_lote='concretizado')
            )
        ).select_related(
            'oferta', 'usuario', 'compra', 'pedido_coletivo'
        ).order_by('-data_criacao')
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        query = self.request.query_params.get('q')
        if query:
            queryset = queryset.filter(
                Q(codigo__icontains=query) |
                Q(usuario__username__icontains=query) |
                Q(usuario__email__icontains=query)
            ).distinct()
        return queryset

    @action(detail=False, methods=['post'], serializer_class=PainelCupomResgateSerializer) # <-- Usa o serializer aqui
    def resgatar_cupom_por_codigo(self, request):
        # ... (lógica do resgate) ...
        serializer = PainelCupomResgateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        codigo = serializer.validated_data['codigo']
        try:
            cupom = Cupom.objects.get(
                codigo=codigo, 
                oferta__vendedor=request.user.vendedor
            )
        except Cupom.DoesNotExist:
            return Response({'detail': 'Cupom não encontrado ou não pertence a este vendedor.'}, status=status.HTTP_404_NOT_FOUND)
        if cupom.status == 'disponivel':
            cupom.status = 'resgatado'
            cupom.data_resgate = timezone.now()
            cupom.save()
            return Response(CupomSerializer(cupom).data, status=status.HTTP_200_OK)
        elif cupom.status == 'resgatado':
            return Response({'detail': 'Este cupom já foi resgatado.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'detail': f'Este cupom não está disponível (Status: {cupom.get_status_display()}).'}, status=status.HTTP_400_BAD_REQUEST)