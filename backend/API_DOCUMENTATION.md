# IAgromoz — API Documentation

Resumo completo dos endpoints disponíveis no backend Django/DRF.

---

## Autenticação

- `POST /api/token/`
  - Descrição: troca credenciais por JWT.
  - Payload: `{ "username": "<user>", "password": "<pass>" }`
  - Resposta: `{ "access": "<token>", "refresh": "<token>" }`

- `POST /api/token/refresh/`
  - Descrição: renova token de acesso.
  - Payload: `{ "refresh": "<refresh_token>" }`

Observações: incluir header `Authorization: Bearer <access>` para endpoints autenticados.

---

## Localização (referência)

- `GET /api/provincias/` — lista províncias.
- `GET /api/distritos/?provincia=<id>` — lista distritos de uma província.

Campos relevantes: ids numéricos para `provincia` e `distrito` usados em criação de recursos.

---

## Técnicas

- `GET /api/tecnicas/` — lista todas as técnicas.

---

## Marketplace

- `GET /api/marketplace/produtos/`
  - Lista produtos públicos.
- `POST /api/marketplace/produtos/`
  - Cria produto (autenticado).
  - Content-Type: `multipart/form-data`
  - Campos obrigatórios: `nome`, `preco`, `provincia`, `distrito`, `fotografia` (imagem obrigatória).
- `GET /api/marketplace/produtos/<pk>/` — ver produto.
- `PATCH/PUT/DELETE /api/marketplace/produtos/<pk>/` — editar/excluir (apenas dono).
- `GET /api/marketplace/meu-pedido/` — consulta pedidos/produtos do vendedor autenticado (se aplicável).

Notas: `fotografia` é um campo `ImageField` salvo em `MEDIA_ROOT`, acessível via `/media/...`.

---

## Comunidade

- `GET /api/comunidade/sessoes/` — lista sessões de comunidade (títulos, ids).
- `POST /api/comunidade/sessoes/` — cria sessão de comunidade (autenticado/opcional).
- `GET /api/comunidade/mensagens/?session_id=<id>` — lista mensagens de uma sessão.
- `POST /api/comunidade/mensagens/` — cria mensagem; payload: `{ "session_id": <id>, "mensagem": "..." }`.

Publicações de comunidade suportam imagens (campo `fotografia`) em uploads multipart.

---

## Chat (IA)

Fluxo pensado para o frontend: mostrar lista de títulos de sessões; ao seleccionar, carregar mensagens da sessão.

- `GET /api/chat/sessoes/`
  - Retorna lista de sessões do utilizador autenticado.
  - Cada item: `{ "session_id": <id>, "titulo": "..." }`.

- `POST /api/chat/sessoes/`
  - Cria sessão (pode ser omitido — normalmente o front inicia conversação enviando mensagem).
  - O servidor cria sessão com `titulo` placeholder; títulos reais são gerados automaticamente quando a primeira mensagem é enviada.

- `GET /api/chat/mensagens/?session_id=<id>`
  - Retorna todas as mensagens da sessão (ordenadas por `timestamp` ascendente).
  - Cada mensagem inclui: `message_id`, `mensagem`, `is_bot`, `timestamp`, `user` e `session` (objecto com `session_id` + `titulo`).

- `POST /api/chat/mensagens/`
  - Envia mensagem do utilizador e recebe as mensagens criadas (usuário + resposta do bot).
  - Payload JSON aceito: `{ "session_id": <id>, "mensagem": "..." }` — `session_id` é opcional.
  - Se `session_id` ausente e o utilizador autenticado, a API cria automaticamente uma `ChatSession` com `titulo` gerado das primeiras 10 palavras da mensagem.
  - Para utilizadores anónimos, o fluxo responde sem persistir sessão (retorna uma estrutura anónima com mensagens).

Exemplo de resposta (POST com criação de sessão e mensagens):

```json
[
  { "message_id": 101, "mensagem": "Olá", "is_bot": false, "timestamp": "...", "user": {"id":5,...}, "session": {"session_id": 7, "titulo": "Como esta o tempo"} },
  { "message_id": 102, "mensagem": "Resposta do bot", "is_bot": true, "timestamp": "...", "user": {...}, "session": {...} }
]
```

O processamento da IA usa `api/ia/service.py` (função `processar_chat`) que chama provedores em `api/ia/providers.py`.

---

## Users (resumo)

- Endpoints relacionados a utilizadores estão em `api/serializers/users.py` e `api/views/auth.py` (registro/login se existirem). Use JWT para autorização.

---

## Serialização e convenções

- Identificadores renomeados para frontend: `session_id` (de `ChatSession.id`) e `message_id` (de `ChatMessage.id`) usando `source='id'` nos serializers.
- `ChatMessageSimpleSerializer` usado dentro do serializer de sessão para devolver mensagens compactas.

---

## Erros comuns e códigos

- `400 Bad Request` — payload inválido (mensagem vazia, campos obrigatórios em falta).
- `401 Unauthorized` — acesso sem token onde é exigido.
- `404 Not Found` — sessão ou recurso inexistente.
- `415 Unsupported Media Type` — uploads sem `multipart/form-data` para imagens.

---

## Exemplos práticos (curl)

Listar sessões do chat (autenticado):

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://127.0.0.1:8000/api/chat/sessoes/
```

Listar mensagens de uma sessão:

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://127.0.0.1:8000/api/chat/mensagens/?session_id=7"
```

Enviar mensagem (gera sessão automática se `session_id` ausente):

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"mensagem":"Como plantar milho?"}' \
  http://127.0.0.1:8000/api/chat/mensagens/
```

Criar produto com imagem:

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -F nome="Milho" -F preco=20 -F provincia=1 -F distrito=2 \
  -F fotografia=@/path/para/imagem.jpg \
  http://127.0.0.1:8000/api/marketplace/produtos/
```

---

## Arquivos relevantes no repositório

- Serializers: [api/serializers/chat.py](api/serializers/chat.py), [api/serializers/marketplace.py](api/serializers/marketplace.py)
- Views: [api/views/chat.py](api/views/chat.py), [api/views/marketplace.py](api/views/marketplace.py)
- IA: [api/ia/service.py](api/ia/service.py), [api/ia/providers.py](api/ia/providers.py)
- Models principais: [api/models/chat.py](api/models/chat.py), [api/models/marketplace.py](api/models/marketplace.py)
- Config: [iagromoz/settings.py](iagromoz/settings.py)

---

## Próximos passos sugeridos

- Gerar automaticamente esquema OpenAPI com DRF (`/schema/` ou `drf-yasg` / `drf-spectacular`) e expor Swagger UI.
- Adicionar exemplos de resposta para cada endpoint no schema.
- Validar endpoints com testes de integração rápidos (use `curl` ou `pytest-django`).

---

Se quiser que eu: 1) gere o schema OpenAPI automático e adicione Swagger UI, ou 2) rode chamadas de verificação locais (requere ambiente com dependências), diga qual prefere que eu faça a seguir.
