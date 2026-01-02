# ofertas/product_scanner.py

"""
Serviço para extrair informações de produtos a partir de imagens.
Usa Google Cloud Vision API para OCR.
"""

import re
from decimal import Decimal, InvalidOperation
from typing import Optional, Dict, Any, List
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class ProductScannerService:
    """
    Serviço para extrair informações de produtos a partir de imagens.
    Usa Google Cloud Vision API para OCR.
    """
    
    def __init__(self):
        self.vision_client = None
        self._initialize_vision_client()
    
    def _initialize_vision_client(self):
        """Inicializa o cliente do Google Cloud Vision."""
        try:
            from google.cloud import vision
            self.vision_client = vision.ImageAnnotatorClient()
            logger.info("Google Cloud Vision inicializado com sucesso.")
        except ImportError:
            logger.warning(
                "google-cloud-vision não instalado. "
                "Instale com: pip install google-cloud-vision"
            )
        except Exception as e:
            logger.error(f"Erro ao inicializar Vision API: {e}")
    
    def extract_text_from_image(self, image_bytes: bytes) -> str:
        """
        Extrai todo o texto de uma imagem usando OCR.
        
        Args:
            image_bytes: Bytes da imagem
            
        Returns:
            Texto extraído da imagem
            
        Raises:
            ValueError: Se o Vision API não está configurado
            Exception: Se houver erro na API
        """
        if not self.vision_client:
            raise ValueError(
                "Google Cloud Vision não está configurado. "
                "Configure a variável GOOGLE_APPLICATION_CREDENTIALS."
            )
        
        from google.cloud import vision
        image = vision.Image(content=image_bytes)
        response = self.vision_client.text_detection(image=image)
        
        if response.error.message:
            raise Exception(f"Erro na API Vision: {response.error.message}")
        
        texts = response.text_annotations
        if texts:
            return texts[0].description
        return ""
    
    def extract_product_info(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Extrai informações de produto de uma imagem.
        
        Args:
            image_bytes: Bytes da imagem
            
        Returns:
            Dicionário com:
            - raw_text: Texto bruto extraído
            - products: Lista de produtos identificados
        """
        text = self.extract_text_from_image(image_bytes)
        
        return {
            'raw_text': text,
            'products': self._parse_products_from_text(text),
            'validity_date': self.extract_validity_date(text),
        }
    
    def _parse_products_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Analisa o texto OCR e extrai lista de produtos.
        Tenta identificar nomes de produtos e preços.
        
        Args:
            text: Texto extraído do OCR
            
        Returns:
            Lista de dicionários com nome e preço de cada produto
        """
        products = []
        lines = text.split('\n')
        
        # Padrões comuns de preço em português brasileiro
        price_patterns = [
            r'R\$\s*([\d]+[,.][\d]{2})',  # R$ 12,99 ou R$ 12.99
            r'([\d]+[,.][\d]{2})\s*R\$',  # 12,99 R$
            r'por\s*apenas\s*R?\$?\s*([\d]+[,.][\d]{2})',  # por apenas 12,99
            r'de\s*R?\$?\s*[\d]+[,.][\d]{2}\s*por\s*R?\$?\s*([\d]+[,.][\d]{2})',  # de R$ X por R$ Y
            r'([\d]+)[,]([\d]{2})',  # 12,99 (formato brasileiro)
        ]
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            # Tenta encontrar preço na linha
            price = None
            for pattern in price_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    # Pega o último grupo (preço com desconto)
                    groups = match.groups()
                    if len(groups) == 2 and groups[1].isdigit():
                        # Formato brasileiro: 12,99
                        price_str = f"{groups[0]}.{groups[1]}"
                    else:
                        price_str = groups[-1].replace(',', '.')
                    
                    try:
                        price = Decimal(price_str)
                        if price > 0 and price < 100000:  # Sanity check
                            break
                    except (InvalidOperation, ValueError):
                        continue
            
            if price and price > 0:
                # Remove o preço e símbolos monetários da linha para pegar o nome
                name = re.sub(r'R?\$?\s*[\d]+[,.][\d]{2}', '', line)
                name = re.sub(r'^\s*[-•·]\s*', '', name)  # Remove bullets
                name = name.strip()
                
                # Validação básica do nome
                if name and len(name) >= 3 and not name.isdigit():
                    products.append({
                        'nome': name[:100],  # Limita tamanho
                        'preco': float(price),
                    })
        
        # Remove duplicatas por nome similar
        unique_products = []
        seen_names = set()
        for p in products:
            name_lower = p['nome'].lower()
            if name_lower not in seen_names:
                seen_names.add(name_lower)
                unique_products.append(p)
        
        return unique_products[:20]  # Limita a 20 produtos
    
    def extract_validity_date(self, text: str) -> Optional[str]:
        """
        Tenta extrair data de validade do texto.
        Procura padrões como 'válido até', 'validade', etc.
        
        Args:
            text: Texto do OCR
            
        Returns:
            Data encontrada ou None
        """
        patterns = [
            r'v[aá]lid[oa]?\s*at[eé]\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
            r'validade[:\s]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
            r'at[eé]\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
            r'oferta\s*v[aá]lida\s*at[eé]\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
            r'promoç[aã]o\s*v[aá]lida\s*at[eé]\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def extract_store_name(self, text: str) -> Optional[str]:
        """
        Tenta extrair nome do supermercado/loja do texto.
        
        Args:
            text: Texto do OCR
            
        Returns:
            Nome da loja ou None
        """
        # Nomes comuns de supermercados brasileiros
        known_stores = [
            'carrefour', 'extra', 'pão de açúcar', 'assaí', 'atacadão',
            'big', 'walmart', 'sam\'s club', 'makro', 'dia', 'sonda',
            'hirota', 'st marche', 'zaffari', 'nacional', 'angeloni',
            'condor', 'festval', 'muffato', 'super muffato', 'oba',
        ]
        
        text_lower = text.lower()
        for store in known_stores:
            if store in text_lower:
                return store.title()
        
        # Tenta encontrar padrão "Supermercado X" ou "Mercado X"
        patterns = [
            r'supermercado\s+([A-Za-z]+)',
            r'mercado\s+([A-Za-z]+)',
            r'atacado\s+([A-Za-z]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).title()
        
        return None
