Aqui está o conteúdo completo para colar no `API_DOCUMENTATION.md`:

---

```markdown
# IAgromoz — API Documentation

Base URL: `https://<host>/api/`

Autenticação: JWT via header `Authorization: Bearer <access_token>`

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

### Email + Password

**POST** `/api/token/`
```json
// Request
{ "email": "user@example.com", "password": "secret" }

// Response 200
{ "access": "...", "refresh": "..." }
```

**POST** `/api/token/refresh/`
```json
// Request
{ "refresh": "<refresh_token>" }

// Response 200
{ "access": "..." }
```

> Rate limit: 5 tentativas/min por IP.
> Bloqueio de conta: 5 falhas consecutivas → bloqueio 10 minutos.

```json
// Response 429 — conta bloqueada
{
  "error": "account_locked",
  "detail": "Conta bloqueada. Tente novamente em 9 minuto(s) e 45 segundo(s).",
  "retry_after": 585
}
```

---

### Google OAuth 2.0

**POST** `/api/auth/google/`

Rate limit: 10 tentativas/min por IP.

```json
// Request
{ "id_token": "<google_id_token>" }

// Response 200
{
  "access": "...",
  "refresh": "...",
  "profile_completed": false,
  "missing_fields": ["first_name", "last_name", "district"],
  "required_profile": "NORMAL",
  "user": {
    "id": 1,
    "email": "user@gmail.com",
    "full_name": "Nome Google",
    "avatar": "https://lh3.googleusercontent.com/...",
    "provider": "GOOGLE"
  }
}

// Response 401 — token inválido
{ "error": "invalid_google_token", "detail": "Token Google inválido." }

// Response 401 — token expirado
{ "error": "expired_google_token", "detail": "Google token expirado." }

// Response 401 — audience errada
{ "error": "invalid_audience", "detail": "Audience inválida." }
```

> O Google Token nunca é usado como token da API. Usar sempre o JWT retornado.

---

## 2. Utilizadores e Perfis

### Registo

**POST** `/api/users/register/normal/`
```json
{ "email": "...", "password": "...", "first_name": "...", "last_name": "...", "district_id": 1, "gender": "M" }
```

**POST** `/api/users/register/producer/`
```json
{ "email": "...", "password": "...", "first_name": "...", "last_name": "...", "district_id": 1, "gender": "M", "contact": "84XXXXXXX", "farm_address": "..." }
```

**POST** `/api/users/register/seller/`
```json
{
  "email": "...", "password": "...", "first_name": "...", "last_name": "...",
  "district_id": 1, "gender": "M",
  "seller_type": "INDIVIDUAL",
  "store_name": "...", "nuit": "...", "contact": "84XXXXXXX", "store_address": "..."
}
```

---

### Perfil do utilizador autenticado

**GET** `/api/users/me/` — dados do utilizador atual.

**PUT/PATCH** `/api/users/me/update/` — atualiza dados básicos.

**GET** `/api/users/me/full-profile/` — dados completos (user + sub-perfil).

**PATCH** `/api/users/me/complete-profile/`
Completa perfil após login Google. Campos proibidos: `email`, `google_id`, `provider`, `email_verified`.
```json
// Request
{ "first_name": "João", "last_name": "Silva", "district_id": 3, "phone": "84XXXXXXX" }

// Response 200
{
  "user": { ... },
  "profile_completed": true,
  "missing_fields": [],
  "required_profile": "NORMAL"
}
```

---

### Perfis específicos

**GET** `/api/users/me/producer-profile/`

**PUT/PATCH** `/api/users/me/producer-profile/update/`

**GET** `/api/users/me/seller-profile/`

**PUT/PATCH** `/api/users/me/seller-profile/update/`

> `contact` e `nuit` são mascarados para terceiros (ex: `***789`). Apenas o próprio e admins veem os valores completos.

---

### Outras ações

**GET** `/api/users/<id>/public-profile/` — público, dados sensíveis mascarados.

**POST** `/api/users/change-password/`
```json
{ "old_password": "...", "new_password": "..." }
```

**POST** `/api/users/logout/`
```json
{ "refresh": "<refresh_token>" }
```

**POST** `/api/users/upgrade-to-producer/`
```json
{ "contact": "84XXXXXXX", "farm_address": "Endereço da quinta" }
```

**GET** `/api/users/upgrade-to-producer/status/`

**POST** `/api/users/<id>/approve-upgrade/` — apenas admin.
```json
{ "decision": "APPROVED" }
```

---

## 3. Localização

**GET** `/api/provinces/`

**GET** `/api/districts/` ou `?province=<id>`

---

## 4. Feed

### Posts

**GET** `/api/feed/posts/` — público, paginado (20/página).

Query params: `?category=AGRICULTURE` ou `?category=LIVESTOCK`

Resposta inclui: `district`, `district_name`, `province`, `linked_products`, `photos`, `comments`, `total_likes`, `liked`.

**POST** `/api/feed/posts/`
```json
{ "title": "...", "content": "...", "category": "AGRICULTURE", "district": 5 }
```

**GET** `/api/feed/posts/<id>/`

**PUT/PATCH** `/api/feed/posts/<id>/` — autor, janela de 10 minutos.

**DELETE** `/api/feed/posts/<id>/` — autor ou admin.

---

### Fotos do post

**POST** `/api/feed/posts/<id>/add_photo/`
Multipart. Campo: `image`. Máximo 5 fotos. Tipos: `image/jpeg`, `image/png`, `image/webp`. Máximo 5MB.

**DELETE** `/api/feed/posts/<id>/remove_photo/<photo_id>/`

---

### Produtos linkados ao post

**GET** `/api/feed/posts/my-products/`
Lista produtos do utilizador no marketplace (`can_sell=True`).

**POST** `/api/feed/posts/<id>/link-product/`
```json
{ "product_id": 3, "label": "Ver produto no marketplace" }
```

**DELETE** `/api/feed/posts/<id>/unlink-product/<product_id>/`

---

### Likes e Comentários

**POST** `/api/feed/posts/<id>/like/`
```json
// Response
{ "status": "liked" }
```

**GET** `/api/feed/comments/?post=<id>` — árvore com respostas aninhadas.

**POST** `/api/feed/comments/`
```json
{ "post": 1, "message": "Excelente!", "parent": null }
```

**PUT/PATCH** `/api/feed/comments/<id>/` — janela de 10 minutos.

**DELETE** `/api/feed/comments/<id>/`

---

## 5. Marketplace — Produtos

**GET** `/api/marketplace/products/` — público, paginado.

**POST** `/api/marketplace/products/` — requer `can_sell=True`. Multipart.

Campos: `name`, `description`, `price`, `category`, `subcategory`, `subcategory_description`, `district`, `stock_quantity`, `base_unit`.

**GET** `/api/marketplace/products/<id>/`

**PUT/PATCH** `/api/marketplace/products/<id>/` — apenas vendedor dono.

**DELETE** `/api/marketplace/products/<id>/`

**GET** `/api/marketplace/products/categories/` — público, cache 1 hora.

**GET** `/api/marketplace/products/base_units/` — público, cache 1 hora.

---

### Fotos do produto

**POST** `/api/marketplace/products/<id>/add_photo/`
Multipart. Campo: `image`. Máximo 5 fotos. Tipos: `image/jpeg`, `image/png`, `image/webp`. Máximo 5MB.

**DELETE** `/api/marketplace/products/<id>/remove_photo/<photo_id>/`

---

### Reserva

**POST** `/api/marketplace/products/<id>/buy/`
```json
// Request
{ "unit_id": 2, "quantity": 3 }

// Response 201
{ "detail": "Reservation created.", "id": 42 }
```

> Deduz stock atomicamente com `select_for_update` (sem race condition).
> Cria automaticamente chat de negociação com o vendedor.

---

## 6. Marketplace — Unidades de Venda

**GET** `/api/marketplace/product-units/`

**POST** `/api/marketplace/product-units/`
```json
{ "product_id": 1, "unit_type": "BOX", "multiplier": 10, "price": 250 }
```
> Se `unit_type = OTHER`, campo `custom_unit_name` é obrigatório.

**PUT/PATCH/DELETE** `/api/marketplace/product-units/<id>/`

**GET** `/api/marketplace/product-units/sale_unit_choices/` — público.

---

## 7. Marketplace — Transações

**GET** `/api/marketplace/transactions/` — paginado (buyer ou seller).

**GET** `/api/marketplace/transactions/<id>/`

**POST** `/api/marketplace/transactions/<id>/confirm/` — vendedor → `AWAITING_PAYMENT`

**POST** `/api/marketplace/transactions/<id>/cancel/` — vendedor → `CANCELLED` + devolve stock

**POST** `/api/marketplace/transactions/<id>/conclude/` — vendedor → `COMPLETED`

**GET** `/api/marketplace/products/<id>/transactions/` — apenas o vendedor do produto.

Estados: `RESERVED → AWAITING_PAYMENT → PAID → COMPLETED / CANCELLED`

---

## 8. Marketplace — Chat de Negociação

> Chat criado automaticamente após reserva. Independente do Chat IA.
> Acesso restrito ao comprador, vendedor e admins.
> Chats `CLOSED` não aparecem na listagem mas o histórico permanece.

**GET** `/api/marketplace/chats/` — chats `ACTIVE` do utilizador.

**GET** `/api/marketplace/chats/<id>/` — inclui `last_message` e `unread_count`.

**GET** `/api/marketplace/chats/<id>/messages/` — marca mensagens como lidas.

**POST** `/api/marketplace/chats/<id>/messages/`
```json
// Request — apenas em chats ACTIVE
{ "content": "Podemos combinar entrega para amanhã?" }
```

**GET** `/api/marketplace/chats/<id>/reservations/`

**GET** `/api/marketplace/reservations/<transaction_id>/chat/`

---

## 9. Avaliações

**POST** `/api/marketplace/ratings/<product_id>/rate_product/`
```json
{ "score": 4.5, "comment": "Muito bom produto." }
```

**POST** `/api/marketplace/ratings/<seller_id>/rate_seller/`
```json
{ "score": 5, "comment": "Excelente vendedor." }
```

---

## 10. Pagamentos

**GET** `/api/payments/`

**POST** `/api/payments/initiate/`

**GET** `/api/payments/<reference>/`

**POST** `/api/payments/<reference>/verify/`

**POST** `/api/payments/webhook/` — uso interno do gateway.

---

## 11. Técnicas

**GET** `/api/techniques/`

**POST** `/api/techniques/`

**GET/PUT/PATCH/DELETE** `/api/techniques/<id>/`

**POST** `/api/techniques/<id>/vote/`
```json
{ "vote": "UP" }
```

---

## 12. Chat IA

Rate limit: 20 mensagens/min por IP.
Sessões requerem autenticação. Mensagens anónimas permitidas mas com rate limit.

**GET** `/api/chat/sessions/` — autenticado.

**POST** `/api/chat/sessions/`

**GET** `/api/chat/messages/?session_id=<id>`

**POST** `/api/chat/messages/`
```json
// Autenticado
{ "session_id": 5, "message": "Como plantar milho?" }

// Anónimo
{ "message": "Como plantar milho?" }
```

---

## 13. Notificações

**GET** `/api/notifications/`

**POST** `/api/notifications/<id>/read/`

---

## 14. Dashboards

### Admin

**GET** `/api/admin-dashboard/`

**GET** `/api/admin-dashboard/metrics/`

**GET/PATCH/DELETE** `/api/admin-dashboard/users/<id>/`

**GET/PATCH/DELETE** `/api/admin-dashboard/products/<id>/`

**GET/PATCH/DELETE** `/api/admin-dashboard/posts/<id>/`

**GET/PATCH/DELETE** `/api/admin-dashboard/techniques/<id>/`

**GET/PATCH/DELETE** `/api/admin-dashboard/transactions/<id>/`

### Vendedor/Produtor

**GET** `/api/seller-dashboard/`

---

## 15. Auditoria

Todos os endpoints requerem role `ADMIN`.

**GET** `/api/audit-logs/`

Query params: `user_email`, `action`, `resource`, `resource_id`, `status`, `severity`, `source`, `ip_address`, `request_id`, `date`, `date_from`, `date_to`

**GET** `/api/audit-logs/security/`

Query params: `event_type`, `user_email`, `ip_address`, `date_from`, `date_to`

**GET** `/api/audit-logs/stats/`

```json
// Response
{
  "total_requests": 15420,
  "total_logins": 892,
  "failed_logins": 34,
  "requests_today": 230,
  "security_events": 156,
  "top_ips": [{"ip_address": "1.2.3.4", "count": 120}],
  "top_endpoints": [{"path": "/api/marketplace/products/", "count": 890}],
  "recent_security_events": [...]
}
```

---

## 16. Paginação

Todos os endpoints de lista são paginados. 20 registos por página.

```
GET /api/marketplace/products/?page=2
```

```json
{
  "count": 150,
  "next": "https://.../api/marketplace/products/?page=3",
  "previous": "https://.../api/marketplace/products/?page=1",
  "results": [...]
}
```

---

## 17. Segurança e Rate Limiting

| Endpoint | Limite |
|---|---|
| `POST /api/token/` | 5 req/min por IP |
| `POST /api/auth/google/` | 10 req/min por IP |
| `POST /api/chat/messages/` | 20 req/min por IP |

Bloqueio de conta:
- 5 tentativas falhadas → conta bloqueada por 10 minutos
- Resposta `429` com `retry_after` em segundos

Tokens JWT:
- Access token: 15 minutos
- Refresh token: 7 dias (rotação automática com blacklist)

---

## 18. Códigos de Erro

| Código | Significado |
|---|---|
| `400` | Payload inválido ou campos obrigatórios em falta |
| `401` | Não autenticado ou token inválido/expirado |
| `403` | Autenticado mas sem permissão |
| `404` | Recurso não encontrado |
| `429` | Rate limit excedido ou conta bloqueada |
| `500` | Erro interno do servidor |

Erros específicos Google Auth:

| `error` | Causa |
|---|---|
| `invalid_google_token` | Token inválido ou assinatura errada |
| `expired_google_token` | Token Google expirado |
| `invalid_audience` | Client ID não corresponde |
| `email_not_verified` | Email Google não verificado |
| `account_locked` | Conta bloqueada por tentativas falhadas |

---

## 19. Variáveis de Ambiente

```env
DJANGO_SECRET_KEY=...
DEBUG=False
ALLOWED_HOSTS=app.iagromoz.com
DATABASE_NAME=...
DATABASE_USER=...
DATABASE_PASSWORD=...
DATABASE_HOST=...
DATABASE_PORT=5432
GOOGLE_API_KEY=...
GOOGLE_CLIENT_ID=...
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=https://app.iagromoz.com
DJANGO_ADMIN_URL=gestao-interna/
PAYMENT_MODE=LIVE
ACCOUNT_LOCKOUT_MAX_ATTEMPTS=5
ACCOUNT_LOCKOUT_DURATION_SECONDS=600
```
```