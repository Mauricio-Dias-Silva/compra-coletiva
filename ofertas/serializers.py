# ofertas/serializers.py

from rest_framework import serializers
from .models import Oferta, Categoria, Vendedor, Avaliacao, Banner

# from contas.serializers import UserSerializer # <--- REMOVA ESTA LINHA DO TOPO

# (O UserSerializer já importa o VendedorSerializer, mas é boa prática
# definir o VendedorSerializer antes de ser usado em 'OfertaSerializer')

class VendedorSerializer(serializers.ModelSerializer):
    """
    Serializer CORRIGIDO para o modelo 'Vendedor'.
    (Baseado no 'ofertas/models.py' real)
    """
    class Meta:
        model = Vendedor
        fields = [
            'id', 
            'nome_empresa',
            'logo', 
            'descricao',
            'email_contato', 
            'telefone',      
            'endereco',      
            'status_aprovacao', 
        ]
        read_only_fields = fields


class CategoriaSerializer(serializers.ModelSerializer):
    """
    Serializer CORRIGIDO para o modelo 'Categoria'.
    (Baseado no 'ofertas/models.py' real)
    """
    class Meta:
        model = Categoria
        fields = [
            'id', 
            'nome', 
            'slug',
            'descricao', 
            'ativa'      
        ]
        read_only_fields = fields


class AvaliacaoSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo 'Avaliacao'.
    (CORRIGIDO para a importação circular)
    """
    # --- A CORREÇÃO ESTÁ AQUI ---
    # 1. Mudamos o campo para 'SerializerMethodField'.
    usuario = serializers.SerializerMethodField()
    # ---------------------------

    class Meta:
        model = Avaliacao
        fields = [
            'id',
            'usuario', # <-- Este agora é o MethodField
            'nota',
            'comentario',
            'data_avaliacao'
        ]

    # --- E AQUI ---
    # 2. Criamos a função para o 'SerializerMethodField' (get_usuario).
    def get_usuario(self, obj):
        """
        Esta função carrega o UserSerializer.
        A importação é feita AQUI DENTRO, quebrando o círculo.
        """
        
        # 3. A importação que estava no topo do arquivo agora está AQUI.
        from contas.serializers import UserSerializer
        
        if obj.usuario:
            return UserSerializer(obj.usuario, context=self.context).data
        return None
    # ---------------------------


class OfertaListSerializer(serializers.ModelSerializer):
    """
    Serializer CORRIGIDO (para Listas) do modelo 'Oferta'.
    """
    vendedor = VendedorSerializer(read_only=True)
    categoria = CategoriaSerializer(read_only=True)
    percentual_desconto = serializers.CharField(read_only=True)
    media_avaliacoes = serializers.FloatField(read_only=True)

    class Meta:
        model = Oferta
        fields = [
            'id',
            'titulo',
            'slug',
            'imagem_principal',
            'preco_original',
            'preco_desconto',
            'percentual_desconto',
            'tipo_oferta',
            'data_inicio', 
            'data_termino',
            'status',      
            'quantidade_vendida', 
            'quantidade_minima_ativacao', 
            'vendedor',
            'categoria',
            'media_avaliacoes', 
        ]


class OfertaDetailSerializer(OfertaListSerializer):
    """
    Serializer CORRIGIDO (para Detalhes) do modelo 'Oferta'.
    Inclui tudo da Lista + as avaliações.
    """
    # Este 'avaliacoes' agora usa o AvaliacaoSerializer corrigido
    avaliacoes = AvaliacaoSerializer(many=True, read_only=True) 

    class Meta(OfertaListSerializer.Meta):
        fields = OfertaListSerializer.Meta.fields + [
            'descricao_detalhada', 
            # 'regras', # (Seu 'ofertas/models.py' não tem 'regras', mas seu form sim)
            'avaliacoes',
            'quantidade_maxima_cupons', 
        ]


class BannerSerializer(serializers.ModelSerializer):
    """
    Serializer NOVO para o modelo 'Banner'.
    """
    class Meta:
        model = Banner
        fields = [
            'id',
            'titulo',
            'imagem',
            'url_destino',
            'ordem',
        ]