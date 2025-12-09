# contas/serializers.py

from rest_framework import serializers
from .models import Usuario, Notificacao
# from ofertas.serializers import VendedorSerializer  <--- REMOVA ESTA LINHA DO TOPO

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer CORRIGIDO para o modelo 'Usuario'.
    (Com a correção da importação circular)
    """
    
    # --- A CORREÇÃO ESTÁ AQUI ---
    # 1. Mudamos o campo para 'SerializerMethodField'.
    #    Isso nos permite controlar como (e quando) os dados do vendedor são carregados.
    vendedor = serializers.SerializerMethodField()
    # ---------------------------

    nome_completo = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            'id', 
            'username', 
            'email', 
            'first_name', 
            'last_name',  
            'nome_completo', 
            'vendedor'       
        ]
        read_only_fields = ['email', 'vendedor']

    def get_nome_completo(self, obj):
        if obj.first_name or obj.last_name:
            return f"{obj.first_name} {obj.last_name}".strip()
        return obj.username

    # --- E AQUI ---
    # 2. Criamos a função para o 'SerializerMethodField' (get_vendedor).
    def get_vendedor(self, obj):
        """
        Esta função carrega o VendedorSerializer.
        A importação é feita AQUI DENTRO, quebrando o círculo.
        """
        
        # 3. A importação que estava no topo do arquivo agora está AQUI.
        from ofertas.serializers import VendedorSerializer 
        
        if obj.vendedor:
            # Nós passamos o 'context' para o serializer aninhado, 
            # o que é uma boa prática para DRF.
            return VendedorSerializer(obj.vendedor, context=self.context).data
        return None
    # ---------------------------


class NotificacaoSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Notificacao.
    (Este não precisa de alteração)
    """
    class Meta:
        model = Notificacao
        fields = [
            'id',
            'data_criacao',
            'lida',
            'titulo',
            'mensagem',
            'tipo',
            'url_destino'
        ]
        read_only_fields = fields
