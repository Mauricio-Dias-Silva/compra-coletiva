Documentação da API - VarejoUnido (Compra Coletiva)

Este documento descreve a API RESTful para o aplicativo mobile VarejoUnido.

1. URL Base

A API está acessível através da seguinte URL base durante o desenvolvimento:

* **`http://192.168.0.244:8000/api/v1/`** ```

Importante:

Substitua SEU_IP_LOCAL pelo endereço IP da máquina onde o servidor Django (runserver) está rodando (não use 127.0.0.1 ou localhost no celular, use o IP real da sua rede local, ex: 192.168.1.10).

Certifique-se de que o firewall da sua máquina permite conexões na porta 8000.

2. Autenticação (JWT - JSON Web Tokens)

A API usa autenticação JWT. O fluxo é o seguinte:

Obter Tokens (Login):

Método: POST

URL: /token/ (URL completa: http://192.168.0.244:8000/api/v1/)

Corpo da Requisição (JSON):

{
    "username": "email_ou_username_do_usuario",
    "password": "senha_do_usuario"
}


Resposta de Sucesso (200 OK):

{
    "refresh": "TOKEN_REFRESH_LONGO...",
    "access": "TOKEN_ACCESS_CURTO..." 
}


Ação no App: Guardar ambos os tokens (refresh e access) de forma segura (ex: flutter_secure_storage).

Fazer Chamadas Autenticadas:

Para todas as URLs que exigem login (veja a lista de endpoints), inclua o access_token no cabeçalho (Header) Authorization.

Formato do Cabeçalho: Authorization: Bearer SEU_ACCESS_TOKEN

Atualizar o Access Token (Quando Expirar):

O access_token tem vida curta (ex: 15 minutos). Quando uma chamada falhar com erro 401 Unauthorized, use o refresh_token.

Método: POST

URL: /token/refresh/

Corpo da Requisição (JSON):

{
    "refresh": "TOKEN_REFRESH_GUARDADO..."
}


Resposta de Sucesso (200 OK):

{
    "access": "NOVO_TOKEN_ACCESS_CURTO...",
    "refresh": "OPCIONAL_NOVO_TOKEN_REFRESH..." // (Se a rotação estiver ativa)
}


Ação no App: Substituir o(s) token(s) antigo(s) pelo(s) novo(s) e tentar a chamada original novamente.

(Opcional) Verificar Token:

Método: POST

URL: /token/verify/

Corpo da Requisição (JSON):

{
    "token": "TOKEN_ACCESS_OU_REFRESH..."
}


Resposta: 200 OK se válido, 401 Unauthorized se inválido ou expirado.

Logout:

(Ainda não implementado no backend, mas o fluxo será:)

Método: POST

URL: /token/logout/ (ou similar)

Corpo da Requisição: { "refresh": "TOKEN_REFRESH_GUARDADO..." }

Ação no App: Remover ambos os tokens do armazenamento seguro.

3. Endpoints da API

Formato: Todas as requisições e respostas usam JSON.

Legenda de Acesso:

Público: Não precisa de token.

Usuário: Precisa de access_token válido no cabeçalho Authorization: Bearer ....

Vendedor: Precisa de access_token válido E o usuário associado deve ser um Vendedor Aprovado.

3.1 Contas (/api/v1/contas/)

GET /me/

Acesso: Usuário

Descrição: Retorna os dados do usuário logado.

Exemplo Resposta:

{
    "id": 1,
    "username": "mauricio",
    "email": "mauricio@email.com",
    "first_name": "Mauricio",
    "last_name": "Silva",
    "nome_completo": "Mauricio Silva",
    "vendedor": { /* Objeto Vendedor ou null */ } 
}


GET /notificacoes/

Acesso: Usuário

Descrição: Lista as notificações do usuário logado.

Exemplo Resposta: [ { "id": 1, "titulo": "...", ... }, ... ]

GET /notificacoes/{id}/

Acesso: Usuário

Descrição: Detalhes de uma notificação específica do usuário.

3.2 Ofertas (/api/v1/ofertas/)

GET /

Acesso: Público

Descrição: Lista ofertas ativas. Aceita filtros como query parameters (ex: ?search=texto, ?categoria__slug=slug-da-categoria, ?tipo_oferta=lote).

Exemplo Resposta: [ { "id": 1, "titulo": "...", "preco_desconto": "19.90", ... }, ... ] (Usar OfertaListSerializer)

GET /{id_ou_slug}/

Acesso: Público

Descrição: Detalhes de uma oferta.

Exemplo Resposta: { "id": 1, ..., "descricao_detalhada": "...", "avaliacoes": [...] } (Usar OfertaDetailSerializer)

GET /categorias/

Acesso: Público

Descrição: Lista as categorias.

GET /vendedores/

Acesso: Público

Descrição: Lista os vendedores aprovados.

GET /banners/

Acesso: Público

Descrição: Lista os banners ativos.

3.3 Pedidos Coletivos (/api/v1/pedidos/)

GET /

Acesso: Usuário

Descrição: Lista os pedidos coletivos do usuário logado.

POST /

Acesso: Usuário

Descrição: Cria um novo pedido coletivo.

Corpo da Requisição:

{
    "oferta_id": ID_DA_OFERTA_TIPO_LOTE, 
    "quantidade": QUANTIDADE_DESEJADA,
    "usar_credito": true_ou_false 
}


Resposta de Sucesso: Detalhes do pedido criado (incluindo payment_url se o pagamento via MP for necessário).

GET /{id}/

Acesso: Usuário

Descrição: Detalhes de um pedido coletivo específico do usuário.

GET /meu-credito/

Acesso: Usuário

Descrição: Retorna o saldo de crédito do usuário.

Exemplo Resposta: [ { "id": 1, "usuario": {...}, "saldo": "10.50", ... } ] (Retorna uma lista com um item)

GET /meu-historico-credito/

Acesso: Usuário

Descrição: Lista o histórico de transações de crédito do usuário.

3.4 Painel do Vendedor (/api/v1/painel/)

Acesso Geral: Vendedor (Requer Token JWT de um usuário associado a um Vendedor Aprovado).

GET /dashboard/

Acesso: Vendedor

Descrição: Retorna estatísticas de vendas do vendedor.

GET /minhas-ofertas/

Acesso: Vendedor

Descrição: Lista as ofertas criadas por este vendedor.

POST /minhas-ofertas/

Acesso: Vendedor

Descrição: Cria uma nova oferta (ficará pendente de aprovação).

Corpo da Requisição: JSON com os campos de MinhaOfertaWriteSerializer (título, descrição, preços, categoria, etc.).

GET /minhas-ofertas/{id}/

Acesso: Vendedor

Descrição: Detalhes de uma oferta criada por este vendedor.

PUT /minhas-ofertas/{id}/ ou PATCH /minhas-ofertas/{id}/

Acesso: Vendedor

Descrição: Atualiza uma oferta criada por este vendedor.

GET /cupons/

Acesso: Vendedor

Descrição: Lista os cupons vendidos por este vendedor. Aceita filtros (ex: ?status=disponivel, ?q=codigo_ou_email).

POST /cupons/resgatar_cupom_por_codigo/

Acesso: Vendedor

Descrição: Marca um cupom como resgatado usando seu código.

Corpo da Requisição:

{
    "codigo": "CODIGO_DO_CUPOM"
}


Resposta de Sucesso: Detalhes do cupom atualizado.

4. Ferramentas Úteis

Postman / Insomnia: Ferramentas excelentes para testar os endpoints da API antes de implementar no Flutter.

Browsable API: Enquanto o Django runserver estiver rodando, você pode acessar a maioria dessas URLs diretamente no navegador para ver a resposta JSON (exceto para POST/PUT). Lembre-se de fazer login no /admin/ primeiro para testar as rotas que exigem autenticação.

Última atualização: 28 de Outubro de 2025