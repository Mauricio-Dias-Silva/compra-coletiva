# IMPLANTAÇÃO: Compra Coletiva AI Turbo 🚀

**Objetivo:** Transformar o projeto atual em uma plataforma de "Compra Coletiva" monetizável, com ingestão automática de produtos via IA (Scan de Encartes) e Pagamentos prontos.

## 1. Upgrade de Dependências (IA & Cloud)
Adicionar suporte ao Gemini (Visão) e Cloud Run.
- [ ] Adicionar `google-generativeai` ao `requirements.txt`.
- [ ] Adicionar `gunicorn` e `whitenoise` (já parecem estar lá, verificar configuração).

## 2. Agente de Visão (O "Scanner de Encartes") 👁️
Criar um serviço que lê fotos de gôndolas ou folhetos de mercado e extrai os produtos automaticamente.
- [ ] Criar `ofertas/services/ai_scanner.py`.
- [ ] Implementar função `scan_flyer(image_path) -> List[Dict]`.
    - Detecta: Nome do Produto, Preço Unitário.
    - Aplica: Margem Automática (ex: +20% para venda final).
- [ ] Criar View no Admin/Dashboard: "Importar Ofertas via Foto".

## 3. Lógica de "Compre Junto" (Refinamento) 🤝
O modelo `Oferta` já tem `tipo_oferta='lote'`, mas precisamos garantir que o fluxo de checkout suporte isso.
- [ ] Verificar `views.py` de `pedidos_coletivos`.
- [ ] Garantir que o estorno ocorra se o lote falhar (ou apenas não cobrar até atingir o alvo - pré-reserva).

## 4. Pagamentos (Mercado Pago) 💸
- [ ] Verificar configuração em `pagamentos/views.py`.
- [ ] Garantir que chaves de API sejam lidas de variáveis de ambiente (`MP_ACCESS_TOKEN`).

## 5. Mobile & SEO 📱
- [ ] Verificar templates base para responsividade.
- [ ] Adicionar Meta Tags dinâmicas (Open Graph) para compartilhamento no WhatsApp ("Compre esse fardo de Coca-Cola comigo!").

## 6. Deploy no PythonJet ☁️
- [ ] Criar/Atualizar `Procfile`.
- [ ] Configurar `settings.py` para ler `DATABASE_URL` e `SECRET_KEY`.
- [ ] Deploy!
