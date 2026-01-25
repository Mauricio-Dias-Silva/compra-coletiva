from django.db import models
from django.conf import settings
from contas.models import Usuario

class Entregador(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='entregador_perfil')
    cpf = models.CharField(max_length=14, unique=True)
    placa_veisulo = models.CharField(max_length=10, blank=True)
    modelo_veiculo = models.CharField(max_length=50, blank=True)
    ativo = models.BooleanField(default=True)
    online = models.BooleanField(default=False)
    
    saldo_a_receber = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    def __str__(self):
        return f"Entregador {self.usuario.get_full_name()} ({self.placa_veisulo})"

class Entrega(models.Model):
    STATUS_ENTREGA = [
        ('pendente', 'Pendente de Aceite'),
        ('aceita', 'Aceita (A Caminho)'),
        ('coletada', 'Coletada (Em Rota)'),
        ('entregue', 'Entregue'),
        ('cancelada', 'Cancelada'),
    ]
    
    entregador = models.ForeignKey(Entregador, on_delete=models.SET_NULL, null=True, blank=True, related_name='entregas')
    pedido_origem_id = models.CharField(max_length=100) # Ex: LOTE-123
    
    endereco_origem = models.CharField(max_length=255)
    endereco_destino = models.CharField(max_length=255)
    valor_frete = models.DecimalField(max_digits=10, decimal_places=2)
    distancia_km = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_ENTREGA, default='pendente')
    
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_conclusao = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Entrega #{self.id} - {self.status}"
