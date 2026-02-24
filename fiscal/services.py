import logging
import requests
import json
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

class FiscalService:
    """
    Serviço para integração com Focus NFe (JSON NFe 4.0)
    """
    
    def __init__(self, api_key=None, environment=None):
        self.api_key = api_key or getattr(settings, 'FOCUS_NFE_API_KEY', 'TOKEN_PARA_TESTES')
        self.environment = environment or getattr(settings, 'FOCUS_NFE_ENV', 'sandbox')
        self.base_url = "https://api.focusnfe.com.br/v2" if self.environment == 'production' else "https://homologacao.focusnfe.com.br/v2"

    def emitir_nfe(self, nota_fiscal):
        """
        Mapeia os dados da Compra/Pedido e envia para a Focus NFe.
        """
        # Identifica se é Compra (Unidade) ou Pedido Coletivo (Lote)
        objeto_origem = nota_fiscal.compra or nota_fiscal.pedido_coletivo
        if not objeto_origem:
            logger.error("Nota Fiscal sem objeto de origem vinculado.")
            return False

        vendedor = objeto_origem.oferta.vendedor
        cliente = objeto_origem.usuario
        oferta = objeto_origem.oferta

        logger.info(f"Gerando JSON de NFe para Compra #{objeto_origem.id}...")

        # --- MAPEAMENTO NFe 4.0 (Simplificado para Marketplace) ---
        payload = {
            "natureza_operacao": "Venda de mercadoria",
            "data_emissao": timezone.now().isoformat(),
            "tipo_documento": 1, # 1=Saída
            "finalidade_emissao": 1, # 1=Normal
            "cnpj_emitente": vendedor.cnpj.replace(".", "").replace("/", "").replace("-", ""),
            "nome_emitente": vendedor.nome_empresa,
            "inscricao_estadual_emitente": vendedor.inscricao_estadual or "ISENTO",
            "logradouro_emitente": vendedor.endereco,
            "numero_emitente": vendedor.numero,
            "bairro_emitente": vendedor.bairro,
            "municipio_emitente": vendedor.municipio,
            "uf_emitente": vendedor.uf,
            "cep_emitente": vendedor.cep.replace("-", ""),
            
            "nome_destinatario": cliente.get_full_name() or cliente.username,
            "cpf_destinatario": (cliente.cpf or "00000000000").replace(".", "").replace("-", ""),
            "logradouro_destinatario": cliente.logradouro or "Consumidor Final",
            "numero_destinatario": cliente.numero or "S/N",
            "bairro_destinatario": cliente.bairro or "Centro",
            "municipio_destinatario": cliente.municipio or "São Paulo",
            "uf_destinatario": cliente.uf or "SP",
            "cep_destinatario": (cliente.cep or "00000000").replace("-", ""),
            
            "items": [
                {
                    "numero_item": "1",
                    "codigo_produto": str(oferta.id),
                    "descricao": oferta.titulo,
                    "ncm": "00000000", # Ideal ter no modelo. Usando generic por enquanto.
                    "cfop": "5102", # Operação Interna
                    "unidade_comercial": "un",
                    "quantidade_comercial": float(getattr(objeto_origem, 'quantidade', 1)),
                    "valor_unitario_comercial": float(oferta.preco_desconto),
                    "valor_unitario_tributavel": float(oferta.preco_desconto),
                    "unidade_tributavel": "un",
                    "quantidade_tributavel": float(getattr(objeto_origem, 'quantidade', 1)),
                    "origem": 0, # Nacional
                    "icms_situacao_tributaria": "102", # Simples Nacional - Sem permissão de crédito
                }
            ],
            "formas_pagamento": [
                {
                    "forma_pagamento": "15", # 15=Boleto, 03=Cartão, 17=PIX (Usando genérico ou mapear do MP)
                    "valor_pagamento": float(objeto_origem.valor_total)
                }
            ]
        }

        try:
            # Referência externa única para Focus (Evita duplicidade)
            ref = f"CC_{objeto_origem.id}_{timezone.now().timestamp()}"
            response = requests.post(
                f"{self.base_url}/nfe?ref={ref}", 
                json=payload, 
                auth=(self.api_key, "")
            )
            
            if response.status_code in [201, 202]:
                data = response.json()
                nota_fiscal.status = 'processando'
                nota_fiscal.mensagem_erro = f"Enviado com REF: {ref}"
                nota_fiscal.save()
                return True
            else:
                nota_fiscal.status = 'erro'
                nota_fiscal.mensagem_erro = f"Erro API Focus ({response.status_code}): {response.text}"
                nota_fiscal.save()
                return False

        except Exception as e:
            nota_fiscal.status = 'erro'
            nota_fiscal.mensagem_erro = f"Falha de Conexão: {str(e)}"
            nota_fiscal.save()
            return False

    def consultar_status(self, nota_fiscal):
        """
        Verifica o status da nota na API da Focus.
        """
        # (Implementação real via GET base_url/nfe/REF pendente de refactoring para usar a REF salva)
        # Por enquanto, mantemos a lógica de transição se processando
        if nota_fiscal.status == 'processando':
            # Simulação de consulta positiva para fluxo fluir no dev
            nota_fiscal.status = 'emitida'
            nota_fiscal.pdf_url = "https://homologacao.focusnfe.com.br/arquivos/exemplo.pdf"
            nota_fiscal.save()
            return True
        return False
