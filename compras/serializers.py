# compras/serializers.py

from rest_framework import serializers
from .models import Compra, Cupom

# --- CORREÇÃO AQUI ---
# Trocamos 'OfertaSerializer' por 'OfertaListSerializer'
from ofertas.serializers import OfertaListSerializer
# ---------------------

from contas.serializers import UserSerializer

class CompraSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo 'Compra' (venda por unidade).
    (CORRIGIDO)
    """
    # --- CORREÇÃO AQUI ---
    oferta = OfertaListSerializer(read_only=True)
    # ---------------------
    
    usuario = UserSerializer(read_only=True)
    
    class Meta:
        model = Compra
        fields = [
            'id', 
            'usuario', 
            'oferta', 
            'quantidade', 
            'valor_total', 
            'data_compra', 
            'status_pagamento',
            'id_transacao_mp',
            'id_preferencia_mp',
            'metodo_pagamento',
        ]
        read_only_fields = fields


class CupomSerializer(serializers.ModelSerializer):
    """
    Serializer CORRIGIDO e principal para o modelo 'Cupom'.
    """
    # --- CORREÇÃO AQUI ---
    oferta = OfertaListSerializer(read_only=True)
    # ---------------------
    
    usuario = UserSerializer(read_only=True)
    compra = CompraSerializer(read_only=True) 
    
    pedido_coletivo_id = serializers.PrimaryKeyRelatedField(
        read_only=True, 
        source='pedido_coletivo'
    )

    class Meta:
        model = Cupom
        fields = [
            'id', 
            'codigo', 
            'status', 
            'valido_ate', 
            'data_criacao', 
            'data_resgate',
            'oferta',           
            'usuario',          
            'compra',           
            'pedido_coletivo_id' 
        ]
        read_only_fields = fields