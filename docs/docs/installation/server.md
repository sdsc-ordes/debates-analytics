# Server Configuration (Production)

This guide upgrades your installation to a secure, production-ready environment using Nginx, SSL, and Authentication.

!!! abstract "Server Upgrade for Public Access"
    * **Goal:** Secure the application for public access.
    * **Security:** SSL/TLS (HTTPS) + Basic Auth
    * **Access:** Domain-based routing (Reverse Proxy)
    * **Time:** ~20 minutes

## 1. Prerequisites

* [x] **Core Installation:** Complete Step 1 first.
* [x] **Domain Name:** DNS pointing to your server IP.
* [x] **SSL Certs:** A valid certificate (e.g., Let's Encrypt).
* [x] **Tools:** `apache2-utils` (for password generation).

## 2. Setup Authentication (HTPasswd)

We use basic auth to secure the site. Generate two users: `editor` (full access) and `reader` (read-only).

```bash title="setup users"
# 1. Create Users
sudo htpasswd -c /etc/apache2/editor.htpasswd editor
sudo htpasswd -c /etc/apache2/reader.htpasswd reader

# 2. Merge for "General Access" (Nginx needs a single file for common areas)
sudo bash -c 'cat /etc/apache2/editor.htpasswd /etc/apache2/reader.htpasswd > /etc/apache2/combined.htpasswd'
```

## 3. Configure Environment

Switch the application to **Production Mode** and define your server paths.

### 3.2 Configure the environment

Copy the production template to your config folder:

```bash title="copy from template"
cp config/.env.prod.tmpl config/.env
```

This activates the prod profile in docker compose for your just file commands:

```ini title="config/.env"
# 🟢 Activate the docker compose profile prod
COMPOSE_PROFILES=prod
```

**Action:** Open `config/.env` and update the following values.

1. **Domain Settings:** Replace `debates.swisscustodian.ch` with your actual domain.
2. **System Paths:** Define where your Certs and Auth files live.

```ini title="config/.env"
# --- Domain Config ---
OPENAPI_URL=https://your-domain.com/openapi.json
S3_PUBLIC_URL=https://your-domain.com
CORS_ORIGINS='["https://your-domain.com", ...]'
ORIGIN=https://your-domain.com

# Where did you create the htpasswd files?
AUTH_DIR=/etc/apache2

# Where do your "Live" certs live?
SSL_DIR=/etc/letsencrypt/live/your-domain.com
```

## 4. Configure Nginx Proxy

### 4.1 Update Config File

Open `components/nginx/nginx.conf`. You must update the **Server Name**.

```nginx title="components/nginx/nginx.conf"
server {
    listen 443 ssl;

    # 🔴 1. CHANGE THIS to your domain
    server_name your-domain.com;

    # ... rest of config ...
}
```

## 5. Launch & Verify

!!! tip
    So `just compose`, `just build` and `just up` will now all run with the docker compose flag `--profiles=prod`.
    Therefore rather use `just` instead of `compose`

Since we changed the profile to `prod`, Docker will now spin up the **Reverse Proxy**.

```bash title="Launch services"
# 1. Build the new proxy image
just build reverse-proxy

# 2. Restart stack (picks up new profile & env vars)
just up --force-recreate
```

### Verification Checklist

* **HTTPS Redirect:** `http://your-domain.com` -> `https://your-domain.com`
* **Login Prompt:** Visiting the site asks for a password.
* **Reader Access:** Log in as `reader`. Accessing `/`.
* **Editor Access:** Log in as `editor`. Access `/edit`.

Once running, access your services:

| Service | URL | Note |
| --- | --- | --- |
| **Frontend** | `https://your-domain.com/` | Main UI |
| **API Docs** | `https://your-domain.com/api-docs` | Backend Swagger |
| **Logs** | `https://your-domain.com/logs` | Container Logs (Protected) |
| **Solr UI** | `http://your-domain.com/solr` | Solr UI |

!!! success "Ready for Public Access"
    Your site is live! secure, authenticated, and running on HTTPS.
