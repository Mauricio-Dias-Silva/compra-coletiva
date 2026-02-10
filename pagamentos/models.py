# pagamentos/models.py

from django.db import models
from django.utils import timezone
from decimal import Decimal


class Pagamento(models.Model):
    """Registro centralizado de todas as transações financeiras da plataforma."""
    TIPO_CHOICES = [
        ('compra_unidade', 'Compra por Unidade'),
        ('compra_lote', 'Compra Coletiva (Lote)'),
        ('assinatura_plano', 'Assinatura de Plano Vendedor'),
        ('destaque_oferta', 'Destaque de Oferta'),
        ('estorno', 'Estorno'),
    ]
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aprovado', 'Aprovado'),
        ('recusado', 'Recusado'),
        ('estornado', 'Estornado'),
        ('cancelado', 'Cancelado'),
    ]

    tipo = models.CharField(max_length=25, choices=TIPO_CHOICES, verbose_name="Tipo")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pendente', verbose_name="Status")

    # Quem pagou
    usuario = models.ForeignKey(
        'contas.Usuario', on_delete=models.CASCADE,
        related_name='pagamentos', verbose_name="Usuário"
    )

    # Valores
    valor_bruto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Bruto")
    comissao_plataforma = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Comissão VarejoUnido"
    )
    valor_liquido_vendedor = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Valor Líquido (Vendedor)"
    )

    # Referência ao pedido
    compra = models.ForeignKey(
        'compras.Compra', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='pagamentos_ref',
        verbose_name="Compra Unitária"
    )
    pedido_coletivo = models.ForeignKey(
        'pedidos_coletivos.PedidoColetivo', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='pagamentos_ref',
        verbose_name="Pedido Coletivo"
    )

    # Mercado Pago
    id_transacao_mp = models.CharField(max_length=255, blank=True, null=True, verbose_name="ID Transação MP")
    metodo_pagamento = models.CharField(max_length=50, blank=True, null=True, verbose_name="Método")

    # Timestamps
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_aprovacao = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Pagamento"
        verbose_name_plural = "Pagamentos"
        ordering = ['-data_criacao']

    def __str__(self):
        return f"PAG-{self.id} | R${self.valor_bruto} | {self.get_status_display()}"

    def calcular_comissao(self, percentual_comissao=None):
        """Calcula comissão da plataforma e valor líquido do vendedor."""
        if percentual_comissao is None:
            percentual_comissao = Decimal('10.00')  # 10% padrão
        self.comissao_plataforma = (self.valor_bruto * percentual_comissao) / Decimal('100')
        self.valor_liquido_vendedor = self.valor_bruto - self.comissao_plataforma
        return self


class PlanoVendedor(models.Model):
    """Planos de assinatura para vendedores na plataforma."""
    PLANO_CHOICES = [
        ('gratis', 'Grátis'),
        ('premium', 'Premium'),
        ('profissional', 'Profissional'),
    ]

    nome = models.CharField(max_length=20, choices=PLANO_CHOICES, unique=True, verbose_name="Plano")
    preco_mensal = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Preço Mensal (R$)")
    comissao_percentual = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name="Comissão (%)",
        help_text="Percentual cobrado sobre cada venda"
    )
    max_ofertas_ativas = models.IntegerField(default=5, verbose_name="Máx. Ofertas Ativas")
    destaque_automatico = models.BooleanField(default=False, verbose_name="Destaque Automático")
    selo_premium = models.BooleanField(default=False, verbose_name="Selo Premium")
    ia_criacao_ofertas = models.BooleanField(default=False, verbose_name="IA para Criar Ofertas")
    analytics_avancado = models.BooleanField(default=False, verbose_name="Analytics Avançado")
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Plano de Vendedor"
        verbose_name_plural = "Planos de Vendedor"
        ordering = ['preco_mensal']

    def __str__(self):
        return f"{self.get_nome_display()} — R${self.preco_mensal}/mês ({self.comissao_percentual}% comissão)"


class AssinaturaVendedor(models.Model):
    """Assinatura ativa de um vendedor a um plano."""
    STATUS_CHOICES = [
        ('ativa', 'Ativa'),
        ('cancelada', 'Cancelada'),
        ('expirada', 'Expirada'),
        ('pendente', 'Pendente Pagamento'),
    ]

    vendedor = models.OneToOneField(
        'ofertas.Vendedor', on_delete=models.CASCADE,
        related_name='assinatura', verbose_name="Vendedor"
    )
    plano = models.ForeignKey(
        PlanoVendedor, on_delete=models.PROTECT,
        related_name='assinaturas', verbose_name="Plano"
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ativa')
    data_inicio = models.DateTimeField(default=timezone.now)
    data_renovacao = models.DateTimeField(verbose_name="Próxima Renovação")
    data_cancelamento = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Assinatura de Vendedor"
        verbose_name_plural = "Assinaturas de Vendedores"

    def __str__(self):
        return f"{self.vendedor.nome_empresa} — {self.plano.get_nome_display()}"

    @property
    def esta_ativa(self):
        return self.status == 'ativa' and self.data_renovacao > timezone.now()
