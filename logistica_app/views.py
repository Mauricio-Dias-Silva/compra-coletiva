from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Entregador, Entrega

@login_required
def painel_motoboy(request):
    # Check if user is a driver
    try:
        entregador = request.user.entregador_perfil
    except:
        messages.error(request, "Você não tem perfil de entregador.")
        return redirect('home') # Adjust redirect
        
    # Entregas Livres (Perto de mim?) - Simulação: Todas as pendentes
    entregas_disponiveis = Entrega.objects.filter(status='pendente').order_by('-data_criacao')
    
    # Minhas Entregas Ativas
    minhas_entregas = Entrega.objects.filter(entregador=entregador, status__in=['aceita', 'coletada']).order_by('-data_criacao')
    
    context = {
        'entregador': entregador,
        'disponiveis': entregas_disponiveis,
        'ativas': minhas_entregas
    }
    return render(request, 'logistica/painel_motoboy.html', context)

@login_required
def aceitar_entrega(request, entrega_id):
    entrega = get_object_or_404(Entrega, id=entrega_id, status='pendente')
    entregador = request.user.entregador_perfil
    
    entrega.entregador = entregador
    entrega.status = 'aceita'
    entrega.save()
    
    messages.success(request, f"Entrega #{entrega.id} aceita! Vá buscar no ponto de coleta.")
    return redirect('logistica_app:painel_motoboy')

@login_required
def atualizar_status(request, entrega_id):
    entrega = get_object_or_404(Entrega, id=entrega_id, entregador__usuario=request.user)
    
    novo_status = request.POST.get('status')
    if novo_status in ['coletada', 'entregue']:
        entrega.status = novo_status
        if novo_status == 'entregue':
            entrega.data_conclusao = timezone.now()
            # Credit Driver BalanceLogic here
            entrega.entregador.saldo_a_receber += entrega.valor_frete
            entrega.entregador.save()
            messages.success(request, "Entrega Concluída! Valor creditado.")
        entrega.save()
        
    return redirect('logistica_app:painel_motoboy')
