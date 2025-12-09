# pedidos_coletivos/views_api.py

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from django.utils import timezone
from decimal import Decimal

# --- CORREÇÃO AQUI ---
# Importamos APENAS os modelos que ESTE app usa, do lugar certo.
from .models import PedidoColetivo, CreditoUsuario, HistoricoCredito # <-- Modelos DESTE app
from ofertas.models import Oferta # <-- Modelo de OUTRO app, necessário aqui
# (NÃO precisamos importar Usuario ou Notificacao aqui)
# ---------------------

# Importa os serializers corretos (que já corrigimos antes)
from .serializers import (
    PedidoColetivoListSerializer,
    PedidoColetivoDetailSerializer,
    CreatePedidoColetivoSerializer,
    CreditoUsuarioSerializer,
    HistoricoCreditoSerializer
)


class PedidoColetivoViewSet(viewsets.ModelViewSet):
    """
    API endpoint para Pedidos Coletivos (CRUD).
    """
    queryset = PedidoColetivo.objects.all().order_by('-data_pedido')
    permission_classes = [permissions.IsAuthenticated] # Só usuários logados

    def get_queryset(self):
        # Filtra para mostrar apenas os pedidos do usuário logado
        return PedidoColetivo.objects.filter(usuario=self.request.user).order_by('-data_pedido')

    def get_serializer_class(self):
        # Usa serializers diferentes para List/Detail/Create
        if self.action == 'list':
            return PedidoColetivoListSerializer
        if self.action == 'create':
            return CreatePedidoColetivoSerializer
        return PedidoColetivoDetailSerializer 

    def create(self, request, *args, **kwargs):
        # (Lógica de criação do pedido que já tínhamos feito...)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        oferta = serializer.validated_data['oferta']
        quantidade = serializer.validated_data['quantidade']
        usar_credito = serializer.validated_data.get('usar_credito', False)
        
        credito_usuario, created = CreditoUsuario.objects.get_or_create(usuario=request.user)
        saldo_disponivel = credito_usuario.saldo
        valor_total_pedido = Decimal(oferta.preco_desconto * quantidade)
        
        valor_a_pagar_mp = valor_total_pedido
        usar_credito_total = False
        valor_credito_usado = Decimal(0.0)

        if usar_credito and saldo_disponivel > 0:
            if saldo_disponivel >= valor_total_pedido:
                valor_a_pagar_mp = Decimal(0.0)
                usar_credito_total = True
                valor_credito_usado = valor_total_pedido
            else:
                valor_a_pagar_mp = valor_total_pedido - saldo_disponivel
                valor_credito_usado = saldo_disponivel
        
        try:
            with transaction.atomic():
                pedido = serializer.save(
                    usuario=request.user,
                    valor_unitario=oferta.preco_desconto,
                    valor_total=valor_total_pedido,
                    status_pagamento='pendente',
                    status_lote='aberto'
                )

                if usar_credito_total:
                    credito_usuario.usar_credito(valor_credito_usado, 
                                                 f"Pagamento API Pedido Coletivo '{oferta.titulo}' (Pedido #{pedido.id})")
                    pedido.status_pagamento = 'aprovado_mp'
                    pedido.metodo_pagamento = 'Credito do Site'
                    pedido.save()
                    oferta.quantidade_vendida += pedido.quantidade
                    oferta.save()
                    headers = self.get_success_headers(serializer.data)
                    detail_serializer = PedidoColetivoDetailSerializer(pedido, context={'request': request})
                    return Response(detail_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
                
                elif valor_a_pagar_mp > 0:
                    # (Lógica simulada do Mercado Pago...)
                    payment_url = "https://mercadopago.com/pagar/simulado"
                    preference_id = f"PREF_SIMULADA_{pedido.id}"
                    pedido.id_preferencia_mp = preference_id
                    pedido.save()
                    headers = self.get_success_headers(serializer.data)
                    detail_serializer = PedidoColetivoDetailSerializer(pedido, context={'request': request})
                    response_data = detail_serializer.data
                    response_data['payment_url'] = payment_url 
                    return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)
                else: # Valor 0.00
                    pedido.status_pagamento = 'aprovado_mp'
                    pedido.metodo_pagamento = 'Gratuito' # Ou similar
                    pedido.save()
                    headers = self.get_success_headers(serializer.data)
                    detail_serializer = PedidoColetivoDetailSerializer(pedido, context={'request': request})
                    return Response(detail_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

        except Exception as e:
            # (Logar o erro aqui seria bom)
            return Response({'error': f'Erro ao criar pedido: {e}'}, status=status.HTTP_400_BAD_REQUEST)


class CreditoUsuarioViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint (Apenas Leitura) para Créditos do Usuário.
    """
    queryset = CreditoUsuario.objects.all()
    serializer_class = CreditoUsuarioSerializer
    permission_classes = [permissions.IsAuthenticated] # Só usuários logados

    def get_queryset(self):
        # Filtra para mostrar apenas o crédito do usuário logado
        return CreditoUsuario.objects.filter(usuario=self.request.user)


class HistoricoCreditoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint (Apenas Leitura) para Histórico de Créditos.
    """
    queryset = HistoricoCredito.objects.all()
    serializer_class = HistoricoCreditoSerializer
    permission_classes = [permissions.IsAuthenticated] # Só usuários logados

    def get_queryset(self):
        # Filtra para mostrar apenas o histórico do usuário logado
        credito_usuario, created = CreditoUsuario.objects.get_or_create(usuario=self.request.user)
        return HistoricoCredito.objects.filter(credito_usuario=credito_usuario).order_by('-data_transacao')