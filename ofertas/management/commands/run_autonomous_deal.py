from django.core.management.base import BaseCommand
from django.utils import timezone
from ofertas.models import Oferta, Vendedor, Categoria
from contas.models import Usuario
from pedidos_coletivos.models import PedidoColetivo
from pedidos_coletivos.services.logistics import LogisticsAdapter
import time
import random

class Command(BaseCommand):
    help = 'Simula o Ciclo de Varejo Autônomo (Project Barbecue)'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('🤖 INICIANDO MODO AUTÔNOMO (PROJECT BARBECUE)...'))
        time.sleep(1)

        # 1. HUNTER AGENT
        self.stdout.write(self.style.WARNING('\n🕵️ HUNTER AGENT: Varrendo redes sociais e encartes...'))
        time.sleep(2)
        
        produto_detectado = {
            "nome": "Cerveja Heineken 350ml (Lata)",
            "preco_encontrado": 3.49,
            "margem_alvo": 1.20, # 20%
            "pacote": 12 # Pack de 12
        }
        
        preco_venda = round(produto_detectado['preco_encontrado'] * produto_detectado['margem_alvo'], 2)
        self.stdout.write(f"   -> Oportunidade Detectada: {produto_detectado['nome']}")
        self.stdout.write(f"   -> Custo: R$ {produto_detectado['preco_encontrado']} | Venda Alvo: R$ {preco_venda}")
        time.sleep(1)

        # 2. MANAGER AGENT
        self.stdout.write(self.style.WARNING('\n👔 MANAGER AGENT: Calculando viabilidade e criando oferta...'))
        
        # Get or Create Dummy Vendedor
        vendedor, _ = Vendedor.objects.get_or_create(
            nome_empresa="Autonomous Store Bot",
            defaults={'cnpj': '00000000000199', 'email_contato': 'bot@varejounido.com.br', 'status_aprovacao': 'aprovado'}
        )
        
        oferta = Oferta.objects.create(
            titulo=f"[AUTO] {produto_detectado['nome']} - Pack {produto_detectado['pacote']}un",
            descricao_detalhada="Oferta gerada automaticamente pelo Hunter Agent.",
            preco_original=preco_venda * 1.5,
            preco_desconto=preco_venda,
            vendedor=vendedor,
            tipo_oferta='lote',
            quantidade_minima_ativacao=produto_detectado['pacote'], # Fecha com 1 pack (simplificado) ou N unidades
            status='ativa',
            publicada=True,
            data_termino=timezone.now() + timezone.timedelta(hours=6),
            tipo_entrega='entrega',
            valor_frete=5.00
        )
        
        self.stdout.write(self.style.SUCCESS(f"   -> Oferta Criada: {oferta.titulo} (ID: {oferta.id})"))
        self.stdout.write(f"   -> Link Gerado: /ofertas/{oferta.slug}/")
        time.sleep(1)

        # 3. SIMULAÇÃO DE COMPRAS (VIRALIZAÇÃO)
        self.stdout.write(self.style.WARNING('\n🔥 CLIENTES: O link viralizou no WhatsApp! Comprando...'))
        time.sleep(2)
        
        # Simula compra para fechar o lote
        # Precisamos de um usuário dummy
        user, _ = Usuario.objects.get_or_create(username="cliente_feliz", email="cliente@teste.com")
        
        PedidoColetivo.objects.create(
            usuario=user,
            oferta=oferta,
            quantidade=produto_detectado['pacote'], # Compra tudo pra fechar
            valor_total=preco_venda * produto_detectado['pacote'],
            status_pagamento='aprovado_mp',
            status_lote='pendente' # Vai virar concretizado no update
        )
        
        oferta.quantidade_vendida += produto_detectado['pacote']
        oferta.save()
        
        self.stdout.write(self.style.SUCCESS(f"   -> Lote Atingido! ({oferta.quantidade_vendida}/{oferta.quantidade_minima_ativacao})"))
        
        # 4. LOGISTICS AGENT
        self.stdout.write(self.style.WARNING('\n🛵 LOGISTICS AGENT: Lote fechado. Chamando entregador...'))
        time.sleep(1)
        
        adapter = LogisticsAdapter()
        # Fake pedido object pass
        class PedidoFake:
            id = 999
            usuario = user
            oferta = oferta
        
        response = adapter.solicitar_entregador(PedidoFake())
        
        if response['status'] == 'success':
            oferta.status = 'sucesso'
            oferta.save()
            self.stdout.write(self.style.SUCCESS(f"\n✅ CICLO COMPLETO COM SUCESSO!"))
            self.stdout.write(f"💰 Lucro Estimado: R$ {((preco_venda - produto_detectado['preco_encontrado']) * produto_detectado['pacote']):.2f}")
            self.stdout.write(f"🍖 PODE COMER O CHURRASCO, CHEFE. O ROBÔ TRABALHOU.\n")
