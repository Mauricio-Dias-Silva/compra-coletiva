# 📘 Manual de Operação: Compra Coletiva AI 👁️

Este projeto foi turbinado com Inteligência Artificial (Gemini Vision) para **Ingestão Automática de Produtos** e **Lógica de Caixa Fechada**.

## 1. Configuração Inicial
Antes de rodar, certifique-se de que sua chave da API do Google Gemini está configurada.
No Painel PythonJet (Variáveis de Ambiente) ou `.env` local:
```
GEMINI_API_KEY=sua_chave_aqui
```

## 2. Como Importar Produtos (O "Pulo do Gato") 🐈
Você não precisa digitar nada.
1. Vá no Supermercado/Atacadão.
2. Tire foto da prateleira ou do encarte de ofertas.
3. Acesse o Admin: `https://seu-site.com/admin/ofertas/oferta/`.
4. Clique no botão roxo: **Importar Encarte (IA) 👁️**.
5. Faça upload da foto e defina sua margem de lucro (ex: 30%).

## 3. A Lógica "Caixa Fechada" 📦
A IA foi treinada para identificar "Packs" (Caixas, Fardos).
- Se a IA ver "Detergente (Cx 12)":
    - Ela cria a oferta.
    - Define `Qtd Mínima de Ativação = 12`.
    - Define `Tipo = Lote`.
- **Resultado:** O site vende unidades soltas para os vizinhos. O pagamento só é confirmado quando o grupo juntar 12 unidades. Aí você busca a caixa.

## 4. Revisão
As ofertas criadas pela IA entram como **"Pendente"**.
Você deve revisá-las e marcar a caixa **"Publicada"** para irem ao ar.

## 4. Modo Vendedor "Uberized" (Qualquer um pode vender) 🛵
O sistema permite que qualquer usuário cadastrado e aprovado venda ofertas.

### Fluxo de Cadastro:
1.  Usuário acessa `/contas/seja-vendedor/` e preenche os dados.
2.  Status inicial: **Pendente de Aprovação**.
3.  Admin (Você) acessa o Painel Admin e **Aprova** o vendedor.
4.  O vendedor ganha acesso ao Painel de Vendedor (`/painel/`).

### Fluxo de Venda Rápida (Smart Flash):
1.  O Vendedor acessa o painel e clica em **"Nova Oferta Flash (IA)"**.
2.  Tira foto da prateleira do mercado.
3.  Define a margem (ex: 15%) e o tipo de entrega (Retirada ou Frete).
4.  **Instantâneo:** A oferta vai ao ar imediatamente com o status **Ativa (Lote)**.

**Obs:** Como Admin, monitore as ofertas criadas para garantir qualidade.

---
*Desenvolvido em Modo Engenheiro Senior Turbo 🚀*
