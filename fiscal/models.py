from django.db import models
from django.utils.translation import gettext_lazy as _

class NotaFiscal(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('processando', 'Processando na API'),
        ('emitida', 'Emitida com Sucesso'),
        ('erro', 'Erro na Emissão'),
        ('cancelada', 'Cancelada'),
    ]

    # Relacionamentos (Pode ser Compra ou PedidoColetivo - Usaremos GenericForeignKey ou campos opcionais)
    # Por simplicidade, vamos vincular à Compra (Unidade) e PedidoColetivo (Lote) via campos opcionais
    compra = models.OneToOneField('compras.Compra', on_delete=models.SET_NULL, null=True, blank=True, related_name='nota_fiscal', verbose_name="Compra")
    pedido_coletivo = models.OneToOneField('pedidos_coletivos.PedidoColetivo', on_delete=models.SET_NULL, null=True, blank=True, related_name='nota_fiscal', verbose_name="Pedido Coletivo")

    # Dados da Nota
    chave_acesso = models.CharField(max_length=100, blank=True, null=True, verbose_name="Chave de Acesso (SEFAZ)")
    numero_nota = models.CharField(max_length=50, blank=True, null=True, verbose_name="Número da Nota")
    serie = models.CharField(max_length=10, blank=True, null=True, verbose_name="Série")
    
    # Arquivos
    pdf_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="URL do PDF")
    xml_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="URL do XML")

    # Controle
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente', verbose_name="Status da Emissão")
    mensagem_erro = models.TextField(blank=True, null=True, verbose_name="Log de Erros")
    data_emissao = models.DateTimeField(blank=True, null=True, verbose_name="Data de Emissão")
    
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Nota Fiscal"
        verbose_name_plural = "Notas Fiscais"

    def __str__(self):
        return f"NF {self.numero_nota or 'Pendente'} - {self.status}"
