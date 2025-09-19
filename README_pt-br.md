# LinkedIn Poster API (Clean Architecture)

Uma API **FastAPI** open‑source para **autenticar com LinkedIn (OAuth 2.0 + OIDC)** e **publicar posts** (texto e **imagem**) no feed do usuário — com **Clean Architecture**, **SOLID**, configuração via **Pydantic Settings**, **atualização automática de tokens** (refresh) e testes unitários com **unittest**.

> **Why**: projeto didático/profissional para aprender **design de APIs backend**, OAuth/OIDC, integração com **LinkedIn Posts API** e práticas de engenharia (organização, testes, segurança, DX).

---

## ✨ Features

* **Autenticação OAuth 2.0 + OIDC** com validação de `state` (CSRF) e suporte a `offline_access`.
* **Refresh automático** de `access_token` (grant `refresh_token`), com **lock** para evitar corrida.
* **Post de texto** no feed (campo `commentary`), com validação de comprimento e normalização.
* **Post com imagem** via **Images API** (`/rest/images?action=initializeUpload`) + **Posts API** (`/rest/posts`).
* **Persistência de sessão** (memória ou arquivo JSON) — reinicie o servidor sem perder login.
* **Configuração** centralizada (env/.env) com validações Pydantic.
* **Observabilidade**: health checks, status de auth, erros com detalhes sanitizados.
* **Arquitetura limpa**: camadas *domain* → *application* → *infra* → *presentation*.
* **Testes unitários** com `unittest` e estrutura espelhada de `src/`.

---

## 🧱 Stack & decisões de projeto

* **FastAPI** (framework HTTP) + **Uvicorn** (ASGI).
* **httpx** (cliente HTTP, timeouts, exceções claras).
* **pydantic / pydantic-settings** (modelos & config com validação).
* **python-jose** (leitura do `id_token` – *sem* validação de assinatura no MVP).
* **Clean Architecture** (separação de camadas e dependências — DIP).
* **SOLID** (contratos via `Protocol`/interfaces; serviços enxutos; SRP).

---

## 📁 Estrutura

```
linkedin-posts/
├─ src/
│  └─ app/
│     ├─ main.py                      # composição da aplicação (FastAPI)
│     ├─ config/
│     │  └─ settings.py               # Settings (Pydantic) + defaults
│     ├─ domain/
│     │  ├─ models/
│     │  │  ├─ post.py                # Post (texto) – validações (bytes→str, limites)
│     │  │  ├─ image_post.py          # Post de imagem (bytes + mime)
│     │  │  └─ token.py               # Token bundle (access/refresh/exp/urn)
│     │  └─ repositories/
│     │     └─ token_repository.py    # contrato (Protocol/ABC)
│     ├─ application/
│     │  └─ services/
│     │     ├─ auth_service.py        # fluxo OAuth/OIDC e status
│     │     ├─ post_service.py        # orquestra post texto/imagem
│     │     └─ health_service.py      # health/env-check
│     ├─ infra/
│     │  ├─ client/
│     │  │  └─ linkedin_client.py     # chamadas LinkedIn (authorize, token, refresh, posts, images)
│     │  └─ persistence/
│     │     ├─ token_repository_file.py   # persistência em arquivo
│     │     └─ token_repository_memory.py # persistência em memória
│     └─ presentation/
│        ├─ routes/
│        │  ├─ auth.py                 # /auth/login, /auth/callback, /auth/status
│        │  ├─ post.py                 # /posts (texto) & /posts/image (multipart)
│        │  └─ health.py               # /health, /health/env-check
│        └─ deps.py                    # providers (Settings, Client, Services, Lock)
├─ .env                                # variáveis locais (gitignored)
├─ README.md                           # este arquivo
└─ requirements.txt
```

---

## 🚀 Quickstart

### 1) Requisitos

* **Python 3.11+**
* **LinkedIn Developer Account** e um **App** criado

### 2) Setup do ambiente

```bash
python -m venv venv
. venv/bin/activate      # (Linux/macOS)
venv\Scripts\activate    # (Windows)

pip install -r requirements.txt
```

### 3) Configure o `.env`

```env
LI_CLIENT_ID=SEU_CLIENT_ID
LI_CLIENT_SECRET=SEU_CLIENT_SECRET
LI_REDIRECT_URI=http://localhost:8000/auth/callback
LI_SCOPES=openid profile email w_member_social offline_access
LINKEDIN_VERSION=202509
# opcional
TOKENS_PATH=.tokens.json
```

> **Importante**
>
> * **`offline_access`** é necessário para receber **`refresh_token`** (senão você perde a sessão ao expirar).
> * `LINKEDIN_VERSION` segue **YYYYMM** (mantenha atualizado para a versão vigente).

### 4) Suba o servidor

```bash
uvicorn app.main:app --reload --app-dir src
```

* Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 5) Faça login com LinkedIn

1. Acesse `GET /auth/login` → será redirecionado ao LinkedIn para consentimento.
2. Ao voltar em `/auth/callback?code=...&state=...`, a API troca o code por tokens, extrai o `sub` do `id_token` e guarda o `person_urn`.
3. Verifique `GET /auth/status`:

   ```json
   {
     "logged_in": true,
     "has_refresh": true,
     "expires_in_s": 3500,
     "author": "urn:li:person:xxxxxxxx"
   }
   ```

---

## 🔐 OAuth 2.0 + OIDC (resumo)

* **/auth/login**: gera `state` seguro (`secrets.token_urlsafe(32)`), guarda com **TTL** e redireciona para a autorização do LinkedIn.
* **/auth/callback**: valida `error`, valida/consome `state`, troca `code` por `access_token` / `refresh_token` / `id_token` (lê `sub`), persiste bundle.
* **Refresh**: antes de chamadas protegidas, a API executa `ensure_token_fresh()`/`refresh_if_needed()` — se estiver perto de expirar e houver `refresh_token`, renova.
* **Lock**: `threading.Lock` evita **refresh concorrente** no mesmo processo (*double‑check + critical section*).

---

## 📤 Endpoints principais

### Health

* `GET /health`
* `GET /health/env-check` → confere variáveis de ambiente úteis (sem vazar segredos).

### Autenticação

* `GET /auth/login` → redireciona ao LinkedIn com `state`.
* `GET /auth/callback?code=...&state=...` → troca o **code** por tokens; retorna `{ message, author }`.
* `GET /auth/status` → status de sessão (`logged_in`, `has_refresh`, `expires_in_s`, `author`).

### Posts — texto

* `POST /posts`

  * **Entrada (multipart)**

    * `text`: arquivo `.txt` (campo `UploadFile`)
  * **Comportamento**

    * A API lê `bytes` → **decodifica** para `str` (UTF‑8, `errors="replace"`), **normaliza** (strip) e aplica **limite**.
    * Publica o post via **Posts API** (`/rest/posts`).
  * **Respostas**

    * **200** com JSON da API; ou
    * **201** sem corpo → API devolve `{ status_code: 201, id: <x-restli-id|location>, note: "Created (no JSON body)." }`.

> **Limite**: o LinkedIn aceita \~**3.000 caracteres** em `commentary`. A API aplica um *soft-limit* conservador (ex.: 2950) para evitar estouro.

### Posts — **imagem**

* `POST /posts/image`

  * **Entrada (multipart)**

    * `text`: arquivo `.txt` (legenda do post)
    * `file`: `image/png` ou `image/jpeg`
    * `mime_type`: opcional (se vazio, usa `file.content_type`)
  * **Fluxo interno**

    1. **Initialize Upload**: `POST /rest/images?action=initializeUpload` com `{ "initializeUploadRequest": { "owner": "urn:li:person:..." } }` → retorna `uploadUrl` + `image URN` (ex.: `urn:li:image:...`).
    2. **Upload binário**: `PUT uploadUrl` com corpo **bytes**, headers `Authorization: Bearer` e `Content-Type` (sem `LinkedIn-Version` aqui).
    3. **Criar Post**: `POST /rest/posts` com `content.media.id = <urn:li:image:...>`.
  * **Respostas**: id como acima (`x-restli-id`/`location`) e erros bem mapeados.

---

## ⚙️ Configuração (Settings)

Variáveis principais (Pydantic Settings):

| Variável           | Obrigatória | Exemplo                                               | Observações                                          |
| ------------------ | ----------- | ----------------------------------------------------- | ---------------------------------------------------- |
| `LI_CLIENT_ID`     | ✅           | `86abc...`                                            | do app no LinkedIn Developer                         |
| `LI_CLIENT_SECRET` | ✅           | `xyz...`                                              | **não** comitar                                      |
| `LI_REDIRECT_URI`  | ✅           | `http://localhost:8000/auth/callback`                 | precisa bater **exatamente** com o app               |
| `LI_SCOPES`        | ✅           | `openid profile email w_member_social offline_access` | inclua `offline_access` para receber `refresh_token` |
| `LINKEDIN_VERSION` | ✅           | `202509`                                              | **YYYYMM**; mantenha atual                           |
| `TOKENS_PATH`      | opcional    | `.tokens.json`                                        | persistência de sessão em arquivo                    |

**Boas práticas**

* `.env` está no `.gitignore`.
* Nunca logar `client_secret`/tokens; se precisar, **mascare**.

---

## 🔒 Persistência de tokens

* **Memória** (dev) ou **Arquivo JSON** (prod simples).
* Estrutura típica:

  ```json
  {
    "access_token": "...",
    "refresh_token": "...",
    "expires_at": 1737140000.12,
    "person_urn": "urn:li:person:..."
  }
  ```
* Escrita **atômica** recomendada (tmp + replace) e `threading.Lock` no repositório de arquivo.

---

## 🧩 Pontos de extensão (roadmap)

* **/posts/ai** – gerar texto/imagem com provedor de IA (ex.: OpenAI). Para imagens, prefira `b64_json` → bytes → upload.
* **Agendamento** de posts (APScheduler): cron/ISO8601 + persistência.
* **Retry/backoff** para 429/5xx transitórios.
* **User-Agent** custom nos requests REST.
* **Logs estruturados** (JSON) e correlação (trace id).
* **Lock distribuído** (Redis) se rodar múltiplos workers/processos.

---

## 🚑 Troubleshooting

| Sintoma                                                            | Causa provável                                     | Como resolver                                                                             |
| ------------------------------------------------------------------ | -------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `openid_insufficient_scope_error` no callback                      | Faltam escopos OIDC                                | Inclua `openid profile email` e refaça o login                                            |
| `No id_token returned`                                             | Falta `openid`                                     | Ajuste escopos e consinta novamente                                                       |
| `Token expired and no refresh_token available`                     | Falta `offline_access` **ou** não salvou o refresh | Inclua `offline_access` e salve o bundle no callback                                      |
| `redirect_uri mismatch`                                            | URI divergente                                     | Garanta que é **idêntica** no app e no `.env`                                             |
| `403 Unpermitted fields [/owner, /serviceRelationships, /recipes]` | Usou **Assets API** payload na **Images API**      | Para `rest/images`, use **`initializeUploadRequest.owner`** (sem `recipes/relationships`) |
| `405` no upload                                                    | Método incorreto                                   | Use **PUT** (ou POST quando indicado pelo uploadUrl)                                      |
| `201 Created` sem corpo                                            | Comportamento esperado                             | Leia `x-restli-id` ou `location` no header                                                |
| `JSONDecodeError` ao processar erro                                | `content-type` não‑JSON                            | Se falhar `json()`, caia para `text`                                                      |
| `422` “missing code/error”                                         | Parâmetros obrigatórios errado                     | Marque `error/error_description` como **opcionais** e valide `code` manualmente           |

---

## 🤝 Contribuição

1. Abra uma issue descrevendo a melhoria/bug.
2. Crie um branch `feat/…` ou `fix/…` a partir da `main`.
3. Adicione/ajuste **testes unitários**.
4. Abra um PR com contexto, screenshots/logs **sanitizados**.

---

## 📜 Licença

MIT — use à vontade, sem garantias. Este projeto **não é oficial** do LinkedIn.

---

## 📎 Referências rápidas

* LinkedIn **Posts API** (`/rest/posts`)
* LinkedIn **Images API** (`/rest/images?action=initializeUpload`)
* OAuth 2.0 / OIDC (authorization code + `id_token` `sub` → `urn:li:person:<sub>`)

> Dúvidas ou ideias? Abra uma issue — sugestões são bem‑vindas! 💙
