import time
import random

class LogisticsAdapter:
    """
    Simula a integração com APIs de entregas rápidas (Uber Direct, Lalamove, Loggi).
    No futuro, substituir os prints por requests reais.
    """
    
    SERVER_URL = "https://api.uber.com/v1/guests/deliveries" # Fake URL for reference

    def solicitar_entregador(self, pedido):
        """
        Chama um motoboy para buscar o pedido no vendedor e levar ao cliente.
        """
        print(f"==================================================")
        print(f"🚁 LOGISTICS BOT: Solicitando Entregador via API...")
        print(f"📦 Pedido: {pedido.id} | Cliente: {pedido.usuario.username}")
        print(f"📍 Origem: {pedido.oferta.vendedor.endereco}")
        # Lógica para pegar endereço do cliente (se fosse entrega em casa)
        # Assumindo retirada no líder do lote ou entrega direta.
        destino = "Endereço do Cliente (Simulado)" 
        print(f"📍 Destino: {destino}")
        
        # Simula delay de API
        time.sleep(1)
        
        # Simula resposta da API
        motoristas = ["Carlos (Honda CG Titan)", "Ana (Yamaha NMax)", "Roberto (Honda Biz)"]
        motorista = random.choice(motoristas)
        placa = f"{random.choice(['ABC', 'XYZ', 'BRA'])}-{random.randint(1000, 9999)}"
        
        tracking_url = f"https://uber.com/track/{random.randint(100000, 999999)}"
        
        response = {
            "status": "success",
            "driver_name": motorista,
            "vehicle_plate": placa,
            "eta_minutes": random.randint(5, 15),
            "tracking_url": tracking_url,
            "cost": 12.50
        }
        
        print(f"✅ LOGISTICS BOT: Motorista Encontrado!")
        print(f"🏍️ {response['driver_name']} - Placa {response['vehicle_plate']}")
        print(f"⏱️ Chega em {response['eta_minutes']} min no Vendedor.")
        print(f"==================================================")
        
        return response
