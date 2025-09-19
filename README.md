# LinkedIn Poster API (Clean Architecture)

A **FastAPI** service to **authenticate with LinkedIn (OAuth 2.0 + OIDC)** and **publish posts** (text and **image**) to a member’s feed — built with **Clean Architecture**, **SOLID**, **Pydantic Settings**, automatic token **refresh**, and unit tests with **unittest**.

> **Why**: a practical project to learn and demonstrate **backend API design**, OAuth/OIDC, **LinkedIn Posts API** integration, and engineering best practices (organization, testing, security, DX).

---

## ✨ Features

* **OAuth 2.0 + OIDC** with `state` (CSRF) validation and `offline_access` support.
* **Automatic refresh** of `access_token` (refresh token grant) with a **lock** to avoid race conditions.
* **Text posts** (`commentary`) with length validation and normalization.
* **Image posts** via **Images API** (`/rest/images?action=initializeUpload`) + **Posts API** (`/rest/posts`).
* **Session persistence** (in‑memory or JSON file) — restart the server without losing login.
* **Configuration** via env/.env with Pydantic validation.
* **Observability**: health checks, auth status, sanitized error details.
* **Clean Architecture**: *domain* → *application* → *infrastructure* → *presentation*.
* **Unit tests** with `unittest`; test tree mirrors `src/`.

---

## 🧱 Stack & Design Choices

* **FastAPI** (HTTP) + **Uvicorn** (ASGI).
* **httpx** (HTTP client: timeouts, clear exceptions).
* **pydantic / pydantic-settings** (validated models & configuration).
* **python-jose** (read `id_token` — *no signature verification in MVP*).
* **Clean Architecture** separation and **SOLID** principles.

---

## 📁 Project Structure

```
linkedin-posts/
├─ src/
│  └─ app/
│     ├─ main.py                      # app composition (FastAPI)
│     ├─ config/
│     │  └─ settings.py               # Pydantic Settings + defaults
│     ├─ domain/
│     │  ├─ models/
│     │  │  ├─ post.py                # Text Post – validations (bytes→str, limits)
│     │  │  ├─ image_post.py          # Image Post (bytes + mime)
│     │  │  └─ token.py               # Token bundle (access/refresh/exp/urn)
│     │  └─ repositories/
│     │     └─ token_repository.py    # contract (Protocol/ABC)
│     ├─ application/
│     │  └─ services/
│     │     ├─ auth_service.py        # OAuth/OIDC flow and status
│     │     ├─ post_service.py        # orchestrates text/image posts
│     │     └─ health_service.py      # health/env-check
│     ├─ infra/
│     │  ├─ client/
│     │  │  └─ linkedin_client.py     # LinkedIn calls (authorize, token, refresh, posts, images)
│     │  └─ persistence/
│     │     ├─ token_repository_file.py   # file persistence
│     │     └─ token_repository_memory.py # in-memory persistence
│     └─ presentation/
│        ├─ routes/
│        │  ├─ auth.py                 # /auth/login, /auth/callback, /auth/status
│        │  ├─ post.py                 # /posts (text) & /posts/image (multipart)
│        │  └─ health.py               # /health, /health/env-check
│        └─ deps.py                    # providers (Settings, Client, Services, Lock)
├─ .env                                # local env (gitignored)
├─ README.md                           # this file
└─ requirements.txt
```

---

## 🚀 Quickstart

### 1) Requirements

* **Python 3.11+**
* **LinkedIn Developer** account and an **App** created

### 2) Setup

```bash
python -m venv venv
. venv/bin/activate      # Linux/macOS
venv\Scripts\activate    # Windows

pip install -r requirements.txt
```

### 3) Configure `.env`

```env
LI_CLIENT_ID=YOUR_CLIENT_ID
LI_CLIENT_SECRET=YOUR_CLIENT_SECRET
LI_REDIRECT_URI=http://localhost:8000/auth/callback
LI_SCOPES=openid profile email w_member_social offline_access
LINKEDIN_VERSION=202509
# optional
TOKENS_PATH=.tokens.json
```

> **Important**
>
> * Include **`offline_access`** to receive a **`refresh_token`**; otherwise the session is lost when the access token expires.
> * `LINKEDIN_VERSION` follows **YYYYMM**; keep it current.

### 4) Run

```bash
uvicorn app.main:app --reload --app-dir src
```

* Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 5) Login with LinkedIn

1. Call `GET /auth/login` → you’ll be redirected to LinkedIn to consent.
2. On return to `/auth/callback?code=...&state=...`, the API exchanges the code for tokens, reads `sub` from `id_token`, and stores `person_urn`.
3. Check `GET /auth/status`:

   ```json
   {
     "logged_in": true,
     "has_refresh": true,
     "expires_in_s": 3500,
     "author": "urn:li:person:xxxxxxxx"
   }
   ```

---

## 🔐 OAuth 2.0 + OIDC (summary)

* **/auth/login**: generates a secure `state` (`secrets.token_urlsafe(32)`), stores it with **TTL**, and redirects to LinkedIn.
* **/auth/callback**: validates `error`, validates/consumes `state`, exchanges `code` for `access_token` / `refresh_token` / `id_token` (reads `sub`), and persists the bundle.
* **Refresh**: before protected calls, `ensure_token_fresh()`/`refresh_if_needed()` renews the token if close to expiration and a `refresh_token` is present.
* **Lock**: a `threading.Lock` prevents **concurrent refreshes** in the same process (*double‑check then critical section*).

---

## 📤 Core Endpoints

### Health

* `GET /health`
* `GET /health/env-check` → confirms important envs (never logs secrets).

### Auth

* `GET /auth/login` → redirect to LinkedIn with `state`.
* `GET /auth/callback?code=...&state=...` → exchanges code for tokens; returns `{ message, author }`.
* `GET /auth/status` → session info (`logged_in`, `has_refresh`, `expires_in_s`, `author`).

### Posts — text

* `POST /posts`

  * **Input (multipart)**

    * `text`: `.txt` file (UploadFile)
  * **Behavior**

    * API reads bytes → **decodes** to `str` (UTF‑8, `errors="replace"`), **normalizes** (strip) and enforces **length limit**.
    * Publishes via **Posts API** (`/rest/posts`).
  * **Responses**

    * **200** with JSON; or
    * **201** without body → API returns `{ status_code: 201, id: <x-restli-id|location>, note: "Created (no JSON body)." }`.

> **Limit**: LinkedIn accepts \~**3,000 characters** in `commentary`. The API uses a conservative soft‑limit (e.g., 2,950) to avoid edge cases with emojis/ZWJ.

### Posts — **image**

* `POST /posts/image`

  * **Input (multipart)**

    * `text`: `.txt` file (caption)
    * `file`: `image/png` or `image/jpeg`
    * `mime_type`: optional (falls back to `file.content_type`)
  * **Flow**

    1. **Initialize Upload**: `POST /rest/images?action=initializeUpload` with `{ "initializeUploadRequest": { "owner": "urn:li:person:..." } }` → returns `uploadUrl` + `image URN` (e.g., `urn:li:image:...`).
    2. **Binary upload**: `PUT uploadUrl` with raw bytes, headers `Authorization: Bearer` and `Content-Type` (no `LinkedIn-Version` on the upload host).
    3. **Create Post**: `POST /rest/posts` with `content.media.id = <urn:li:image:...>`.
  * **Responses**: same id behavior (`x-restli-id`/`location`) and clear error mapping.

---

## ⚙️ Configuration (Settings)

Key variables (Pydantic Settings):

| Variable           | Required | Example                                               | Notes                                        |
| ------------------ | -------- | ----------------------------------------------------- | -------------------------------------------- |
| `LI_CLIENT_ID`     | ✅        | `86abc...`                                            | LinkedIn Developer app                       |
| `LI_CLIENT_SECRET` | ✅        | `xyz...`                                              | **do not** commit                            |
| `LI_REDIRECT_URI`  | ✅        | `http://localhost:8000/auth/callback`                 | must **exactly** match the app               |
| `LI_SCOPES`        | ✅        | `openid profile email w_member_social offline_access` | include `offline_access` for `refresh_token` |
| `LINKEDIN_VERSION` | ✅        | `202509`                                              | **YYYYMM**; keep current                     |
| `TOKENS_PATH`      | optional | `.tokens.json`                                        | session persistence on disk                  |

**Best practices**

* `.env` is git‑ignored.
* Never log tokens/secrets; if necessary, **mask** them.

---

## 🔒 Token Persistence

* **In‑memory** (dev) or **JSON file** (simple prod).
* Typical structure:

  ```json
  {
    "access_token": "...",
    "refresh_token": "...",
    "expires_at": 1737140000.12,
    "person_urn": "urn:li:person:..."
  }
  ```
* Recommended: **atomic writes** (temp + replace) and a `threading.Lock` inside the file repository.

---

## 🧩 Extensions (roadmap)

* **/posts/ai** – generate text/image with an AI provider (e.g., OpenAI). For images, prefer `b64_json` → bytes → upload.
* **Scheduling** (APScheduler): cron/ISO8601 + persistence.
* **Retry/backoff** for transient 429/5xx.
* **Custom User‑Agent** on REST calls.
* **Structured logs** (JSON) with correlation/trace ids.
* **Distributed lock** (Redis) if running multiple workers.

---

## 🚑 Troubleshooting

| Symptom                                                            | Likely cause                              | Fix                                                                                   |
| ------------------------------------------------------------------ | ----------------------------------------- | ------------------------------------------------------------------------------------- |
| `openid_insufficient_scope_error` at callback                      | Missing OIDC scopes                       | Include `openid profile email` and re‑consent                                         |
| `No id_token returned`                                             | Missing `openid`                          | Add scope and re‑consent                                                              |
| `Token expired and no refresh_token available`                     | Missing `offline_access` or not persisted | Add `offline_access` and save bundle on callback                                      |
| `redirect_uri mismatch`                                            | URI mismatch                              | Ensure exact match in LinkedIn app and `.env`                                         |
| `403 Unpermitted fields [/owner, /serviceRelationships, /recipes]` | Assets payload used on Images API         | For `rest/images`, use **`initializeUploadRequest.owner`** (no recipes/relationships) |
| `405` on upload                                                    | Wrong method                              | Use **PUT** (or POST if indicated by uploadUrl)                                       |
| `201` without body                                                 | Expected behavior                         | Read `x-restli-id` or `location` header                                               |
| `JSONDecodeError` when handling errors                             | Non‑JSON `content-type`                   | Try `json()`, fall back to `text`                                                     |
| `422` missing code/error                                           | Required query params                     | Mark `error/error_description` optional and validate `code` manually                  |

---

## 🤝 Contributing

1. Open an issue describing the enhancement/bug.
2. Create a branch `feat/...` or `fix/...` from `main`.
3. Add/adjust **unit tests**.
4. Open a PR with context and sanitized screenshots/logs.

---

## 📜 License

MIT — use freely, no warranties. This project is **not** affiliated with LinkedIn.

---

## 📎 Quick References

* LinkedIn **Posts API** (`/rest/posts`)
* LinkedIn **Images API** (`/rest/images?action=initializeUpload`)
* OAuth 2.0 / OIDC (authorization code + `id_token` `sub` → `urn:li:person:<sub>`)

> Questions or ideas? Open an issue — contributions are welcome! 💙
