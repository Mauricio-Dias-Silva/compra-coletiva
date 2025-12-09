from rest_framework import permissions

class IsVendedorAprovado(permissions.BasePermission):
    """
    Permissão customizada da API para replicar o decorador '@vendedor_required'.
    """
    
    # Mensagem genérica, podemos customizar na view se necessário
    message = 'Você não tem permissão para acessar o painel do vendedor.'

    def has_permission(self, request, view):
        # 1. Precisa estar logado
        if not request.user or not request.user.is_authenticated:
            self.message = 'Autenticação necessária.'
            return False
            
        # 2. Precisa estar associado a um Vendedor
        vendedor = getattr(request.user, 'vendedor', None)
        if not vendedor:
            self.message = 'Você não está associado a uma conta de vendedor.'
            return False
            
        # 3. O Vendedor precisa estar APROVADO
        if vendedor.status_aprovacao == 'aprovado':
            return True
            
        # 4. Mensagens de erro específicas
        if vendedor.status_aprovacao == 'pendente':
            self.message = 'Seu cadastro de vendedor está pendente de aprovação.'
        elif vendedor.status_aprovacao == 'suspenso':
            self.message = 'Sua conta de vendedor está suspensa.'
        elif vendedor.status_aprovacao == 'rejeitado':
            self.message = 'Seu cadastro de vendedor foi rejeitado.'
        
        return False
