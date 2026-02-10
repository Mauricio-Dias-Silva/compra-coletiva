# pagamentos/admin.py

from django.contrib import admin
from .models import Pagamento, PlanoVendedor, AssinaturaVendedor


@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display = ['id', 'tipo', 'status', 'usuario', 'valor_bruto', 'comissao_plataforma', 'valor_liquido_vendedor', 'metodo_pagamento', 'data_criacao']
    list_filter = ['tipo', 'status', 'metodo_pagamento', 'data_criacao']
    search_fields = ['usuario__username', 'id_transacao_mp']
    readonly_fields = ['data_criacao', 'data_aprovacao']
    date_hierarchy = 'data_criacao'


@admin.register(PlanoVendedor)
class PlanoVendedorAdmin(admin.ModelAdmin):
    list_display = ['nome', 'preco_mensal', 'comissao_percentual', 'max_ofertas_ativas', 'selo_premium', 'ia_criacao_ofertas', 'ativo']
    list_editable = ['preco_mensal', 'comissao_percentual', 'ativo']


@admin.register(AssinaturaVendedor)
class AssinaturaVendedorAdmin(admin.ModelAdmin):
    list_display = ['vendedor', 'plano', 'status', 'data_inicio', 'data_renovacao']
    list_filter = ['status', 'plano']
    search_fields = ['vendedor__nome_empresa']
