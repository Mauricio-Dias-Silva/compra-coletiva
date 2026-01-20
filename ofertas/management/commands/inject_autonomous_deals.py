
import os
import chromadb
import random
from datetime import timedelta
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from ofertas.models import Oferta, Vendedor, Categoria

class Command(BaseCommand):
    help = 'SHOP-BOT: Cria ofertas automaticamente baseadas em Tendências de Mercado (TrendCodex).'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🛒 INICIANDO AUTONOMOUS SHOP (Codex -> CompraColetiva)...'))

        # 1. Conectar à Memória do Codex
        CODEX_MEMORY_PATH = r"c:\Users\Mauricio\Desktop\codex-IA\.codex_memory"
        if not os.path.exists(CODEX_MEMORY_PATH):
            self.stdout.write(self.style.ERROR('❌ Memória Codex não encontrada.'))
            return

        try:
            client = chromadb.PersistentClient(path=CODEX_MEMORY_PATH)
            collection = client.get_collection("project_codebase")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro Vector Store: {e}'))
            return

        # 2. Criar Vendedor AI (A "Corporate Persona")
        vendor, _ = Vendedor.objects.get_or_create(
            cnpj='00000000000000',
            defaults={
                'nome_empresa': 'Codex Autonomous Ventures',
                'email_contato': 'ai@codex.ventures',
                'descricao': 'Produtos curados por Inteligência Artificial baseados em tendências globais.',
                'status_aprovacao': 'aprovado',
                'ativo': True
            }
        )

        # 3. Buscar Tendências (TrendCodex)
        self.stdout.write('   🔮 Consultando o Oráculo de Tendências (via Gemini Embeddings)...')
        
        # Configurar Gemini (Hardcoded for stability across projects)
        import google.generativeai as genai
        API_KEY = "AIzaSyBREWGg-uOUss7bZIoK0xqBU5svqvyCX6Y"
        genai.configure(api_key=API_KEY)
        
        # Gerar embedding da query (768 dim) para bater com o banco
        query_text = "Top products trends 2026 viral market"
        try:
            model = "models/embedding-001" # Ou text-embedding-004
            embedding_result = genai.embed_content(
                model=model,
                content=query_text,
                task_type="retrieval_query"
            )
            query_vector = embedding_result['embedding']
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao gerar embedding: {e}'))
            # Fallback Fake Vector (apenas para não crashar, embora não vá achar nada relevante)
            query_vector = [0.0] * 768 

        results = collection.query(
            query_embeddings=[query_vector],
            n_results=5
        )
        
        trends = results['documents'][0] if results['documents'] else [
            "Smart Home Eco-Friendly", "Biohacking Gadgets", "Nootropic Coffee"
        ]

        # 4. Fabricar Ofertas
        for trend_text in trends:
            # Simplificação: Extrair um título curto do texto da tendência
            # Em prod, usaríamos um LLM para resumir. Aqui, pegamos as primeiras 4 palavras.
            product_name = " ".join(trend_text.split()[:4]).title()
            
            # Categoria Dinâmica
            cat_name = "Inovação"
            categoria, _ = Categoria.objects.get_or_create(nome=cat_name, defaults={'slug': 'inovacao'})

            # Pricing Psychology (Preços quebrados vendem mais)
            price = random.randint(50, 500)
            price_promo = price * 0.7
            
            try:
                oferta, created = Oferta.objects.get_or_create(
                    titulo=f"Kit {product_name} (Viral)",
                    vendedor=vendor,
                    defaults={
                        'categoria': categoria,
                        'descricao_detalhada': f"🔥 PRODUTO TENDÊNCIA!\n\nBaseado na análise: {trend_text[:200]}...\n\nCompre antes que acabe.",
                        'preco_original': price,
                        'preco_desconto': price_promo,
                        'tipo_oferta': 'unidade',
                        'status': 'ativa',
                        'publicada': True,
                        'data_inicio': timezone.now(),
                        'data_termino': timezone.now() + timedelta(days=7),
                        'quantidade_maxima_cupons': 100
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'   ✅ Produto Criado: {oferta.titulo} (R$ {price_promo})'))
                else:
                    self.stdout.write(f'   ℹ️ Produto já existe: {oferta.titulo}')
            except IntegrityError:
                pass

        self.stdout.write(self.style.SUCCESS('🚀 LOJA ATUALIZADA COM SUCESSO.'))
