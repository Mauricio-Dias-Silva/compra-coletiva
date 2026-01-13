from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    def enviar_confirmacao_pedido(usuario, pedido, tipo="compra"):
        """
        Envia e-mail de confirmação de compra para o usuário.
        """
        assunto = f"VarejoUnido: Pagamento Aprovado! #{pedido.id}"
        
        # Nome do produto
        produto_titulo = pedido.oferta.titulo
        valor = getattr(pedido, 'valor_total', 0)
        
        mensagem = f"""
        Olá, {usuario.first_name or usuario.username}! 
        
        Seu pagamento foi aprovado com sucesso! 🎉
        
        Detalhes do Pedido:
        -------------------
        Item: {produto_titulo}
        Valor: R$ {valor}
        Tipo: {tipo.capitalize()}
        Status: Aprovado
        
        Obrigado por comprar no VarejoUnido!
        
        Acesse seus cupons/pedidos no site para mais detalhes.
        """
        
        try:
            send_mail(
                subject=assunto,
                message=mensagem,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[usuario.email],
                fail_silently=False,
            )
            logger.info(f"EMAIL: Confirmação enviada para {usuario.email}")
        except Exception as e:
            logger.error(f"EMAIL FALHA: Erro ao enviar para {usuario.email}: {e}")

    @staticmethod
    def enviar_aviso_indicacao(usuario_indicador, valor_bonus, amigo_nome):
        """
        Avisa o usuário que ele ganhou créditos por indicação.
        """
        assunto = "VarejoUnido: Você ganhou créditos! 🎁"
        
        mensagem = f"""
        Olá, {usuario_indicador.first_name or usuario_indicador.username}!
        
        Boas notícias! Seu amigo {amigo_nome} acabou de fazer uma compra usando seu código.
        
        Você ganhou R$ {valor_bonus:.2f} em créditos!
        
        Use seus créditos na sua próxima compra.
        """
        
        try:
            send_mail(
                subject=assunto,
                message=mensagem,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[usuario_indicador.email],
                fail_silently=True,
            )
            logger.info(f"EMAIL: Aviso de indicação enviado para {usuario_indicador.email}")
        except Exception as e:
            logger.error(f"EMAIL FALHA: Erro ao enviar aviso de indicação: {e}")
