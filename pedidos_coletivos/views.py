# pedidos_coletivos/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
import uuid
from decimal import Decimal # Importe Decimal para o ViewSet

from ofertas.models import Oferta
from .models import PedidoColetivo, CreditoUsuario, HistoricoCredito
from compras.models import Cupom 

from django.urls import reverse 

# (logger, sdk - existentes) ...
# (Importe o logger se ainda não estiver)
import logging
logger = logging.getLogger(__name__)


# --- SUAS VIEWS DA WEB (HTML) ---
# (Todo o seu código de views web permanece aqui, intocado)

@login_required
def fazer_pedido_coletivo(request, slug_oferta):
    oferta = get_object_or_404(
        Oferta, 
        slug=slug_oferta,
        tipo_oferta='lote', 
        publicada=True,
        status='ativa', 
        data_termino__gte=timezone.now() 
    )

    if not oferta.esta_disponivel_para_compra:
        messages.error(request, 'Esta oferta de compra coletiva não está mais disponível para pedidos.')
        return redirect('ofertas:detalhe_oferta', slug_oferta=oferta.slug)

    credito_usuario, created = CreditoUsuario.objects.get_or_create(usuario=request.user)
    saldo_disponivel = credito_usuario.saldo

    valor_total_pedido = oferta.preco_desconto 
    quantidade_comprada = 1

    if request.method == 'POST':
        quantidade_comprada = int(request.POST.get('quantidade', 1)) 
        if quantidade_comprada < 1:
            messages.error(request, 'A quantidade deve ser pelo menos 1.')
            return redirect('pedidos_coletivos:fazer_pedido_coletivo', slug_oferta=oferta.slug)

        valor_total_pedido = oferta.preco_desconto * quantidade_comprada
        
        usar_credito = request.POST.get('usar_credito') == 'on'
        valor_a_pagar_mp = valor_total_pedido
        usar_credito_total = False

        if usar_credito and saldo_disponivel > 0:
            if saldo_disponivel >= valor_total_pedido:
                valor_a_pagar_mp = 0.00
                usar_credito_total = True
            else:
                valor_a_pagar_mp = valor_total_pedido - saldo_disponivel
        
        try:
            with transaction.atomic():
                pedido = PedidoColetivo.objects.create(
                    usuario=request.user,
                    oferta=oferta,
                    quantidade=quantidade_comprada,
                    valor_unitario=oferta.preco_desconto,
                    valor_total=valor_total_pedido, 
                    status_pagamento='pendente', 
                    status_lote='aberto' 
                )

                if usar_credito_total:
                    credito_usuario.usar_credito(valor_total_pedido, 
                                                 f"Pagamento do Pedido Coletivo '{oferta.titulo}' (Pedido #{pedido.id})")
                    pedido.status_pagamento = 'aprovado_mp'
                    pedido.metodo_pagamento = 'Credito do Site'
                    pedido.save()

                    oferta.quantidade_vendida += pedido.quantidade
                    oferta.save()
                    messages.success(request, f'Seu pedido coletivo para "{oferta.titulo}" foi registrado e pago com seu crédito! Aguarde a concretização do lote.')
                    return redirect('pedidos_coletivos:meus_pedidos')
                else:
                    messages.info(request, 'Redirecionando para o Mercado Pago para finalizar o pedido coletivo...')
                    request.session['valor_a_cobrar_mp'] = float(valor_a_pagar_mp) 
                    return redirect(reverse('pagamentos:iniciar_pagamento_mp', args=['pedidocoletivo', pedido.id]))

        except Exception as e:
            messages.error(request, f'Ocorreu um erro ao preparar seu pedido coletivo: {e}. Por favor, tente novamente.')
            return redirect('ofertas:detalhe_oferta', slug_oferta=oferta.slug)
    
    contexto = {
        'oferta': oferta,
        'saldo_disponivel': saldo_disponivel,
        'valor_unitario_oferta': oferta.preco_desconto, 
        'titulo_pagina': f'Fazer Pedido Coletivo: {oferta.titulo}'
    }
    return render(request, 'pedidos_coletivos/fazer_pedido_coletivo.html', contexto)


@login_required
def meu_credito(request):
    credito_usuario, created = CreditoUsuario.objects.get_or_create(usuario=request.user)
    historico = HistoricoCredito.objects.filter(credito_usuario=credito_usuario).order_by('-data_transacao')

    contexto = {
        'credito_usuario': credito_usuario,
        'historico': historico,
        'titulo_pagina': 'Meu Crédito no Site'
    }
    return render(request, 'pedidos_coletivos/meu_credito.html', contexto)


@login_required
def meus_pedidos_coletivos(request):
    pedidos = PedidoColetivo.objects.filter(usuario=request.user).order_by('-data_pedido')
    contexto = {
        'pedidos': pedidos,
        'titulo_pagina': 'Meus Pedidos Coletivos'
    }
    return render(request, 'pedidos_coletivos/meus_pedidos_coletivos.html', contexto)


@transaction.atomic
def adicionar_credito_por_lote_falho(pedido_coletivo):
    credito_usuario, created = CreditoUsuario.objects.get_or_create(usuario=pedido_coletivo.usuario)
    
    valor_a_adicionar = pedido_coletivo.valor_total
    descricao_credito = f"Crédito por falha no lote da oferta: '{pedido_coletivo.oferta.titulo}' (Pedido #{pedido_coletivo.id})"
    
    credito_usuario.adicionar_credito(valor_a_adicionar, descricao_credito)
    
    pedido_coletivo.status_lote = 'falha' 
    pedido_coletivo.status_pagamento = 'lote_cancelado_com_credito' 
    pedido_coletivo.save()
    
    logger.info(f"Crédito de R${valor_a_adicionar:.2f} adicionado ao usuário {pedido_coletivo.usuario.username} por falha de lote do pedido {pedido_coletivo.id}.")


# Tarefa Celery
from celery import shared_task
logger_tasks = logging.getLogger('pedidos_coletivos.tasks') 

@shared_task
def verificar_e_processar_lotes_coletivos():
    logger_tasks.info("Iniciando verificação e processamento de pedidos coletivos...")
    
    ofertas_lote_expiradas = Oferta.objects.filter(
        tipo_oferta='lote',
        status__in=['ativa', 'pendente'], 
        data_termino__lt=timezone.now()
    ).distinct()

    for oferta in ofertas_lote_expiradas:
        with transaction.atomic():
            oferta.refresh_from_db() 
            logger_tasks.info(f"Processando oferta de lote '{oferta.titulo}' (ID: {oferta.id}) - Qtd Vendida: {oferta.quantidade_vendida}, Mínimo: {oferta.quantidade_minima_ativacao}")

            if oferta.quantidade_vendida >= oferta.quantidade_minima_ativacao:
                # Lote BEM-SUCEDIDO
                oferta.status = 'sucesso'
                oferta.save()
                logger_tasks.info(f"Oferta '{oferta.titulo}' - Lote CONCRETIZADO! Processando pedidos aprovados.")
                
                pedidos_aprovados = PedidoColetivo.objects.filter(
                    oferta=oferta, 
                    status_pagamento='aprovado_mp', 
                    status_lote='aberto' 
                )
                
                for pedido in pedidos_aprovados:
                    try:
                        pedido.status_lote = 'concretizado'
                        pedido.data_cupom_gerado = timezone.now()
                        pedido.cupom_gerado = str(uuid.uuid4()).replace('-', '')[:12].upper() 
                        pedido.save()

                        Cupom.objects.create(
                            compra=None, 
                            pedido_coletivo=pedido, # <--- Corrigido (se o models.py tiver o campo)
                            oferta=oferta,
                            usuario=pedido.usuario,
                            codigo=pedido.cupom_gerado,
                            valido_ate=oferta.data_termino,
                            status='disponivel'
                        )
                        logger_tasks.info(f"Pedido Coletivo {pedido.id}: Lote concretizado, cupom {pedido.cupom_gerado} gerado.")

                    except Exception as e:
                        logger_tasks.error(f"Erro ao processar pedido coletivo {pedido.id} (sucesso): {e}", exc_info=True)
            else:
                # Lote FALHOU
                oferta.status = 'falha_lote'
                oferta.save()
                logger_tasks.warning(f"Oferta '{oferta.titulo}' - Lote FALHOU! ({oferta.quantidade_vendida}/{oferta.quantidade_minima_ativacao}). Reembolsando/Creditando.")
                
                pedidos_falhos = PedidoColetivo.objects.filter(
                    oferta=oferta, 
                    status_pagamento='aprovado_mp', 
                    status_lote='aberto' 
                )
                
                for pedido in pedidos_falhos:
                    try:
                        adicionar_credito_por_lote_falho(pedido)
                        logger_tasks.info(f"Pedido Coletivo {pedido.id}: Lote falhou, valor creditado ao usuário.")

                    except Exception as e:
                        logger_tasks.error(f"Erro ao processar reembolso (crédito) para pedido coletivo {pedido.id} (falha): {e}", exc_info=True)
    
    logger_tasks.info("Verificação e processamento de pedidos coletivos concluído.")


# -----------------------------------------------------------------
# --- INÍCIO: API VIEWS (ViewSets para o Flutter) ---
# -----------------------------------------------------------------

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
# (O 'pagamentos' SDK pode ser importado aqui se necessário para a API)
# from pagamentos.mp_sdk import sdk 

# --- CORREÇÃO AQUI ---
# Importamos os nomes corretos que definimos no serializers.py
from .serializers import (
    PedidoColetivoListSerializer,
    PedidoColetivoDetailSerializer,
    CreatePedidoColetivoSerializer,
    CreditoUsuarioSerializer,
    HistoricoCreditoSerializer
)
# ---------------------

class PedidoColetivoViewSet(viewsets.ModelViewSet):
    """
    API endpoint para Pedidos Coletivos (CRUD).
    (CORRIGIDO para usar os serializers corretos)
    """
    queryset = PedidoColetivo.objects.all().order_by('-data_pedido')
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Filtra o queryset para retornar apenas os pedidos do usuário logado.
        """
        return PedidoColetivo.objects.filter(usuario=self.request.user).order_by('-data_pedido')

    def get_serializer_class(self):
        """
        Retorna serializers diferentes para ações diferentes (Lista, Detalhe, Criação).
        """
        if self.action == 'list':
            return PedidoColetivoListSerializer
        if self.action == 'create':
            return CreatePedidoColetivoSerializer
        return PedidoColetivoDetailSerializer # (Para 'retrieve', 'update', 'partial_update')

    def create(self, request, *args, **kwargs):
        """
        Sobrescreve o método 'create' para incluir a lógica de 
        'usar_credito' e 'pagamento_url' (MP).
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Pega os dados validados
        oferta = serializer.validated_data['oferta']
        quantidade = serializer.validated_data['quantidade']
        usar_credito = serializer.validated_data.get('usar_credito', False)
        
        # Lógica de cálculo (similar à sua view web)
        credito_usuario = CreditoUsuario.objects.get(usuario=request.user)
        saldo_disponivel = credito_usuario.saldo
        valor_total_pedido = Decimal(oferta.preco_desconto * quantidade)
        
        valor_a_pagar_mp = valor_total_pedido
        usar_credito_total = False
        valor_credito_usado = Decimal(0.0)

        if usar_credito and saldo_disponivel > 0:
            if saldo_disponivel >= valor_total_pedido:
                valor_a_pagar_mp = Decimal(0.0)
                usar_credito_total = True
                valor_credito_usado = valor_total_pedido
            else:
                valor_a_pagar_mp = valor_total_pedido - saldo_disponivel
                valor_credito_usado = saldo_disponivel
        
        try:
            with transaction.atomic():
                pedido = serializer.save(
                    usuario=request.user,
                    valor_unitario=oferta.preco_desconto,
                    valor_total=valor_total_pedido,
                    status_pagamento='pendente',
                    status_lote='aberto'
                )

                if usar_credito_total:
                    # Pago 100% com crédito
                    credito_usuario.usar_credito(valor_credito_usado, 
                                                 f"Pagamento API Pedido Coletivo '{oferta.titulo}' (Pedido #{pedido.id})")
                    pedido.status_pagamento = 'aprovado_mp'
                    pedido.metodo_pagamento = 'Credito do Site'
                    pedido.save()

                    oferta.quantidade_vendida += pedido.quantidade
                    oferta.save()
                    
                    # Retorna o pedido pago (serializer de detalhe)
                    headers = self.get_success_headers(serializer.data)
                    detail_serializer = PedidoColetivoDetailSerializer(pedido, context={'request': request})
                    return Response(detail_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
                
                elif valor_a_pagar_mp > 0:
                    # [REAL-PAYMENT] Mercado Pago SDK Integration
                    import mercadopago
                    from django.conf import settings
                    sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
                    
                    base_url = request.build_absolute_uri('/')[:-1]
                    success_url = f"{base_url}/pagamentos/retorno/sucesso/pedidocoletivo/{pedido.id}/"
                    
                    preference_data = {
                        "items": [
                            {
                                "title": f"Pedido Coletivo: {oferta.titulo}",
                                "quantity": 1,
                                "unit_price": float(valor_a_pagar_mp),
                                "currency_id": "BRL",
                            }
                        ],
                        "payer": {
                            "email": request.user.email,
                        },
                        "external_reference": f"pedidocoletivo_{pedido.id}",
                        "back_urls": {
                            "success": success_url,
                            "pending": success_url,
                            "failure": f"{base_url}/ofertas/"
                        },
                        "auto_return": "all",
                    }
                    
                    preference_response = sdk.preference().create(preference_data)
                    preference = preference_response["response"]
                    
                    payment_url = preference.get("init_point") if not settings.DEBUG else preference.get("sandbox_init_point")
                    preference_id = preference.get("id")
                    
                    # Salva o ID da preferência no pedido
                    pedido.id_preferencia_mp = preference_id
                    pedido.save()

                    # Retorna o pedido pendente + a URL de pagamento real
                    headers = self.get_success_headers(serializer.data)
                    detail_serializer = PedidoColetivoDetailSerializer(pedido, context={'request': request})
                    
                    # Adiciona a URL de pagamento ao JSON de resposta
                    response_data = detail_serializer.data
                    response_data['payment_url'] = payment_url 
                    
                    return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)

        except Exception as e:
            return Response({'error': f'Erro ao criar pedido: {e}'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Fallback (não deve acontecer)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreditoUsuarioViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint (Apenas Leitura) para Créditos do Usuário.
    """
    queryset = CreditoUsuario.objects.all()
    serializer_class = CreditoUsuarioSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Filtra para mostrar apenas o crédito do usuário logado.
        """
        return CreditoUsuario.objects.filter(usuario=self.request.user)


class HistoricoCreditoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint (Apenas Leitura) para Histórico de Créditos.
    """
    queryset = HistoricoCredito.objects.all()
    serializer_class = HistoricoCreditoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Filtra para mostrar apenas o histórico do usuário logado.
        """
        credito_usuario = CreditoUsuario.objects.get(usuario=self.request.user)
        return HistoricoCredito.objects.filter(credito_usuario=credito_usuario).order_by('-data_transacao')

# --- FIM: API VIEWS ---