Aqui está a documentação completa para copiar:

---

```markdown
# IAgromoz — API Documentation

Base URL: `https://<host>/api/`
Autenticação: `Authorization: Bearer <access_token>`

Todos os endpoints protegidos requerem o header de autenticação.
O frontend deve guardar o `access` e `refresh` token após login e enviar o `access` em cada pedido autenticado.

---

## Índice

1. [Autenticação](#1-autenticação)
2. [Utilizadores e Perfis](#2-utilizadores-e-perfis)
3. [Localização](#3-localização)
4. [Feed](#4-feed)
5. [Marketplace — Produtos](#5-marketplace--produtos)
6. [Marketplace — Unidades de Venda](#6-marketplace--unidades-de-venda)
7. [Marketplace — Transações](#7-marketplace--transações)
8. [Marketplace — Chat de Negociação](#8-marketplace--chat-de-negociação)
9. [Avaliações](#9-avaliações)
10. [Pagamentos](#10-pagamentos)
11. [Técnicas](#11-técnicas)
12. [Chat IA](#12-chat-ia)
13. [Notificações](#13-notificações)
14. [Dashboards](#14-dashboards)
15. [Auditoria](#15-auditoria)
16. [Paginação](#16-paginação)
17. [Segurança e Rate Limiting](#17-segurança-e-rate-limiting)
18. [Códigos de Erro](#18-códigos-de-erro)
19. [Variáveis de Ambiente](#19-variáveis-de-ambiente)

---

## 1. Autenticação

### Login com Email e Password

**POST** `/api/token/`

Autentica um utilizador com email e password. Retorna um par de tokens JWT.
O `access` token deve ser enviado em todos os pedidos protegidos.
O `refresh` token serve para renovar o `access` quando este expirar (a cada 15 minutos).

```json
// Request
{
  "email": "utilizador@exemplo.com",
  "password": "minhapassword"
}

// Response 200 — Login bem-sucedido
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}

// Response 401 — Credenciais incorrectas
{
  "detail": "No active account found with the given credentials"
}

// Response 429 — Conta bloqueada após 5 tentativas falhadas
{
  "error": "account_locked",
  "detail": "Conta bloqueada. Tente novamente em 9 minuto(s) e 45 segundo(s).",
  "retry_after": 585
}
```

> Rate limit: 5 tentativas/min por IP.
> Bloqueio de conta: 5 falhas consecutivas bloqueiam a conta por 10 minutos.
> O frontend deve mostrar o tempo restante usando o campo `retry_after` (em segundos).

---

### Renovar Access Token

**POST** `/api/token/refresh/`

Quando o `access` token expira (após 15 minutos), usa o `refresh` token para obter um novo sem precisar que o utilizador faça login novamente. O frontend deve fazer este pedido automaticamente quando receber um erro 401.

```json
// Request
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}

// Response 200 — Novo access token
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}

// Response 401 — Refresh token inválido ou expirado (utilizador deve fazer login novamente)
{
  "detail": "Token is invalid or expired"
}
```

---

### Login com Google

**POST** `/api/auth/google/`

Autentica um utilizador através do Google Identity Services. O frontend obtém o `id_token` do Google e envia-o para este endpoint. O backend valida o token junto ao Google, cria ou associa o utilizador, e retorna os tokens JWT da aplicação.
O Google Token nunca é usado directamente como token da API.

```json
// Request — enviar o id_token obtido do Google no frontend
{
  "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6..."
}

// Response 200 — Login/registo bem-sucedido
{
  "access": "...",
  "refresh": "...",
  "profile_completed": false,
  "missing_fields": ["first_name", "last_name", "district"],
  "required_profile": "NORMAL",
  "user": {
    "id": 1,
    "email": "utilizador@gmail.com",
    "full_name": "Nome Do Google",
    "avatar": "https://lh3.googleusercontent.com/foto...",
    "provider": "GOOGLE"
  }
}
```

> Se `profile_completed` for `false`, o frontend deve redirecionar para o ecrã de completar perfil.
> O campo `missing_fields` indica exactamente quais campos faltam preencher.

```json
// Response 401 — Token Google inválido
{ "error": "invalid_google_token", "detail": "Token Google inválido." }

// Response 401 — Token Google expirado (utilizador deve repetir o login Google)
{ "error": "expired_google_token", "detail": "Google token expirado." }

// Response 401 — Client ID errado (erro de configuração)
{ "error": "invalid_audience", "detail": "Audience inválida." }

// Response 401 — Email Google não verificado
{ "error": "email_not_verified", "detail": "Email Google não verificado." }
```

---

## 2. Utilizadores e Perfis

### Registar Utilizador Normal

**POST** `/api/users/register/normal/`

Cria uma conta de utilizador normal (consumidor/comprador). Não requer autenticação. Após o registo, o utilizador deve fazer login para obter os tokens.

```json
// Request
{
  "email": "joao@exemplo.com",
  "password": "minhapassword123",
  "first_name": "João",
  "last_name": "Silva",
  "district_id": 5,
  "gender": "M"
}

// Response 201 — Conta criada com sucesso
{
  "id": 42,
  "email": "joao@exemplo.com",
  "first_name": "João",
  "last_name": "Silva",
  "role": "NORMAL",
  "can_sell": false
}
```

---

### Registar Produtor

**POST** `/api/users/register/producer/`

Cria uma conta de produtor agrícola. Requer dados adicionais de contacto e endereço da quinta.

```json
// Request
{
  "email": "produtor@exemplo.com",
  "password": "minhapassword123",
  "first_name": "Maria",
  "last_name": "Machava",
  "district_id": 3,
  "gender": "F",
  "contact": "84XXXXXXX",
  "farm_address": "Bairro X, Machava"
}

// Response 201
{
  "id": 43,
  "email": "produtor@exemplo.com",
  "role": "PRODUCER",
  "can_sell": true
}
```

---

### Registar Vendedor

**POST** `/api/users/register/seller/`

Cria uma conta de vendedor. Requer dados do estabelecimento comercial.

```json
// Request
{
  "email": "vendedor@exemplo.com",
  "password": "minhapassword123",
  "first_name": "António",
  "last_name": "Nhantumbo",
  "district_id": 1,
  "gender": "M",
  "seller_type": "INDIVIDUAL",
  "store_name": "Loja do António",
  "nuit": "123456789",
  "contact": "86XXXXXXX",
  "store_address": "Mercado Central, Barraca 12"
}

// seller_type pode ser: INDIVIDUAL, COMPANY ou COOPERATIVE

// Response 201
{
  "id": 44,
  "email": "vendedor@exemplo.com",
  "role": "SELLER",
  "can_sell": true
}
```

---

### Ver Perfil Próprio

**GET** `/api/users/me/`

Retorna os dados do utilizador actualmente autenticado. O frontend usa este endpoint ao carregar a app para obter os dados do utilizador logado.

```json
// Response 200
{
  "id": 42,
  "email": "joao@exemplo.com",
  "first_name": "João",
  "last_name": "Silva",
  "full_name": "João Silva",
  "role": "NORMAL",
  "can_sell": false,
  "gender": "M",
  "district": { "id": 5, "name": "Matola", "province": "Maputo" },
  "profile_photo": "https://res.cloudinary.com/...",
  "total_ratings": null,
  "average_rating": null
}
```

---

### Atualizar Perfil Próprio

**PUT/PATCH** `/api/users/me/update/`

Atualiza os dados básicos do utilizador autenticado. Usar PATCH para atualizar apenas alguns campos.

```json
// Request (PATCH — atualizar apenas o distrito)
{
  "district_id": 7
}

// Response 200 — dados atualizados
```

---

### Ver Perfil Completo

**GET** `/api/users/me/full-profile/`

Retorna o perfil do utilizador junto com o sub-perfil (produtor ou vendedor, se existir). Útil para a página de configurações da conta.

```json
// Response 200
{
  "user": { "id": 42, "email": "...", "role": "SELLER", ... },
  "producer_profile": null,
  "seller_profile": {
    "id": 10,
    "seller_type": "INDIVIDUAL",
    "store_name": "Loja do António",
    "nuit": "***789",
    "contact": "***456",
    "store_address": "Mercado Central"
  }
}
```

---

### Completar Perfil após Login Google

**PATCH** `/api/users/me/complete-profile/`

Usado exclusivamente por utilizadores que fizeram login com Google e têm `profile_completed: false`. Permite preencher os dados em falta. Não é possível alterar `email`, `google_id`, `provider` ou `email_verified`.

```json
// Request
{
  "first_name": "Carlos",
  "last_name": "Mondlane",
  "district_id": 2,
  "phone": "84XXXXXXX"
}

// Response 200
{
  "user": { ... },
  "profile_completed": true,
  "missing_fields": [],
  "required_profile": "NORMAL"
}
```

---

### Ver Perfil de Produtor

**GET** `/api/users/me/producer-profile/`

Retorna o perfil de produtor do utilizador autenticado. Apenas acessível por utilizadores com role PRODUCER.

---

### Atualizar Perfil de Produtor

**PUT/PATCH** `/api/users/me/producer-profile/update/`

```json
// Request
{
  "contact": "84XXXXXXX",
  "farm_address": "Novo endereço da quinta"
}
```

---

### Ver Perfil de Vendedor

**GET** `/api/users/me/seller-profile/`

Retorna o perfil de vendedor. O campo `nuit` e `contact` são mostrados completos apenas ao próprio utilizador e ao admin. Para terceiros são mascarados (ex: `***789`).

---

### Atualizar Perfil de Vendedor

**PUT/PATCH** `/api/users/me/seller-profile/update/`

```json
// Request
{
  "store_name": "Nova Loja",
  "contact": "86XXXXXXX"
}
```

---

### Ver Perfil Público de Outro Utilizador

**GET** `/api/users/<id>/public-profile/`

Retorna o perfil público de qualquer utilizador. Dados sensíveis como `nuit` e `contact` aparecem mascarados. Endpoint público — não requer autenticação.

```json
// Response 200
{
  "user": {
    "id": 44,
    "full_name": "António Nhantumbo",
    "role": "SELLER",
    "district": "Maputo Cidade"
  },
  "seller_profile": {
    "store_name": "Loja do António",
    "seller_type": "INDIVIDUAL",
    "store_address": "Mercado Central",
    "contact": "***456"
  },
  "producer_profile": null,
  "profile_photo": "https://..."
}
```

---

### Alterar Password

**POST** `/api/users/change-password/`

Permite ao utilizador autenticado alterar a sua password. Requer a password actual para confirmação.

```json
// Request
{
  "old_password": "passwordAntiga",
  "new_password": "novaPasswordSegura123"
}

// Response 200
{ "detail": "Password updated successfully." }

// Response 400 — Password actual incorrecta
{ "old_password": ["Current password is incorrect."] }
```

---

### Logout

**POST** `/api/users/logout/`

Invalida o refresh token no servidor (blacklist). O frontend deve apagar os tokens do armazenamento local após este pedido.

```json
// Request
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}

// Response 200
{ "detail": "Logged out successfully." }
```

---

### Pedir Upgrade para Produtor

**POST** `/api/users/upgrade-to-producer/`

Um utilizador com role NORMAL pode pedir para se tornar PRODUCER. O pedido fica pendente até o admin aprovar. Apenas um pedido activo de cada vez.

```json
// Request
{
  "contact": "84XXXXXXX",
  "farm_address": "Bairro X, Localidade Y"
}

// Response 201
{ "detail": "Upgrade request submitted. Awaiting admin approval." }
```

---

### Ver Estado do Pedido de Upgrade

**GET** `/api/users/upgrade-to-producer/status/`

Permite ao utilizador ver o estado do seu pedido de upgrade (PENDING, APPROVED ou REJECTED).

```json
// Response 200
{
  "id": 3,
  "contact": "84XXXXXXX",
  "farm_address": "Bairro X",
  "status": "PENDING",
  "created_at": "2026-01-15T10:30:00Z",
  "reviewed_at": null
}
```

---

### Aprovar/Rejeitar Upgrade (Admin)

**POST** `/api/users/<id>/approve-upgrade/`

Apenas administradores. Aprova ou rejeita o pedido de upgrade do utilizador com o ID indicado.

```json
// Request
{ "decision": "APPROVED" }
// ou
{ "decision": "REJECTED" }

// Response 200
{ "detail": "Upgrade request approved." }
```

---

## 3. Localização

### Listar Províncias

**GET** `/api/provinces/`

Retorna a lista de todas as províncias. Usado para preencher o selector de localização no registo e nos filtros. Endpoint público.

```json
// Response 200
[
  { "id": 1, "name": "Maputo Cidade" },
  { "id": 2, "name": "Maputo Província" },
  ...
]
```

---

### Listar Distritos

**GET** `/api/districts/`

Retorna todos os distritos. Filtrar por província usando o parâmetro `province`.

**GET** `/api/districts/?province=1`

Retorna apenas os distritos da província com id=1.

```json
// Response 200
[
  { "id": 5, "name": "Matola", "province": { "id": 2, "name": "Maputo Província" } },
  ...
]
```

---

## 4. Feed

### Listar Posts

**GET** `/api/feed/posts/`

Retorna todos os posts do feed ordenados do mais recente para o mais antigo. Paginado (20 por página). Endpoint público — não requer autenticação.

Filtros disponíveis:
- `?category=AGRICULTURE` — posts de agricultura
- `?category=LIVESTOCK` — posts de pecuária
- `?author=<id>` — posts de um utilizador específico (ex: ver todos os posts de um produtor)

Cada post inclui: fotos, produtos linkados, comentários, total de likes, e se o utilizador actual já deu like.

```json
// Response 200
{
  "count": 150,
  "next": "https://.../api/feed/posts/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Nova colheita de milho",
      "content": "Excelente colheita este ano...",
      "author": 42,
      "full_name": "Maria Machava",
      "category": "AGRICULTURE",
      "district": 3,
      "district_name": "Machava",
      "province": "Maputo Província",
      "photos": [{ "id": 1, "image": "https://...", "order": 0 }],
      "linked_products": [
        {
          "id": 1,
          "product_id": 5,
          "product_name": "Milho branco",
          "product_price": "150.00",
          "product_district": "Machava",
          "product_province": "Maputo Província",
          "label": "Comprar no marketplace"
        }
      ],
      "total_likes": 23,
      "liked": false,
      "comments": [...],
      "created_at": "2026-07-01T08:00:00Z"
    }
  ]
}
```

---

### Criar Post

**POST** `/api/feed/posts/`

Cria um novo post no feed. Requer autenticação. Utilizadores com role SELLER não podem publicar no feed (apenas no marketplace). O campo `district` é opcional mas recomendado para localizar o conteúdo.

```json
// Request
{
  "title": "Nova colheita disponível",
  "content": "Tenho milho branco disponível em grandes quantidades...",
  "category": "AGRICULTURE",
  "district": 3
}

// Response 201 — Post criado
```

---

### Ver Post Específico

**GET** `/api/feed/posts/<id>/`

Retorna o detalhe completo de um post incluindo todos os comentários em árvore. Endpoint público.

---

### Editar Post

**PUT/PATCH** `/api/feed/posts/<id>/`

Apenas o autor pode editar o seu post. A edição só é permitida nos primeiros 10 minutos após a publicação.

```json
// Request (PATCH)
{ "content": "Conteúdo actualizado..." }

// Response 403 — Se passou mais de 10 minutos
{ "detail": "Edit window expired (10 minutes)." }
```

---

### Eliminar Post

**DELETE** `/api/feed/posts/<id>/`

O autor ou um admin pode eliminar o post.

---

### Adicionar Foto ao Post

**POST** `/api/feed/posts/<id>/add_photo/`

Adiciona uma foto ao post. Máximo de 5 fotos por post. A foto deve ser enviada como `multipart/form-data`. Tipos aceites: JPEG, PNG, WebP. Tamanho máximo: 5MB.

```
// Request — multipart/form-data
Campo: image (ficheiro de imagem)

// Response 201
{ "id": 10, "image": "https://...", "order": 0 }

// Response 400 — Já tem 5 fotos
{ "detail": "Máximo de 5 fotos atingido." }
```

---

### Remover Foto do Post

**DELETE** `/api/feed/posts/<id>/remove_photo/<photo_id>/`

Remove uma foto específica do post. Apenas o autor pode remover.

---

### Obter Produtos do Utilizador para Linkar

**GET** `/api/feed/posts/my-products/`

Retorna os produtos do utilizador autenticado no marketplace. Usar este endpoint para mostrar ao utilizador quais produtos pode linkar ao seu post. Apenas disponível para utilizadores com `can_sell=true`.

```json
// Response 200
[
  {
    "id": 5,
    "name": "Milho branco",
    "price": "150.00",
    "district": 3,
    "province": "Maputo Província",
    "stock_quantity": "500.00",
    "base_unit": "KG"
  }
]
```

---

### Linkar Produto ao Post

**POST** `/api/feed/posts/<id>/link-product/`

Liga um produto do marketplace ao post para que os leitores possam clicar e ir directamente ao produto. Apenas o autor do post pode linkar e só pode linkar os seus próprios produtos.

```json
// Request
{
  "product_id": 5,
  "label": "Ver produto no marketplace"
}

// Response 201 — Produto linkado
{
  "detail": "Produto linkado com sucesso.",
  "product_id": 5,
  "product_name": "Milho branco",
  "label": "Ver produto no marketplace"
}
```

---

### Remover Produto Linkado

**DELETE** `/api/feed/posts/<id>/unlink-product/<product_id>/`

Remove a ligação entre o post e o produto.

---

### Dar/Remover Like

**POST** `/api/feed/posts/<id>/like/`

Alterna o like do utilizador autenticado no post. Se já deu like, remove; se não deu, adiciona.

```json
// Response 200
{ "status": "liked" }
// ou
{ "status": "unliked" }
```

---

### Listar Comentários

**GET** `/api/feed/comments/?post=<id>`

Retorna os comentários de um post em formato de árvore (respostas aninhadas nos comentários pai).

```json
// Response 200
[
  {
    "id": 1,
    "post": 1,
    "author": 42,
    "full_name": "João Silva",
    "message": "Excelente post!",
    "parent": null,
    "created_at": "2026-07-01T09:00:00Z",
    "replies": [
      {
        "id": 2,
        "message": "Obrigado!",
        "parent": 1,
        "replies": []
      }
    ]
  }
]
```

---

### Criar Comentário

**POST** `/api/feed/comments/`

Cria um comentário num post. Para responder a outro comentário, indicar o `parent` com o id do comentário pai.

```json
// Request — comentário simples
{ "post": 1, "message": "Muito bom!", "parent": null }

// Request — resposta a outro comentário
{ "post": 1, "message": "Concordo totalmente!", "parent": 5 }
```

---

### Editar Comentário

**PUT/PATCH** `/api/feed/comments/<id>/`

Apenas o autor pode editar. Janela de 10 minutos após criação.

---

### Eliminar Comentário

**DELETE** `/api/feed/comments/<id>/`

O autor ou um admin pode eliminar.

---

## 5. Marketplace — Produtos

### Listar Produtos

**GET** `/api/marketplace/products/`

Retorna todos os produtos disponíveis no marketplace. Paginado. Endpoint público.

Filtros disponíveis:
- `?seller=<id>` — produtos de um vendedor específico
- `?category=AGRICULTURE` ou `?category=LIVESTOCK`
- `?subcategory=CEREALS` — filtra por subcategoria
- `?district=<id>` — produtos de um distrito específico
- `?page=2` — navegar entre páginas

```json
// Response 200
{
  "count": 80,
  "next": "...?page=2",
  "previous": null,
  "results": [
    {
      "id": 5,
      "seller": "Maria Machava",
      "name": "Milho branco",
      "description": "Milho de qualidade premium...",
      "price": "150.00",
      "category": "AGRICULTURE",
      "subcategory": "CEREALS",
      "district": 3,
      "province": "Maputo Província",
      "stock_quantity": "500.00",
      "base_unit": "KG",
      "photos": [{ "id": 1, "image": "https://...", "order": 0 }],
      "units": [
        { "id": 1, "unit_type": "SACK", "name": "Saco", "multiplier": "50.00", "price": "700.00" }
      ],
      "average_rating": 4.5,
      "total_ratings": 12,
      "user_rated": false
    }
  ]
}
```

---

### Criar Produto

**POST** `/api/marketplace/products/`

Cria um novo produto no marketplace. Apenas disponível para utilizadores com `can_sell=true` (SELLER ou PRODUCER). Enviar como `multipart/form-data`.

```json
// Request
{
  "name": "Feijão nhemba",
  "description": "Feijão de qualidade, colhido recentemente",
  "price": "80.00",
  "category": "AGRICULTURE",
  "subcategory": "LEGUMES",
  "district": 3,
  "stock_quantity": "200.00",
  "base_unit": "KG"
}
// base_unit pode ser: UNIT, KG, TON, LITER
```

---

### Ver Produto Específico

**GET** `/api/marketplace/products/<id>/`

Retorna o detalhe completo de um produto incluindo fotos, unidades de venda e avaliações. Endpoint público.

---

### Editar Produto

**PUT/PATCH** `/api/marketplace/products/<id>/`

Apenas o vendedor dono do produto pode editar.

---

### Eliminar Produto

**DELETE** `/api/marketplace/products/<id>/`

Apenas o vendedor dono ou um admin pode eliminar.

---

### Listar Categorias

**GET** `/api/marketplace/products/categories/`

Retorna as categorias e subcategorias disponíveis. Usado para preencher os selectores de categoria no formulário de criação de produto. Endpoint público com cache de 1 hora.

```json
// Response 200
[
  {
    "value": "AGRICULTURE",
    "label": "Agricultura",
    "subcategories": [
      { "value": "CEREALS", "label": "Cereais" },
      { "value": "LEGUMES", "label": "Leguminosas" },
      ...
    ]
  },
  {
    "value": "LIVESTOCK",
    "label": "Pecuária",
    "subcategories": [...]
  }
]
```

---

### Listar Unidades Base

**GET** `/api/marketplace/products/base_units/`

Retorna as unidades de medida base disponíveis. Usado no formulário de criação de produto. Endpoint público com cache de 1 hora.

```json
// Response 200
[
  { "value": "KG", "label": "Quilograma" },
  { "value": "UNIT", "label": "Unidade" },
  { "value": "TON", "label": "Tonelada" },
  { "value": "LITER", "label": "Litro" }
]
```

---

### Adicionar Foto ao Produto

**POST** `/api/marketplace/products/<id>/add_photo/`

Adiciona uma foto ao produto. Máximo de 5 fotos. Enviar como `multipart/form-data`. Apenas o vendedor dono pode adicionar.

```
// Request — multipart/form-data
Campo: image (ficheiro de imagem)

// Response 201
{ "id": 3, "image": "https://...", "order": 1 }
```

---

### Remover Foto do Produto

**DELETE** `/api/marketplace/products/<id>/remove_photo/<photo_id>/`

Remove uma foto específica do produto.

---

### Reservar Produto (Comprar)

**POST** `/api/marketplace/products/<id>/buy/`

Cria uma reserva do produto. Deduz o stock atomicamente (sem race condition). Cria automaticamente um chat de negociação com o vendedor. O utilizador não pode comprar o seu próprio produto.

```json
// Request — com unidade de venda específica
{
  "unit_id": 1,
  "quantity": 3
}

// Request — sem unidade (usa o preço base por unidade base)
{
  "quantity": 10
}

// Response 201 — Reserva criada
{
  "detail": "Reservation created.",
  "id": 42
}

// Response 400 — Stock insuficiente
{
  "detail": "Stock insuficiente. Disponível: 5.00 KG."
}
```

---

### Ver Transações do Produto (Vendedor)

**GET** `/api/marketplace/products/<id>/transactions/`

Retorna todas as transações de um produto específico. Apenas o vendedor dono pode ver.

---

## 6. Marketplace — Unidades de Venda

### Listar Unidades do Vendedor

**GET** `/api/marketplace/product-units/`

Retorna as unidades de venda criadas pelo utilizador autenticado. Uma unidade de venda define uma forma alternativa de vender 
Continuando a partir de onde ficou:

---

```markdown
### Listar Unidades do Vendedor

**GET** `/api/marketplace/product-units/`

Retorna as unidades de venda criadas pelo utilizador autenticado. Uma unidade de venda define uma forma alternativa de vender o produto (ex: vender por saco de 50kg em vez de por kg). Requer autenticação.

---

### Criar Unidade de Venda

**POST** `/api/marketplace/product-units/`

Cria uma nova unidade de venda para um produto. Permite ao vendedor definir pacotes ou quantidades agrupadas com preço próprio.

```json
// Request
{
  "product_id": 5,
  "unit_type": "SACK",
  "multiplier": "50.00",
  "price": "700.00"
}
// unit_type pode ser: UNIT, DOZEN, FAVO, BOX, SACK, OTHER
// Se unit_type = OTHER, é obrigatório enviar também custom_unit_name
// multiplier = quantas unidades base compõem esta unidade (ex: 50kg por saco)
// price = preço total desta unidade

// Response 201
{
  "id": 1,
  "unit_type": "SACK",
  "name": "Saco",
  "multiplier": "50.00",
  "price": "700.00",
  "is_active": true
}
```

---

### Editar Unidade de Venda

**PUT/PATCH** `/api/marketplace/product-units/<id>/`

Apenas o vendedor dono do produto pode editar.

---

### Eliminar Unidade de Venda

**DELETE** `/api/marketplace/product-units/<id>/`

Apenas o vendedor dono pode eliminar.

---

### Listar Tipos de Unidade

**GET** `/api/marketplace/product-units/sale_unit_choices/`

Retorna os tipos de unidade disponíveis. Endpoint público. Usar para preencher o selector no formulário.

```json
// Response 200
[
  { "value": "UNIT", "label": "Unidade" },
  { "value": "DOZEN", "label": "Dúzia" },
  { "value": "FAVO", "label": "Favo" },
  { "value": "BOX", "label": "Caixa" },
  { "value": "SACK", "label": "Saco" },
  { "value": "OTHER", "label": "Outro" }
]
```

---

## 7. Marketplace — Transações

### Listar Transações

**GET** `/api/marketplace/transactions/`

Retorna todas as transações do utilizador autenticado onde ele é comprador OU vendedor. Paginado.

```json
// Response 200
{
  "count": 15,
  "results": [
    {
      "id": 42,
      "buyer_name": "João Silva",
      "seller_name": "Maria Machava",
      "product_name": "Milho branco",
      "unit_name": "Saco",
      "quantity": "3.00",
      "total_base_quantity": "150.00",
      "amount": "2100.00",
      "status": "RESERVED",
      "created_at": "2026-07-01T10:00:00Z"
    }
  ]
}
```

Estados possíveis: `RESERVED → AWAITING_PAYMENT → PAID → COMPLETED / CANCELLED`

---

### Ver Transação Específica

**GET** `/api/marketplace/transactions/<id>/`

Retorna o detalhe de uma transação. Apenas o comprador, o vendedor ou um admin podem ver.

---

### Confirmar Transação (Vendedor)

**POST** `/api/marketplace/transactions/<id>/confirm/`

O vendedor confirma a reserva, passando o estado para `AWAITING_PAYMENT`. Indica ao comprador que a reserva foi aceite e que deve prosseguir com o pagamento.

```json
// Response 200
{ "detail": "Transaction confirmed." }

// Response 403 — Se não for o vendedor
{ "detail": "Not authorized." }
```

---

### Cancelar Transação (Vendedor)

**POST** `/api/marketplace/transactions/<id>/cancel/`

O vendedor cancela a reserva. O stock é automaticamente devolvido ao produto. Se não houver mais transações activas entre o comprador e o vendedor, o chat de negociação é encerrado automaticamente.

```json
// Response 200
{ "detail": "Transaction cancelled." }
```

---

### Concluir Transação (Vendedor)

**POST** `/api/marketplace/transactions/<id>/conclude/`

O vendedor marca a transação como concluída após a entrega e pagamento. Se não houver mais transações activas, o chat é encerrado automaticamente.

```json
// Response 200
{ "detail": "Transaction completed." }
```

---

## 8. Marketplace — Chat de Negociação

O chat de negociação é criado automaticamente quando uma reserva é feita. Serve para comprador e vendedor comunicarem sobre detalhes da entrega e pagamento. É independente do Chat IA. Apenas o comprador, o vendedor e admins podem aceder.

### Listar Chats Activos

**GET** `/api/marketplace/chats/`

Retorna todos os chats com estado `ACTIVE` do utilizador autenticado. Chats encerrados (`CLOSED`) não aparecem nesta lista mas o histórico permanece acessível via detalhe da transação.

```json
// Response 200
{
  "count": 3,
  "results": [
    {
      "id": 10,
      "buyer": 42,
      "buyer_name": "João Silva",
      "seller": 44,
      "seller_name": "António Nhantumbo",
      "status": "ACTIVE",
      "created_at": "2026-07-01T10:00:00Z",
      "closed_at": null,
      "last_message": {
        "content": "Posso entregar amanhã às 9h",
        "created_at": "2026-07-01T11:30:00Z"
      },
      "unread_count": 2
    }
  ]
}
```

---

### Ver Detalhe do Chat

**GET** `/api/marketplace/chats/<id>/`

Retorna o detalhe de um chat específico incluindo o número de mensagens não lidas.

---

### Listar Mensagens do Chat

**GET** `/api/marketplace/chats/<id>/messages/`

Retorna todas as mensagens do chat ordenadas por data. As mensagens do outro utilizador são automaticamente marcadas como lidas ao fazer este pedido.

```json
// Response 200
[
  {
    "id": 1,
    "chat": 10,
    "sender": 42,
    "sender_name": "João Silva",
    "content": "Olá, quando pode entregar?",
    "is_read": true,
    "created_at": "2026-07-01T10:05:00Z"
  },
  {
    "id": 2,
    "sender": 44,
    "sender_name": "António Nhantumbo",
    "content": "Posso entregar amanhã às 9h",
    "is_read": false,
    "created_at": "2026-07-01T11:30:00Z"
  }
]
```

---

### Enviar Mensagem

**POST** `/api/marketplace/chats/<id>/messages/`

Envia uma mensagem no chat. Apenas permitido em chats com estado `ACTIVE`. Chats encerrados não aceitam novas mensagens.

```json
// Request
{ "content": "Confirmo a entrega para amanhã às 9h." }

// Response 201
{
  "id": 3,
  "sender": 42,
  "sender_name": "João Silva",
  "content": "Confirmo a entrega para amanhã às 9h.",
  "is_read": false,
  "created_at": "2026-07-01T12:00:00Z"
}

// Response 403 — Chat encerrado
{ "detail": "Este chat está encerrado. Não é possível enviar mensagens." }
```

---

### Listar Reservas do Chat

**GET** `/api/marketplace/chats/<id>/reservations/`

Retorna todas as transações (reservas) associadas a este chat.

---

### Obter Chat de uma Reserva

**GET** `/api/marketplace/reservations/<transaction_id>/chat/`

Retorna o chat associado a uma transação específica. Útil para navegar directamente ao chat a partir do detalhe de uma reserva.

---

## 9. Avaliações

### Avaliar Produto

**POST** `/api/marketplace/ratings/<product_id>/rate_product/`

Permite ao utilizador autenticado avaliar um produto. Não é possível avaliar o próprio produto. Apenas uma avaliação por utilizador por produto.

```json
// Request
{
  "score": 4.5,
  "comment": "Produto de boa qualidade, entrega rápida."
}
// score deve estar entre 1.0 e 5.0

// Response 201
{ "detail": "Rating submitted successfully." }

// Response 400 — Já avaliou este produto
{ "detail": "You have already rated this item." }
```

---

### Avaliar Vendedor

**POST** `/api/marketplace/ratings/<seller_id>/rate_seller/`

Permite avaliar um vendedor directamente. Não é possível avaliar-se a si próprio.

```json
// Request
{
  "score": 5,
  "comment": "Excelente vendedor, muito profissional."
}

// Response 201
{ "detail": "Rating submitted successfully." }
```

---

## 10. Pagamentos

### Listar Pagamentos

**GET** `/api/payments/`

Retorna os pagamentos do utilizador autenticado.

---

### Iniciar Pagamento

**POST** `/api/payments/initiate/`

Inicia o processo de pagamento para uma transação. Retorna os dados necessários para o frontend processar o pagamento.

---

### Ver Detalhe do Pagamento

**GET** `/api/payments/<reference>/`

Retorna o detalhe de um pagamento específico usando a referência UUID.

---

### Verificar Estado do Pagamento

**POST** `/api/payments/<reference>/verify/`

Verifica o estado actual de um pagamento junto ao gateway. Usar para actualizar o estado após o utilizador completar o pagamento.

---

### Webhook do Gateway

**POST** `/api/payments/webhook/`

Endpoint interno usado pelo gateway de pagamento para notificar o backend sobre mudanças de estado. Não deve ser chamado directamente pelo frontend.

---

## 11. Técnicas

### Listar Técnicas

**GET** `/api/techniques/`

Retorna as técnicas agrícolas publicadas na plataforma. Paginado. Requer autenticação.

---

### Criar Técnica

**POST** `/api/techniques/`

Cria uma nova técnica agrícola. Requer autenticação.

---

### Ver Técnica Específica

**GET** `/api/techniques/<id>/`

Retorna o detalhe de uma técnica.

---

### Editar Técnica

**PUT/PATCH** `/api/techniques/<id>/`

Apenas o autor pode editar.

---

### Eliminar Técnica

**DELETE** `/api/techniques/<id>/`

O autor ou um admin pode eliminar.

---

### Votar numa Técnica

**POST** `/api/techniques/<id>/vote/`

Permite ao utilizador votar positiva ou negativamente numa técnica. Requer autenticação.

```json
// Request
{ "vote": "UP" }
// ou
{ "vote": "DOWN" }

// Response 200
{ "detail": "Vote registered." }
```

---

## 12. Chat IA

O Chat IA é o assistente inteligente da plataforma. É completamente independente do Chat de Negociação do Marketplace. As sessões requerem autenticação para serem guardadas. Mensagens anónimas são permitidas mas com rate limit.

Rate limit: 20 mensagens/minuto por IP.

### Listar Sessões do Chat IA

**GET** `/api/chat/sessions/`

Retorna todas as sessões de chat do utilizador autenticado. O título de cada sessão é gerado automaticamente a partir das primeiras palavras da primeira mensagem.

```json
// Response 200
[
  { "id": 1, "title": "Como plantar milho" },
  { "id": 2, "title": "Doenças do feijão" }
]
```

---

### Criar Sessão de Chat IA

**POST** `/api/chat/sessions/`

Cria uma nova sessão de chat. Requer autenticação.

```json
// Response 201
{ "id": 3, "title": "Nova conversa" }
```

---

### Listar Mensagens de uma Sessão

**GET** `/api/chat/messages/?session_id=<id>`

Retorna todas as mensagens de uma sessão específica ordenadas por data.

---

### Enviar Mensagem ao Chat IA

**POST** `/api/chat/messages/`

Envia uma mensagem ao assistente e recebe a resposta. Se `session_id` não for indicado, cria uma nova sessão automaticamente. Funciona para utilizadores autenticados e anónimos.

```json
// Request — utilizador autenticado com sessão existente
{
  "session_id": 1,
  "message": "Qual é a melhor época para plantar milho em Moçambique?"
}

// Request — sem sessão (cria automaticamente)
{
  "message": "Como combater pragas no feijão?"
}

// Response 201 — retorna mensagem do utilizador e resposta do bot
[
  {
    "id": 10,
    "message": "Como combater pragas no feijão?",
    "is_bot": false,
    "timestamp": "2026-07-01T10:00:00Z"
  },
  {
    "id": 11,
    "message": "Para combater pragas no feijão, recomendo...",
    "is_bot": true,
    "timestamp": "2026-07-01T10:00:01Z"
  }
]
```

---

## 13. Notificações

### Listar Notificações

**GET** `/api/notifications/`

Retorna todas as notificações do utilizador autenticado ordenadas da mais recente para a mais antiga.

```json
// Response 200
[
  {
    "id": 5,
    "message": "O seu pedido de upgrade foi aprovado.",
    "is_read": false,
    "created_at": "2026-07-01T09:00:00Z"
  }
]
```

---

### Marcar Notificação como Lida

**POST** `/api/notifications/<id>/read/`

Marca uma notificação específica como lida.

```json
// Response 200
{ "detail": "Marked as read." }
```

---

## 14. Dashboards

### Dashboard do Admin

**GET** `/api/admin-dashboard/`

Retorna métricas gerais da plataforma. Apenas para administradores.

---

### Métricas Detalhadas do Admin

**GET** `/api/admin-dashboard/metrics/`

Retorna métricas detalhadas incluindo gráficos e tendências.

---

### Gestão de Utilizadores (Admin)

**GET** `/api/admin-dashboard/users/` — lista todos os utilizadores

**GET** `/api/admin-dashboard/users/<id>/` — detalhe de um utilizador

**PATCH** `/api/admin-dashboard/users/<id>/` — editar dados de um utilizador

**DELETE** `/api/admin-dashboard/users/<id>/` — eliminar utilizador

---

### Gestão de Produtos (Admin)

**GET** `/api/admin-dashboard/products/` — lista todos os produtos

**PATCH** `/api/admin-dashboard/products/<id>/` — editar produto

**DELETE** `/api/admin-dashboard/products/<id>/` — eliminar produto

---

### Gestão de Posts (Admin)

**GET** `/api/admin-dashboard/posts/` — lista todos os posts

**DELETE** `/api/admin-dashboard/posts/<id>/` — eliminar post

---

### Gestão de Técnicas (Admin)

**GET** `/api/admin-dashboard/techniques/`

**DELETE** `/api/admin-dashboard/techniques/<id>/`

---

### Gestão de Transações (Admin)

**GET** `/api/admin-dashboard/transactions/`

**GET** `/api/admin-dashboard/transactions/<id>/`

---

### Dashboard do Vendedor

**GET** `/api/seller-dashboard/`

Retorna métricas do vendedor autenticado: total de produtos, transações, receita, etc.

---

## 15. Auditoria

Todos os endpoints de auditoria requerem role ADMIN.

### Listar Logs de Auditoria

**GET** `/api/audit-logs/`

Retorna todos os logs de actividade da plataforma. Máximo 500 por pedido.

Filtros:
- `?user_email=utilizador@exemplo.com`
- `?action=LOGIN` ou `DELETE` ou `CREATE` etc.
- `?resource=Product`
- `?status=FAILED`
- `?severity=HIGH`
- `?source=API` ou `ADMIN`
- `?ip_address=1.2.3.4`
- `?date=2026-07-01`
- `?date_from=2026-07-01&date_to=2026-07-31`

---

### Listar Logs de Segurança

**GET** `/api/audit-logs/security/`

Retorna eventos de segurança (logins, falhas, bloqueios, alterações de role).

Filtros: `?event_type=LOGIN_FAILED`, `?user_email=...`, `?ip_address=...`, `?date_from=...`

```json
// Response 200
[
  {
    "id": 1,
    "user_email": "joao@exemplo.com",
    "event_type": "LOGIN_FAILED",
    "ip_address": "1.2.3.4",
    "detail": "Failed login attempt for 'joao@exemplo.com'.",
    "timestamp": "2026-07-01T08:00:00Z"
  }
]
```

---

### Estatísticas de Auditoria

**GET** `/api/audit-logs/stats/`

Retorna estatísticas agregadas para o dashboard de segurança.

```json
// Response 200
{
  "total_requests": 15420,
  "total_logins": 892,
  "failed_logins": 34,
  "requests_today": 230,
  "security_events": 156,
  "top_ips": [
    { "ip_address": "1.2.3.4", "count": 120 }
  ],
  "top_endpoints": [
    { "path": "/api/marketplace/products/", "count": 890 }
  ],
  "recent_security_events": [...]
}
```

---

## 16. Paginação

Todos os endpoints de lista são paginados com 20 registos por página.

```
GET /api/marketplace/products/?page=2
GET /api/feed/posts/?page=3
```

```json
// Estrutura da resposta paginada
{
  "count": 150,
  "next": "https://<host>/api/marketplace/products/?page=3",
  "previous": "https://<host>/api/marketplace/products/?page=1",
  "results": [...]
}
```

O frontend deve usar `next` e `previous` para navegar entre páginas.

---

## 17. Segurança e Rate Limiting

| Endpoint | Limite |
|---|---|
| `POST /api/token/` | 5 pedidos/min por IP |
| `POST /api/auth/google/` | 10 pedidos/min por IP |
| `POST /api/chat/messages/` | 20 pedidos/min por IP |

Quando o limite é excedido, a resposta é `429 Too Many Requests`:
```json
{ "detail": "Demasiadas tentativas. Tente novamente mais tarde." }
```

**Bloqueio de conta:**
- 5 tentativas de login falhadas consecutivas → conta bloqueada 10 minutos
- O frontend deve ler o campo `retry_after` e mostrar um contador decrescente
- O bloqueio é por email, não por IP — não é contornável mudando de rede

**Tokens JWT:**
- `access`: válido 15 minutos — o frontend deve renovar automaticamente com o `refresh`
- `refresh`: válido 7 dias — após expirar o utilizador deve fazer login novamente

---

## 18. Códigos de Erro

| Código | Significado | O que fazer no frontend |
|---|---|---|
| `400 Bad Request` | Dados inválidos ou campos em falta | Mostrar erros de validação ao utilizador |
| `401 Unauthorized` | Token inválido ou expirado | Tentar renovar com `/token/refresh/`; se falhar, redirecionar para login |
| `403 Forbidden` | Sem permissão para esta acção | Mostrar mensagem de acesso negado |
| `404 Not Found` | Recurso não encontrado | Mostrar página de erro ou redirecionar |
| `429 Too Many Requests` | Rate limit ou conta bloqueada | Mostrar contador com tempo restante usando `retry_after` |
| `500 Internal Server Error` | Erro interno do servidor | Mostrar mensagem genérica de erro |
