# vendedores_painel/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.text import slugify
from django.db import transaction
from django.utils import timezone
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# Importe modelos e formulários dos apps relacionados
from ofertas.models import Oferta, Vendedor
from ofertas.forms import OfertaForm
from compras.models import Cupom, Compra
from pedidos_coletivos.models import CreditoUsuario, PedidoColetivo
from contas.models import Usuario


# Decorador para garantir que apenas usuários associados a vendedores APROVADOS acessem o painel
def vendedor_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Você precisa estar logado para acessar esta área.')
            return redirect('account_login')
        
        if not request.user.vendedor or \
           request.user.vendedor.status_aprovacao != 'aprovado':
            
            if request.user.vendedor and request.user.vendedor.status_aprovacao == 'pendente':
                messages.warning(request, 'Seu cadastro de vendedor está pendente de aprovação. Por favor, aguarde a análise.')
            elif request.user.vendedor and request.user.vendedor.status_aprovacao == 'suspenso':
                messages.error(request, 'Sua conta de vendedor está suspensa. Entre em contato com o suporte.')
            elif request.user.vendedor and request.user.vendedor.status_aprovacao == 'rejeitado':
                messages.error(request, 'Seu cadastro de vendedor foi rejeitado. Entre em contato com o suporte para mais informações.')
            else:
                 messages.error(request, 'Você não tem permissão para acessar o painel do vendedor. Cadastre sua empresa ou associe-se a um vendedor aprovado.')
            
            return redirect('ofertas:lista_ofertas')
        return view_func(request, *args, **kwargs)
    return wrapper

@vendedor_required
def dashboard_vendedor(request):
    vendedor_associado = request.user.vendedor
    ofertas_do_vendedor = Oferta.objects.filter(vendedor=vendedor_associado).order_by('-data_criacao')

    # --- Relatórios para o Vendedor ---
    total_cupons_vendidos = Cupom.objects.filter(
    Q(oferta__vendedor=vendedor_associado) & ( # <--- Q object é posicional
        Q(compra__status_pagamento='aprovada') |
        Q(pedido_coletivo__status_pagamento='aprovado_mp', pedido_coletivo__status_lote='concretizado')
    )
).count()


    total_cupons_resgatados = Cupom.objects.filter(
        oferta__vendedor=vendedor_associado,
        status='resgatado'
    ).count()

    receita_bruta_compras_unidade = Compra.objects.filter(
        oferta__vendedor=vendedor_associado,
        status_pagamento='aprovada'
    ).aggregate(Sum('valor_total'))['valor_total__sum'] or 0.00

    receita_bruta_pedidos_coletivos = PedidoColetivo.objects.filter(
        oferta__vendedor=vendedor_associado,
        status_pagamento='aprovado_mp',
        status_lote='concretizado'
    ).aggregate(Sum('valor_total'))['valor_total__sum'] or 0.00
    
    receita_bruta_total = receita_bruta_compras_unidade + receita_bruta_pedidos_coletivos

    contexto = {
        'vendedor': vendedor_associado,
        'ofertas': ofertas_do_vendedor,
        'titulo_pagina': f'Painel do Vendedor: {vendedor_associado.nome_empresa}',
        'total_cupons_vendidos': total_cupons_vendidos,
        'total_cupons_resgatados': total_cupons_resgatados,
        'receita_bruta': receita_bruta_total,
    }
    return render(request, 'vendedores_painel/dashboard.html', contexto)

@vendedor_required
def criar_oferta(request): # <-- FUNÇÃO RESTAURADA
    if request.method == 'POST':
        form = OfertaForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                oferta = form.save(commit=False)
                oferta.vendedor = request.user.vendedor
                oferta.slug = slugify(oferta.titulo)
                
                original_slug = oferta.slug
                num = 1
                while Oferta.objects.filter(slug=oferta.slug).exists():
                    oferta.slug = f"{original_slug}-{num}"
                    num += 1

                oferta.status = 'pendente'
                oferta.publicada = False
                oferta.save()

                messages.success(request, 'Oferta criada com sucesso! Ela passará por moderação antes de ser publicada.')
                return redirect('vendedores_painel:dashboard')
        else:
            messages.error(request, 'Por favor, corrija os erros no formulário.')
    else:
        form = OfertaForm()
    
    contexto = {
        'form': form,
        'titulo_pagina': 'Criar Nova Oferta'
    }
    return render(request, 'vendedores_painel/criar_editar_oferta.html', contexto)

@vendedor_required
def editar_oferta(request, pk): # <-- FUNÇÃO RESTAURADA
    oferta = get_object_or_404(Oferta, pk=pk, vendedor=request.user.vendedor)

    if request.method == 'POST':
        form = OfertaForm(request.POST, request.FILES, instance=oferta)
        if form.is_valid():
            with transaction.atomic():
                oferta = form.save(commit=False)
                if 'titulo' in form.changed_data or Oferta.objects.filter(slug=oferta.slug).exclude(pk=oferta.pk).exists():
                    oferta.slug = slugify(oferta.titulo)
                    original_slug = oferta.slug
                    num = 1
                    while Oferta.objects.filter(slug=oferta.slug).exclude(pk=oferta.pk).exists():
                        oferta.slug = f"{original_slug}-{num}"
                        num += 1

                oferta.save()

                messages.success(request, f'Oferta "{oferta.titulo}" atualizada com sucesso!')
                return redirect('vendedores_painel:dashboard')
        else:
            messages.error(request, 'Por favor, corrija os erros no formulário.')
    else:
        form = OfertaForm(instance=oferta)
    
    contexto = {
        'form': form,
        'oferta': oferta,
        'titulo_pagina': f'Editar Oferta: {oferta.titulo}'
    }
    return render(request, 'vendedores_painel/criar_editar_oferta.html', contexto)

@vendedor_required
def gerenciar_cupons(request): # Renomeada de listar_cupons_vendedor
    vendedor = request.user.vendedor
    
    # CORREÇÃO AQUI: A query do filter() para cupons
    # Garante que as condições de Q estão corretamente passadas como argumentos posicionais
    cupons_queryset = Cupom.objects.filter(
    Q(oferta__vendedor=vendedor) & (
        Q(compra__isnull=False, compra__status_pagamento='aprovada') |
        Q(pedido_coletivo__isnull=False, pedido_coletivo__status_pagamento='aprovado_mp', pedido_coletivo__status_lote='concretizado')
    )
).select_related('oferta', 'usuario', 'compra', 'pedido_coletivo').order_by('-data_criacao')


    status_filter = request.GET.get('status')
    if status_filter and status_filter != 'todos':
        cupons_queryset = cupons_queryset.filter(status=status_filter)

    query = request.GET.get('q')
    if query:
        cupons_queryset = cupons_queryset.filter(
            Q(codigo__icontains=query) |
            Q(usuario__username__icontains=query) |
            Q(usuario__email__icontains=query)
        ).distinct()

    paginator = Paginator(cupons_queryset, 10)
    page = request.GET.get('page')
    try:
        cupons = paginator.page(page)
    except PageNotAnInteger:
        cupons = paginator.page(1)
    except EmptyPage:
        cupons = paginator.page(paginator.num_pages)

    contexto = {
        'cupons': cupons,
        'titulo_pagina': 'Gerenciar Cupons',
        'current_status_filter': status_filter,
        'search_query': query,
        'cupom_status_choices': Cupom.STATUS_CHOICES
    }
    return render(request, 'vendedores_painel/gerenciar_cupons.html', contexto)


@vendedor_required
def resgatar_cupom(request, cupom_id):
    cupom = get_object_or_404(Cupom, id=cupom_id, oferta__vendedor=request.user.vendedor)

    if request.method == 'POST':
        if cupom.status == 'disponivel':
            cupom.status = 'resgatado'
            cupom.data_resgate = timezone.now()
            cupom.save()
            messages.success(request, f'Cupom "{cupom.codigo}" resgatado com sucesso!')
        else:
            messages.warning(request, f'O cupom "{cupom.codigo}" já foi resgatado ou não está disponível.')
        return redirect('vendedores_painel:gerenciar_cupons')
    
    contexto = {
        'cupom': cupom,
        'titulo_pagina': 'Confirmar Resgate de Cupom'
    }
    return render(request, 'vendedores_painel/confirmar_resgate_cupom.html', contexto)


@vendedor_required
def buscar_cupom_para_resgate(request):
    if request.method == 'POST':
        codigo = request.POST.get('codigo_cupom')
        if codigo:
            # Tenta achar cupom exato
            cupom = Cupom.objects.filter(codigo=codigo, oferta__vendedor=request.user.vendedor).first()
            if cupom:
                return redirect('vendedores_painel:resgatar_cupom', cupom_id=cupom.id)
            else:
                messages.error(request, 'Cupom não encontrado ou não pertence a este vendedor.')
    
    contexto = {
        'titulo_pagina': 'Buscar Cupom para Resgate'
    }
    return render(request, 'vendedores_painel/buscar_cupom.html', contexto)


@vendedor_required
def nova_oferta_ia(request):
    """
    Permite ao vendedor tirar uma foto e criar uma oferta automaticamente via IA.
    """
    from django import forms
    from ofertas.services.ai_scanner import AIScannerService
    import os

    class IAUploadForm(forms.Form):
        foto = forms.ImageField(label="Foto do Produto/Prateleira")
        margem = forms.DecimalField(initial=20.0, label="Margem de Lucro (%)", help_text="Quanto você quer ganhar sobre o preço da prateleira?")
        tipo_entrega = forms.ChoiceField(choices=Oferta.TIPO_ENTREGA_CHOICES, initial='retirada', label="Entrega")
        valor_frete = forms.DecimalField(initial=0.00, required=False, label="Valor do Frete (se houver)")

    if request.method == "POST":
        form = IAUploadForm(request.POST, request.FILES)
        if form.is_valid():
            foto = form.cleaned_data['foto']
            margem = float(form.cleaned_data['margem'])
            tipo_entrega = form.cleaned_data['tipo_entrega']
            valor_frete = form.cleaned_data['valor_frete'] or 0.00

            # Salvar Temporário
            temp_path = f"temp_seller_{request.user.id}_{foto.name}"
            with open(temp_path, 'wb+') as destination:
                for chunk in foto.chunks():
                    destination.write(chunk)
            
            try:
                # SCANNER IA
                scanner = AIScannerService()
                products = scanner.scan_flyer(temp_path, margin_percent=margem)
                
                if not products:
                    messages.warning(request, "A IA não conseguiu identificar produtos na imagem. Tente uma foto mais clara.")
                else:
                    count = 0
                    for p in products:
                        # Criação Automática
                        Oferta.objects.create(
                            titulo=p.get('suggested_title') or p.get('name'),
                            descricao_detalhada=f"Oferta Rápida (Smart Seller).\nItem: {p['name']}\nBox/Meta: {p['min_qty']}",
                            preco_original=p['selling_price'] * 1.3,
                            preco_desconto=p['selling_price'],
                            vendedor=request.user.vendedor,
                            categoria=None, # Categoria nula, requer ajuste depois ou IA guess? (Deixar null por enquanto)
                            tipo_oferta='lote', # Default para compra coletiva rápida
                            quantidade_minima_ativacao=p['min_qty'],
                            status='ativa', # AUTO PUBLISH para agilidade? Ou 'pendente'? User pediu agilidade ("tempo curto"). Vamos por ATIVA mas não publicada? Ou Publicada?
                            # O User disse: "se a pessoas colocar o tempo curto... ela ja faz a venda". 
                            # Vamos colocar status='ativa' e publicada=True para ser "Uber" style (Instantâneo).
                            status_pagamento='pendente', # Ops, status da oferta
                            publicada=True, # INSTANT PUBLISH
                            data_termino=timezone.now() + timezone.timedelta(hours=24), # Default 24h
                            tipo_entrega=tipo_entrega,
                            valor_frete=valor_frete
                        )
                        count += 1
                    
                    messages.success(request, f"🚀 Sucesso! {count} ofertas criadas e JÁ ESTÃO NO AR!")
                    return redirect('vendedores_painel:dashboard')

            except Exception as e:
                messages.error(request, f"Erro no processamento da IA: {e}")
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
    else:
        form = IAUploadForm()

    return render(request, 'vendedores_painel/nova_oferta_ia.html', {'form': form, 'titulo_pagina': 'Nova Oferta Flash (IA)'})