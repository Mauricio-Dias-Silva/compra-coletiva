
import os
import json
import logging
from typing import List, Dict, Any
import google.generativeai as genai
from django.conf import settings
from decimal import Decimal

# Configure Logger
logger = logging.getLogger(__name__)

class AIScannerService:
    """
    Service to scan supermarket flyers/shelves and extract product data via Gemini Vision.
    """
    def __init__(self):
        try:
            api_key = os.getenv("GEMINI_API_KEY") # Ensure this is set in .env
            if not api_key:
                logger.warning("GEMINI_API_KEY not set. AI Scanner will fail.")
            
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro-vision') # Or gemini-2.0-flash-exp if available
        except Exception as e:
            logger.error(f"Failed to init Gemini: {e}")

    def scan_flyer(self, image_path: str, margin_percent: float = 20.0) -> List[Dict[str, Any]]:
        """
        Scans an image for products/prices and adds a profit margin.
        V2.0: Suporte a Regex, Fallback e Prompt Otimizado para Brasil.
        """
        import re
        
        prompt = """
        🔍 AJA COMO UM ESPECIALISTA EM VAREJO BRASILEIRO.
        Analise esta imagem (folheto/gôndola). Extraia TODOS os produtos.
        Seja preciso com números e formatação R$.

        Para cada produto, extraia:
        1. "name": Nome completo (Marca, Tipo, Peso/Vol). Ex: "Arroz Tio João 5kg".
        2. "found_price": O preço da unidade visível na etiqueta. Ignore "R$", converta vírgula para ponto (ex: 10,90 -> 10.90).
        3. "pack_info": Olhe atentamente se é um FARDO, CAIXA ou PACK. 
           - Se encontrar "Cx 12", "Fardo com 6", extraia esse número.
           - Se for item solto (ex: Detergente), estime o padrão de atacado (ex: 12 ou 24).
           - ATENÇÃO: Se o preço for "Leve 3 Pague 2", calcule o preço unitário real.
        
        RETORNE APENAS UM JSON ARRAY VÁLIDO. SEM MARKDOWN.
        Exemplo:
        [
            {"name": "Cerveja Heineken 350ml", "found_price": 4.50, "pack_qty": 12, "unit": "lata"},
            {"name": "Sabão em Pó Omo 1kg", "found_price": 12.90, "pack_qty": 10, "unit": "caixa"}
        ]
        """
        
        try:
            # Load Image
            if not os.path.exists(image_path):
                return [{"error": "Image file not found"}]

            img = None
            with open(image_path, "rb") as f:
                img_data = f.read()
                img = {"mime_type": "image/jpeg", "data": img_data}

            # Generate (Try Flash model first for speed)
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content([prompt, img])
            except:
                logger.warning("Gemini Flash unavailable, falling back to Pro Vision")
                model = genai.GenerativeModel('gemini-pro-vision')
                response = model.generate_content([prompt, img])
                
            text = response.text
            
            # --- ROBUST PARSING ENGINE (V2) ---
            products = []
            
            # 1. Clean Markdown
            cleaned_text = text.replace("```json", "").replace("```", "").strip()
            
            try:
                products = json.loads(cleaned_text)
            except json.JSONDecodeError:
                # 2. Regex Fallback
                logger.warning("JSON Decode failed. Attempting Regex Extraction.")
                pattern = r'\{.*?\}'
                matches = re.findall(pattern, cleaned_text, re.DOTALL)
                for m in matches:
                    try:
                        # Tentar consertar JSONs quebrados comuns
                        m = m.replace("'", '"') 
                        p = json.loads(m)
                        products.append(p)
                    except:
                        pass
            
            if not products:
                # 3. Last Resort: Structured Text Parsing via AI (Recursive fix? Too slow).
                # For now just return empty but log raw text for debug
                logger.error(f"Failed to parse AI response: {text[:100]}...")
                return []

            # Post-Process: Apply Margin & Box Logic
            processed = []
            for p in products:
                try:
                    # Fix Price Format (some AI returns "R$ 10,90")
                    raw_price = str(p.get('found_price', 0)).replace('R$', '').replace(',', '.').strip()
                    cost_price = Decimal(raw_price)
                    
                    box_qty = int(p.get('pack_qty', 12))
                    
                    # Selling Price = Cost + Margin
                    selling_price = cost_price * (1 + Decimal(margin_percent)/100)
                    
                    processed.append({
                        "name": p.get('name', 'Produto Desconhecido'),
                        "cost_price": float(cost_price),
                        "selling_price": float(round(selling_price, 2)),
                        "margin": f"{margin_percent}%",
                        "min_qty": box_qty,
                        "suggested_title": f"{p.get('name')} (Lote de {box_qty} un)"
                    })
                except Exception as row_err:
                    logger.error(f"Error processing row {p}: {row_err}")
                    continue
                
            return processed

        except Exception as e:
            logger.error(f"Scan failed: {e}")
            # Em prod, retornar erro user-friendly
            return []
