# Debates Analytics

Transcribes, diarizes, and indexes UNHRC debate recordings so statements can be
searched by speaker/topic/date. See [README.md](README.md) and
[docs/docs/architecture/overview.md](docs/docs/architecture/overview.md) for
the full picture.

## Stack

| Service | Tech | Role |
| --- | --- | --- |
| frontend | SvelteKit | UI (search page, media player, editor) |
| backend | FastAPI | REST API |
| workers | RQ | async job processing (calls HF Whisper) |
| mongodb-instance | MongoDB | media/speaker/subtitle/segment metadata |
| solr | Apache Solr | full-text search index |
| redis | Redis | job queue backing RQ |
| garage | Garage (S3) | media file storage |
| reverse-proxy | Nginx | TLS + basic auth + routing (`prod` profile only) |
| dozzle | Dozzle | web UI for container logs |
| mongodb-express | mongo-express | Mongo admin UI |

## Compose layout

Everything lives under [deploy/compose/](deploy/compose/):

- `compose.yml` — top-level file, defines networks/volumes, `dozzle` and
  `reverse-proxy`, and `include`s the two files below.
- `compose.data.yml` — solr, mongodb-instance, mongodb-express, redis, garage.
- `compose.app.yml` — backend, workers, frontend.

Two profiles:

- **default (no profile)** — core stack only, served at `localhost:3000`, no
  auth/TLS. Used for local dev.
- **`prod`** (`COMPOSE_PROFILES=prod`) — adds `reverse-proxy`, which fronts
  everything with HTTPS + basic auth (see
  [components/nginx/nginx.conf](components/nginx/nginx.conf) for routing:
  `/` and `/edit` → frontend, `/api-docs` + `/openapi.json` → backend,
  `/solr` → solr, `/logs` → dozzle, `/debates` → garage).

Always run compose through `just`, not `docker compose` directly — it wires
up the right env files:

```bash
just up               # start stack (-d), respects $COMPOSE_PROFILES
just build [service]  # build image(s)
just compose <args>   # raw passthrough, e.g. `just compose ps`
```

## Checking what's running

```bash
just compose ps       # running containers + health
just compose ps -a    # include stopped/exited/crashed containers
just compose logs -f <service>   # e.g. reverse-proxy, backend, solr
```

If the public site is down, check in this order:

1. `just compose ps -a` — is `reverse-proxy` even present? It only starts
   under the `prod` profile (`COMPOSE_PROFILES=prod` in `config/.env`).
2. `just compose logs reverse-proxy` — the container bind-mounts
   `${SSL_DIR}/fullchain.pem` and `${SSL_DIR}/privkey.pem` from the host
   (Let's Encrypt path). A missing/expired cert here fails the container
   start or breaks TLS.
3. `just compose ps` health status for `mongodb-instance`, `solr`, `redis` —
   `backend` won't become healthy until all three are.

Dozzle (live log UI) is also reachable directly at `:8080`, or at `/logs`
behind the reverse-proxy (auth-protected).

## Config

Env vars live in `config/.env` (+ `config/.env.secret`), templated from
`config/.env.core.tmpl` / `config/.env.prod.tmpl`. **Do not read `.env` files
directly** — ask the user if you need to know a value.

## Dev environment

Nix + direnv (`.envrc`, `tools/nix/`) provide the shell; `just` is the task
runner (see `justfile`, `tools/just/*.just`).
