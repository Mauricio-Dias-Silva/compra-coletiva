
import os
import sys
import django

# Setup Django Environment
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "projeto_compra_coletiva.settings")
django.setup()

from ofertas.services.ai_scanner import AIScannerService

if __name__ == "__main__":
    print("🚀 Iniciando Teste do Scanner AI...")
    
    # Mock Image Path (User needs to provide one)
    image_path = "flyer_test.jpg"
    
    if not os.path.exists(image_path):
        print(f"❌ Imagem de teste '{image_path}' não encontrada.")
        print("Coloque uma foto de encarte na raiz do projeto para testar.")
    else:
        scanner = AIScannerService()
        print("📸 Lendo imagem...")
        products = scanner.scan_flyer(image_path)
        
        print(f"✅ Encontrados {len(products)} produtos:")
        for p in products:
            print(f" - {p['suggested_title']} | Custo: R${p['cost_price']} | Venda: R${p['selling_price']}")
