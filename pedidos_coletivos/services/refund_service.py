from pedidos_coletivos.models import CreditoUsuario, PedidoColetivo
from compras.models import Compra
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class RefundService:
    @staticmethod
    def processar_reembolso_oferta_cancelada(oferta):
        """
        Devolve o dinheiro de todos os compradores de uma oferta cancelada (falha de meta).
        O dinheiro volta como CRÉDITO na plataforma (Wallet).
        """
        logger.info(f"Iniciando reembolso em massa para oferta: {oferta.titulo}")
        
        pedidos = PedidoColetivo.objects.filter(oferta=oferta, status_pagamento__in=['aprovado_mp', 'aprovada'])
        count = 0
        total_reembolsado = 0.0

        with transaction.atomic():
            for pedido in pedidos:
                valor = float(pedido.valor_total)
                usuario = pedido.usuario
                
                # 1. Adicionar Crédito
                CreditoUsuario.adicionar_credito(
                    usuario=usuario,
                    valor=valor,
                    descricao=f"Reembolso: Oferta {oferta.titulo} não atingiu a meta."
                )
                
                # 2. Atualizar Status do Pedido
                pedido.status_pagamento = 'reembolsado_credito'
                pedido.save()
                
                # 3. Notificar (Email) - Futuro
                # EmailService.enviar_aviso_reembolso(usuario, valor)

                count += 1
                total_reembolsado += valor
        
        logger.info(f"Reembolso concluído. {count} usuários. Total: R$ {total_reembolsado}")
        return count
