# contas/views_api.py

from rest_framework import viewsets, permissions, generics
from rest_framework.response import Response
from .models import Notificacao
from .serializers import UserSerializer, NotificacaoSerializer

class MeView(generics.RetrieveAPIView):
    """
    API endpoint (Apenas Leitura) que retorna os dados
    do usuário atualmente autenticado (logado).
    Acessível em /api/v1/contas/me/
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        # Retorna o próprio usuário que fez a requisição
        return self.request.user


class NotificacaoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint (Apenas Leitura) para listar as notificações
    do usuário logado.
    Acessível em /api/v1/contas/notificacoes/
    """
    serializer_class = NotificacaoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Filtra o queryset para retornar apenas as notificações
        do usuário que está fazendo a requisição.
        """
        return Notificacao.objects.filter(usuario=self.request.user).order_by('-data_criacao')