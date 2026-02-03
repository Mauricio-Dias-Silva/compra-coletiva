import os
import django
from decimal import Decimal
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projeto_compra_coletiva.settings')
django.setup()

from ofertas.models import Oferta, Vendedor, Categoria
from django.contrib.auth import get_user_model

def seed_heatmap():
    print("🔥 Seeding Heatmap Data...")
    
    # Ensure a vendor exists
    vendedor, _ = Vendedor.objects.get_or_create(
        nome_empresa="Tech Deals Ltda",
        defaults={'cnpj': '00000000000191', 'email_contato': 'tech@deals.com'}
    )
    
    # Ensure category
    cat, _ = Categoria.objects.get_or_create(nome="Eletrônicos", slug="eletronicos")
    
    # 1. THE HOT DEAL (On Fire)
    Oferta.objects.create(
        titulo="iPhone 15 Pro Max - Lote Promocional",
        slug="iphone-15-pro-fire",
        vendedor=vendedor,
        categoria=cat,
        tipo_oferta='lote',
        descricao_detalhada="Oferta imperdível se atingirmos 100 compradores.",
        preco_original=Decimal("9000.00"),
        preco_desconto=Decimal("7500.00"),
        quantidade_minima_ativacao=50,
        quantidade_vendida=45, # 90% -> HOT
        data_termino=timezone.now() + timezone.timedelta(days=2),
        publicada=True,
        status='ativa'
    )
    
    # 2. THE WARM DEAL (Heating Up)
    Oferta.objects.create(
        titulo="Monitor Ultrawide 34'",
        slug="monitor-ultrawide-warm",
        vendedor=vendedor,
        categoria=cat,
        tipo_oferta='lote',
        descricao_detalhada="Dê um upgrade no setup.",
        preco_original=Decimal("3500.00"),
        preco_desconto=Decimal("2800.00"),
        quantidade_minima_ativacao=20,
        quantidade_vendida=12, # 60% -> WARM
        data_termino=timezone.now() + timezone.timedelta(days=5),
        publicada=True,
        status='ativa'
    )
    
    # 3. THE COLD DEAL (Ice)
    Oferta.objects.create(
        titulo="Teclado Mecânico Custom",
        slug="teclado-mecanico-cold",
        vendedor=vendedor,
        categoria=cat,
        tipo_oferta='lote',
        descricao_detalhada="Precisamos de 200 pessoas.",
        preco_original=Decimal("800.00"),
        preco_desconto=Decimal("500.00"),
        quantidade_minima_ativacao=200,
        quantidade_vendida=15, # 7.5% -> COLD
        data_termino=timezone.now() + timezone.timedelta(days=10),
        publicada=True,
        status='ativa'
    )
    
    print("✅ Seed Complete! Visit /ofertas/heatmap/")

if __name__ == '__main__':
    seed_heatmap()
