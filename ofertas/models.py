# ofertas/models.py

from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.urls import reverse
from typing import Tuple, Optional, Union
from decimal import Decimal


# === Modelo Vendedor ===
class Vendedor(models.Model):
    STATUS_APROVACAO_CHOICES: Tuple[Tuple[str, str], ...] = [
        ('pendente', 'Pendente de Aprovação'),
        ('aprovado', 'Aprovado'),
        ('suspenso', 'Suspenso'),
        ('rejeitado', 'Rejeitado'),
    ]
    nome_empresa: models.CharField = models.CharField(max_length=200, verbose_name="Nome da Empresa")
    cnpj: models.CharField = models.CharField(max_length=18, unique=True, verbose_name="CNPJ (somente números)")
    email_contato: models.EmailField = models.EmailField(verbose_name="Email de Contato")
    telefone: models.CharField = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone")
    descricao: models.TextField = models.TextField(blank=True, null=True, verbose_name="Descrição da Empresa")
    logo: models.ImageField = models.ImageField(upload_to='vendedores/logos/', blank=True, null=True, verbose_name="Logo do Vendedor")
    endereco: models.CharField = models.CharField(max_length=255, verbose_name="Endereço Completo")
    ativo: models.BooleanField = models.BooleanField(default=True, verbose_name="Ativo no Site")
    selo_verificado: models.BooleanField = models.BooleanField(default=False, verbose_name="Selo de Verificação (B2B/Partner)")

    status_aprovacao: models.CharField = models.CharField(
        max_length=10,
        choices=STATUS_APROVACAO_CHOICES,
        default='pendente',
        verbose_name="Status de Aprovação"
    )

    data_cadastro: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    data_atualizacao: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name: str = "Vendedor"
        verbose_name_plural: str = "Vendedores"
        ordering: list[str] = ['nome_empresa']

    def __str__(self) -> str:
        return self.nome_empresa


# === Modelo Categoria ===
class Categoria(models.Model):
    nome: models.CharField = models.CharField(max_length=100, unique=True, verbose_name="Nome da Categoria")
    slug: models.SlugField = models.SlugField(max_length=100, unique=True, help_text="URL amigável (gerado automaticamente ou manual)", blank=True)
    descricao: models.TextField = models.TextField(blank=True, null=True, verbose_name="Descrição da Categoria")
    ativa: models.BooleanField = models.BooleanField(default=True, verbose_name="Ativa no Site")

    class Meta:
        verbose_name: str = "Categoria"
        verbose_name_plural: str = "Categorias"
        ordering: list[str] = ['nome']

    def __str__(self) -> str:
        return self.nome

    def save(self, *args, **kwargs):
        if not self.slug:  # Se o slug não estiver preenchido
            self.slug: str = slugify(self.nome)  # Ele tenta gerar
        super().save(*args, **kwargs)


# === Modelo Oferta ===
class Oferta(models.Model):
    TIPO_OFERTA_CHOICES: Tuple[Tuple[str, str], ...] = [
        ('unidade', 'Venda por Unidade (Imediata)'),
        ('lote', 'Compra Coletiva por Lote'),
    ]
    tipo_oferta: models.CharField = models.CharField(
        max_length=10,
        choices=TIPO_OFERTA_CHOICES,
        default='unidade',
        verbose_name="Tipo de Oferta"
    )

    vendedor: models.ForeignKey = models.ForeignKey(Vendedor, on_delete=models.CASCADE, related_name='ofertas', verbose_name="Vendedor")
    categoria: models.ForeignKey = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, related_name='ofertas', verbose_name="Categoria")
    titulo: models.CharField = models.CharField(max_length=255, verbose_name="Título da Oferta")
    # IMAGEM PRINCIPAL: Apenas uma declaração do campo
    imagem_principal: models.ImageField = models.ImageField(upload_to='ofertas/imagens/', verbose_name="Imagem Principal da Oferta", blank=True, null=True)
    slug: models.SlugField = models.SlugField(max_length=255, unique=True, help_text="URL amigável da oferta", blank=True)
    descricao_detalhada: models.TextField = models.TextField(verbose_name="Descrição Detalhada da Oferta")
    destaque: models.BooleanField = models.BooleanField(default=False, verbose_name="Oferta em Destaque")
    preco_original: models.DecimalField = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço Original")
    preco_desconto: models.DecimalField = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço com Desconto")
    data_inicio: models.DateTimeField = models.DateTimeField(default=timezone.now, verbose_name="Data de Início da Oferta")
    data_termino: models.DateTimeField = models.DateTimeField(verbose_name="Data de Término da Oferta")

    quantidade_minima_ativacao: models.IntegerField = models.IntegerField(default=1, verbose_name="Quantidade Mínima de Cupons para Ativação")
    quantidade_maxima_cupons: models.IntegerField = models.IntegerField(blank=True, null=True, verbose_name="Quantidade Máxima de Cupons (Limite)")

    quantidade_vendida: models.IntegerField = models.IntegerField(default=0, verbose_name="Quantidade de Cupons Vendidos")

    publicada: models.BooleanField = models.BooleanField(default=False, verbose_name="Publicada (Visível no Site)")

    STATUS_CHOICES: Tuple[Tuple[str, str], ...] = [
        ('pendente', 'Pendente'),
        ('ativa', 'Ativa'),
        ('sucesso', 'Sucesso (mínimo atingido)'),
        ('expirada', 'Expirada'),
        ('cancelada', 'Cancelada'),
        ('falha_lote', 'Falha (mínimo não atingido)'),
    ]
    status: models.CharField = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente', verbose_name="Status da Oferta")

    # === LOGÍSTICA & ENTREGA (NOVO) ===
    TIPO_ENTREGA_CHOICES = [
        ('retirada', 'Retirada no Local (Vendedor)'),
        ('entrega', 'Entrega (Delivery/Moto)'),
        ('ambos', 'Retirada ou Entrega'),
    ]
    tipo_entrega = models.CharField(max_length=15, choices=TIPO_ENTREGA_CHOICES, default='retirada', verbose_name="Tipo de Entrega")
    valor_frete = models.DecimalField(max_digits=6, decimal_places=2, default=0.00, verbose_name="Valor do Frete (Se houver)")
    endereco_retirada = models.CharField(max_length=255, blank=True, null=True, verbose_name="Endereço de Retirada (Opcional)")
    
    data_criacao: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    data_atualizacao: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name: str = "Oferta"
        verbose_name_plural: str = "Ofertas"
        ordering: list[str] = ['-data_inicio']

    def __str__(self) -> str:
        return self.titulo

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug: str = slugify(self.titulo)
        super().save(*args, **kwargs)

    @property
    def percentual_desconto(self) -> str:
        if self.preco_original > 0:
            return f"{((self.preco_original - self.preco_desconto) / self.preco_original) * 100:.0f}%"
        return "0%"

    @property
    def esta_expirada(self) -> bool:
        return timezone.now() > self.data_termino

    @property
    def esta_disponivel_para_compra(self) -> bool:
        if self.tipo_oferta == 'unidade':
            return self.publicada and self.status == 'ativa' and not self.esta_expirada and \
                   (self.quantidade_maxima_cupons is None or self.quantidade_vendida < self.quantidade_maxima_cupons)
        elif self.tipo_oferta == 'lote':
            return self.publicada and self.status == 'ativa' and not self.esta_expirada and \
                   (self.quantidade_maxima_cupons is None or self.quantidade_vendida < self.quantidade_maxima_cupons)
        return False

    def verificar_lote_e_finalizar(self):
        if self.tipo_oferta == 'lote' and self.status == 'ativa' and self.esta_expirada:
            if self.quantidade_vendida >= self.quantidade_minima_ativacao:
                self.status = 'sucesso'
                print(f"LOTE SUCESSO: Oferta '{self.titulo}' atingiu o mínimo. Processar capturas e cupons.")
            else:
                self.status = 'falha_lote'
                print(f"LOTE FALHA: Oferta '{self.titulo}' NÃO atingiu o mínimo. Processar estornos.")
            self.save()

    # MÉTODO PARA SEO E NOTIFICAÇÕES (get_absolute_url)
    def get_absolute_url(self) -> str:
        return reverse('ofertas:detalhe_oferta', kwargs={'slug_oferta': self.slug})


# === Modelo Avaliacao ===
class Avaliacao(models.Model):
    oferta: models.ForeignKey = models.ForeignKey(Oferta, on_delete=models.CASCADE, related_name='avaliacoes', verbose_name="Oferta Avaliada")
    usuario: models.ForeignKey = models.ForeignKey('contas.Usuario', on_delete=models.CASCADE, related_name='minhas_avaliacoes', verbose_name="Usuário Avaliador")
    nota: models.IntegerField = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)], verbose_name="Nota (1-5)")
    comentario: models.TextField = models.TextField(blank=True, null=True, verbose_name="Comentário")
    data_avaliacao: models.DateTimeField = models.DateTimeField(auto_now_add=True, verbose_name="Data da Avaliação")

    class Meta:
        verbose_name: str = "Avaliação"
        verbose_name_plural: str = "Avaliações"
        unique_together: list[tuple[str, str]] = ('oferta', 'usuario')
        ordering: list[str] = ['-data_avaliacao']

    def __str__(self) -> str:
        return f"Avaliação de {self.usuario.username} para {self.oferta.titulo} - Nota: {self.nota}"


# === Modelo Banner ===
class Banner(models.Model):
    titulo: models.CharField = models.CharField(max_length=200, verbose_name="Título do Banner")
    imagem: models.ImageField = models.ImageField(upload_to='banners/', verbose_name="Imagem do Banner")
    url_destino: models.URLField = models.URLField(max_length=200, blank=True, null=True, verbose_name="URL de Destino")
    ativo: models.BooleanField = models.BooleanField(default=True, verbose_name="Ativo")
    ordem: models.IntegerField = models.IntegerField(default=0, verbose_name="Ordem de Exibição")

    class Meta:
        verbose_name: str = "Banner"
        verbose_name_plural: str = "Banners"
        ordering: list[str] = ['ordem']

    def __str__(self) -> str:
        return self.titulo
