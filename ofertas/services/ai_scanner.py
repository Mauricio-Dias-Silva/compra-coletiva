
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
        """
        prompt = """
        Analyze this supermarket shelf/product image.
        Extract ALL products.
        For each product, IDENTIFY:
        1. Product Name (e.g., "Detergente Ypê 500ml")
        2. PRICE found on the tag (This is the COST PRICE for me).
        3. PACK QUANTITY (Crucial): Does the tag or box say "Cx 12", "Fardo 6", "Pack 24"? 
           - If found, extract this number as 'box_qty'.
           - If NOT found, estimate based on product type (e.g., Soda=6, Soap=12, default=12).
        
        Return RAW JSON array:
        [{"name": "...", "found_price": 10.50, "box_qty": 12, "unit_type": "un"}]
        """
        
        try:
            # Load Image
            if not os.path.exists(image_path):
                return [{"error": "Image file not found"}]

            img = None
            with open(image_path, "rb") as f:
                img_data = f.read()
                img = {"mime_type": "image/jpeg", "data": img_data}

            # Generate
            response = self.model.generate_content([prompt, img])
            text = response.text
            
            # Clean JSON
            if "```json" in text:
                text = text.replace("```json", "").replace("```", "")
            
            products = json.loads(text)
            
            # Post-Process: Apply Margin & Box Logic
            processed = []
            for p in products:
                cost_price = Decimal(str(p.get('found_price', 0)))
                box_qty = int(p.get('box_qty', 12)) # Default 12 if AI fails
                
                # Logic:
                # We buy the WHOLE BOX at (cost_price * box_qty) -> Actually usually shelf price is UNIT price?
                # Case A: Tag says "Nestle Cx 12 - R$ 120,00" -> Unit Cost = 10.00
                # Case B: Tag says "Coca Cola - R$ 5,00" (Unit) -> We just buy 6 units.
                # ASSUMPTION: The price found is the UNIT price of the item on the shelf.
                
                # Selling Price = Cost + Margin
                selling_price = cost_price * (1 + Decimal(margin_percent)/100)
                
                processed.append({
                    "name": p.get('name'),
                    "cost_price": float(cost_price),
                    "selling_price": float(round(selling_price, 2)),
                    "margin": f"{margin_percent}%",
                    "min_qty": box_qty, # The "Box Barrier"
                    "suggested_title": f"{p.get('name')} (Lote de {box_qty})"
                })
                
            return processed

        except Exception as e:
            logger.error(f"Scan failed: {e}")
            return []
