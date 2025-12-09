# pedidos_coletivos/serializers.py

from rest_framework import serializers
from .models import PedidoColetivo, CreditoUsuario, HistoricoCredito
from contas.serializers import UserSerializer
from decimal import Decimal
from django.db import transaction
from django.utils import timezone

# --- CORREÇÃO AQUI ---
# Trocamos 'OfertaSerializer' por 'OfertaListSerializer'
from ofertas.serializers import OfertaListSerializer, VendedorSerializer
# ---------------------

# Importa o serializer de cupom recém-corrigido
from compras.serializers import CupomSerializer 

# --- Serializers de Crédito (Sem alterações) ---

class CreditoUsuarioSerializer(serializers.ModelSerializer):
    usuario = UserSerializer(read_only=True)
    class Meta:
        model = CreditoUsuario
        fields = ['id', 'usuario', 'saldo', 'data_atualizacao']
        read_only_fields = fields

class HistoricoCreditoSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoricoCredito
        fields = [
            'id', 
            'data_transacao', 
            'tipo_transacao', 
            'valor', 
            'saldo_apos_transacao', 
            'descricao'
        ]
        read_only_fields = fields

# --- Serializers de Pedido (CORRIGIDOS) ---

class PedidoColetivoListSerializer(serializers.ModelSerializer):
    """
    Serializer de LISTA para Pedidos Coletivos (CORRIGIDO).
    """
    # --- CORREÇÃO AQUI ---
    # Trocamos 'OfertaSerializer' por 'OfertaListSerializer'
    oferta = OfertaListSerializer(read_only=True)
    # ---------------------
    
    usuario = UserSerializer(read_only=True) # 'usuario' em vez de 'criador'
    cupom_coletivo = CupomSerializer(read_only=True)

    class Meta:
        model = PedidoColetivo
        fields = [
            'id',
            'oferta',
            'usuario',
            'quantidade',
            'valor_total',
            'data_pedido',
            'status_pagamento',
            'status_lote',
            'cupom_coletivo' 
        ]

class PedidoColetivoDetailSerializer(PedidoColetivoListSerializer):
    """
    Serializer de DETALHE para Pedidos Coletivos (herda a correção).
    """
    class Meta(PedidoColetivoListSerializer.Meta):
        fields = PedidoColetivoListSerializer.Meta.fields


class CreatePedidoColetivoSerializer(serializers.ModelSerializer):
    """
    Serializer de ESCRITA (Criação) para Pedidos Coletivos.
    (Este não precisa de correção, mas precisa do import 'Oferta' de models)
    """
    # Importa o modelo Oferta para o queryset
    from ofertas.models import Oferta 
    
    oferta_id = serializers.PrimaryKeyRelatedField(
        queryset=Oferta.objects.filter(
            tipo_oferta='lote', 
            publicada=True, 
            status='ativa'
        ),
        source='oferta',
        write_only=True
    )
    usar_credito = serializers.BooleanField(write_only=True, default=False)

    class Meta:
        model = PedidoColetivo
        fields = [
            'oferta_id',
            'quantidade',
            'usar_credito',
        ]