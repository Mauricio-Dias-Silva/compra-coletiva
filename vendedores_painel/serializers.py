# vendedores_painel/serializers.py

from rest_framework import serializers
# Importa APENAS o MODELO Oferta, não o serializer
from ofertas.models import Oferta 
# Importa o Form para reusar a validação
from ofertas.forms import OfertaForm 
# Importa serializers de OUTROS apps (isso é seguro agora que eles são "lazy")
from compras.serializers import CupomSerializer 
from contas.serializers import UserSerializer 

# --- NENHUMA importação de 'OfertaSerializer' aqui ---

class DashboardStatsSerializer(serializers.Serializer):
    """
    Serializer Read-Only para as estatísticas do Dashboard.
    """
    total_cupons_vendidos = serializers.IntegerField(read_only=True)
    total_cupons_resgatados = serializers.IntegerField(read_only=True)
    receita_bruta_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)


class MinhaOfertaWriteSerializer(serializers.ModelSerializer):
    """
    Serializer de Escrita (Create/Update) para o Vendedor.
    """
    class Meta:
        model = Oferta
        # Campos que o Vendedor pode preencher
        fields = [
            'titulo',
            'descricao_detalhada',
            # 'regras', # (Adicione ao models.py se este campo for necessário)
            'preco_original',
            'preco_desconto',
            'imagem_principal',
            'tipo_oferta',
            'data_inicio',
            'data_termino',
            'quantidade_minima_ativacao', 
            'quantidade_maxima_cupons', # (Este é o nome correto)
            'categoria',
        ]
        
    def validate(self, data):
        # Reusa a validação do OfertaForm
        form = OfertaForm(data=data, instance=self.instance) # <-- Linha corrigida
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)
        return data

# --- ESTA CLASSE PRECISA ESTAR AQUI ---
class PainelCupomResgateSerializer(serializers.Serializer):
    """
    Serializer simples para a action de resgatar cupom.
    """
    codigo = serializers.CharField(max_length=50)

    def validate_codigo(self, value):

        # Normaliza o código (remove espaços, maiúsculas)
        return value.strip().upper()
# ------------------------------------