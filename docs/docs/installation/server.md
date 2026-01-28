# Server Configuration (Production Deployment)

This guide covers the additional steps required to deploy the application on a production server with Nginx reverse proxy, SSL/TLS encryption, and user authentication.

!!! abstract "Quick Overview"
    This builds on the [Core Installation](core.md) by adding production features:

    - **User authentication** with role-based access control
    - **SSL/TLS encryption** for secure HTTPS access
    - **Domain configuration** with Nginx reverse proxy
    - **Production environment** setup

    **Time required:** ~20 minutes
    **Difficulty:** Intermediate to Advanced

---

## Prerequisites

Before proceeding, ensure you have:

=== "Required"

    - [x] **Completed [Core Installation](core.md)** - Base application running locally
    - [x] **Domain name** - DNS pointing to your server's IP address
    - [x] **SSL/TLS certificates** - For HTTPS (e.g., from [Let's Encrypt](https://letsencrypt.org/))
    - [x] **Apache2 utilities** - For password generation: `sudo apt-get install apache2-utils`

=== "Server Access"

    - [x] **Root or sudo privileges** - For system configuration
    - [x] **Open ports** - 80 (HTTP) and 443 (HTTPS)
    - [x] **SSH access** - To configure the server

!!! example "Example Domain"
    Throughout this guide, we use `debates.swisscustodian.ch` as the example. Replace it with your actual domain.

---

## Step 1: Configure User Authentication

The application uses HTTP Basic Authentication with two roles for access control.

### Understanding User Roles

| Role | Access Level | Credentials File |
|------|--------------|------------------|
| **Editor** | Full access including content editing (`/edit` routes) | `editor.htpasswd` |
| **Reader** | Read-only access to public content | `reader.htpasswd` |

!!! info "Role Details"
    For complete information about permissions and use cases, see the [Roles documentation](../userguide/roles.md).

### Create Password Files

Generate password files for both user roles:

```bash title="Create authentication files"
# Create editor credentials
sudo htpasswd -c /etc/apache2/editor.htpasswd editor

# Create reader credentials
sudo htpasswd -c /etc/apache2/reader.htpasswd reader

# Create combined file for general authentication
sudo bash -c 'cat /etc/apache2/editor.htpasswd /etc/apache2/reader.htpasswd > /etc/apache2/combined.htpasswd'
```

!!! warning "Strong Passwords Required"
    You'll be prompted to enter passwords. Choose strong, unique passwords for production security.

### Verify Password Files

Confirm all three files were created:

```bash
ls -l /etc/apache2/*.htpasswd
```

Expected output:
```plaintext
-rw-r--r-- 1 root root ... /etc/apache2/combined.htpasswd
-rw-r--r-- 1 root root ... /etc/apache2/editor.htpasswd
-rw-r--r-- 1 root root ... /etc/apache2/reader.htpasswd
```

---

## Step 2: Obtain SSL/TLS Certificates

Secure your deployment with SSL/TLS certificates for HTTPS.

=== "Let's Encrypt (Recommended)"

    Free, automated SSL certificates with auto-renewal:

    ```bash
    # Install Certbot
    sudo apt-get update
    sudo apt-get install certbot

    # Obtain certificate
    sudo certbot certonly --standalone -d debates.swisscustodian.ch
    ```

    Your certificates will be saved to:
    ```plaintext
    Certificate: /etc/letsencrypt/live/debates.swisscustodian.ch/fullchain.pem
    Private Key: /etc/letsencrypt/live/debates.swisscustodian.ch/privkey.pem
    ```

=== "Custom Certificate"

    If using your own certificate provider:

    1. Obtain your certificate and private key files
    2. Place them in a secure location (e.g., `/etc/ssl/certs/`)
    3. Set appropriate permissions:

    ```bash
    sudo chmod 644 /path/to/certificate.cert
    sudo chmod 600 /path/to/private.key
    ```

!!! tip "Certificate Paths"
    Note the full paths to your certificate files—you'll need them for Nginx configuration.

---

## Step 3: Configure Environment Variables

Update application configuration to use your production domain.

### Update Root Environment

Edit `.env` in the project root directory:

```ini title=".env" hl_lines="1"
OPENAPI_URL=https://debates.swisscustodian.ch/openapi.json
CONTAINER_MGR=docker
```

### Update Docker Compose Environment

Edit `deploy/compose/.env` with the highlighted values:

```ini title="deploy/compose/.env" hl_lines="8 14 20 26"
# -----------------------------------------------
# Adapt this section for server deployment:
# -----------------------------------------------

# Compose Profiles:
# For server deployment: add the "prod" profile:
# Example:
COMPOSE_PROFILES=prod

# Frontend Origin:
# For server deployment: ORIGIN should be the domain url:
# Example:
# ORIGIN=https://debates.swisscustodian.ch
ORIGIN=https://debates.swisscustodian.ch

# Backend Cors Origins:
# For server deployment: replace http://localhost:3000 with your domain url
# Example:
# CORS_ORIGINS='["https://debates.swisscustodian.ch", "http://localhost:5173", "http://127.0.0.1:3000"]'
CORS_ORIGINS='["https://debates.swisscustodian.ch", "http://localhost:5173", "http://127.0.0.1:3000"]'

# S3 Urls that are clickable from the frontend:
# For server deployment: S3 public URL should be the domain url:
# Example:
# S3_PUBLIC_URL=https://debates.swisscustodian.ch
S3_PUBLIC_URL=https://debates.swisscustodian.ch
```

!!! info "Configuration Details"
    - **COMPOSE_PROFILES=prod** - Activates the Nginx reverse proxy container
    - **ORIGIN** - Frontend's public URL (required for CSRF protection)
    - **CORS_ORIGINS** - Allowed origins for API requests (keep localhost for development)
    - **S3_PUBLIC_URL** - Public URL for accessing uploaded files and media

---

## Step 4: Configure Nginx Reverse Proxy

Update the Nginx configuration to route traffic and enforce authentication.

### Locate Configuration File

The Nginx configuration is located at:
```plaintext
components/nginx/nginx.conf
```

### Update Server Settings

Edit `components/nginx/nginx.conf` and update the highlighted lines with your domain and certificate paths:

```nginx title="components/nginx/nginx.conf" hl_lines="8 16 17"
server {
    listen 80;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name debates.swisscustodian.ch;

    client_max_body_size 2G;

    auth_basic "Restricted area";
    auth_basic_user_file /run/secrets/htpasswd_combined;

    # Path to certs
    ssl_certificate /etc/nginx/ssl/debates.swisscustodian.ch.cert;
    ssl_certificate_key /run/secrets/ssl_private_key;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers on;

    # HSTS (HTTP Strict Transport Security)
    add_header Strict-Transport-Security "max-age=63072000" always;

    # Solr admin interface
    location /solr {
        proxy_pass http://solr:8983;
    }

    # Dozzle log viewer with WebSocket support
    location /logs {
        proxy_pass http://dozzle:8080;

        # Enable Websockets (Critical for Dozzle)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Standard headers
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Disable buffering for live streaming
        proxy_buffering off;
    }

    # Documentation
    location /sdsc-ordes {
        proxy_pass http://docs:8000/sdsc-ordes;
    }

    # API documentation
    location /api-docs {
        proxy_pass http://backend:8000/docs;
    }

    # OpenAPI specification
    location /openapi.json {
        proxy_pass http://backend:8000/openapi.json;
    }

    # S3 storage (public access, no authentication)
    location /debates {
        auth_basic off;
        proxy_pass http://garage:3900;
        proxy_set_header Host garage:3900;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_force_ranges on;
    }

    # Editor-only routes (enhanced authentication)
    location /edit {
        auth_basic "Editor area";
        auth_basic_user_file /run/secrets/htpasswd_editor;
        proxy_pass http://frontend:3000;
    }

    # Default route (requires authentication)
    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Key Configuration Values

Make sure you've updated:

1. **Line 8:** `server_name` → Your actual domain name
2. **Line 16:** `ssl_certificate` → Path to your SSL certificate
3. **Line 17:** `ssl_certificate_key` → Path to your private key

??? info "Understanding the Configuration"

    **Authentication Zones:**

    | Route | Auth Required | Access Level |
    |-------|---------------|--------------|
    | `/` (default) | Yes (combined) | All authenticated users |
    | `/edit` | Yes (editor only) | Editors only |
    | `/debates` | No | Public (S3 storage) |
    | `/api-docs`, `/logs`, `/solr` | Yes (combined) | All authenticated users |

    **Security Features:**

    - **HTTP to HTTPS redirect:** All HTTP traffic automatically upgrades to HTTPS
    - **TLS 1.2/1.3 only:** Enforces modern, secure protocols
    - **HSTS enabled:** Browsers will always use HTTPS (2-year policy)
    - **Strong cipher suites:** ECDHE and ChaCha20-Poly1305 preferred

---

## Step 5: Launch Production Stack

Deploy the application with production configuration.

### Start All Services

From the project root directory, execute:

```bash
just up --profiles prod --force-recreate
```

!!! info "Command Explanation"
    - `--profiles prod` - Activates the production profile (starts Nginx container)
    - `--force-recreate` - Rebuilds containers with updated configuration

### Monitor Deployment

Watch the logs to ensure all services start correctly:

```bash
just compose logs -f
```

Press `Ctrl+C` to exit log viewing once all services are running.

---

## Step 6: Verify Deployment

Test your production deployment to ensure everything works.

### Check Service Status

Verify all containers are running:

```bash
just compose ps
```

You should see these containers:
```plaintext
backend        ✓
docs           ✓
dozzle         ✓
frontend       ✓
garage         ✓
mongo-db       ✓
mongo-express. ✓
solr           ✓
redis          ✓
reverse-proxy  ✓
workers        ✓
```

### Test HTTPS Redirect

Verify HTTP automatically redirects to HTTPS:

```bash
curl -I http://debates.swisscustodian.ch
```

Expected response:
```plaintext hl_lines="1 2"
HTTP/1.1 301 Moved Permanently
Location: https://debates.swisscustodian.ch/
```

### Test Authentication

```bash
# Without credentials (should fail)
curl -I https://debates.swisscustodian.ch

# With reader credentials (should succeed)
curl -u reader:YOUR_PASSWORD https://debates.swisscustodian.ch

# Editor access to /edit route
curl -u editor:YOUR_PASSWORD https://debates.swisscustodian.ch/edit
```

### Browser Verification

Open your browser and test these URLs:

| URL | Expected Result |
|-----|-----------------|
| `http://debates.swisscustodian.ch` | Redirects to HTTPS, prompts for login |
| `https://debates.swisscustodian.ch` | Login prompt, then shows frontend |
| `https://debates.swisscustodian.ch/api-docs` | API documentation (after login) |
| `https://debates.swisscustodian.ch/edit` | Requires editor credentials |
| `https://debates.swisscustodian.ch/logs` | Shows container logs (after login) |

!!! success "Deployment Complete!"
    Your application is now running in production with SSL/TLS and authentication! 🎉

    Access your application at: **https://debates.swisscustodian.ch**

---

## Maintenance

### Certificate Renewal (Let's Encrypt)

Set up automatic certificate renewal:

```bash
# Test renewal process
sudo certbot renew --dry-run

# Enable automatic renewal (runs twice daily)
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

After certificate renewal, restart Nginx:

```bash
just compose restart nginx
```

### Update User Passwords

To change a user password:

```bash
# Update the password
sudo htpasswd /etc/apache2/editor.htpasswd editor

# Recreate combined file
sudo bash -c 'cat /etc/apache2/editor.htpasswd /etc/apache2/reader.htpasswd > /etc/apache2/combined.htpasswd'

# Restart Nginx to apply changes
just compose restart nginx
```

### View Application Logs

```bash
# All services
just compose logs -f

# Specific service
just compose logs reverse-proxy
just compose logs frontend
just compose logs backend
```

---

## Next Steps

=== "Monitoring & Maintenance"

    - Set up log rotation and archival
    - Configure backup strategy for databases
    - Monitor certificate expiration dates
    - Review application logs regularly

=== "Advanced Configuration"

    - Configure custom domain redirects
    - Set up additional authentication methods
    - Implement rate limiting
    - Configure caching strategies

=== "Scaling"

    - Add load balancing for multiple instances
    - Configure database replication
    - Implement CDN for static assets
    - Set up horizontal scaling

---

## Additional Resources

- [Core Installation Guide](core.md) - Initial setup steps
- [User Roles Documentation](../userguide/roles.md) - Role permissions and management
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/) - SSL certificate help
- [Nginx Configuration Guide](https://nginx.org/en/docs/) - Advanced proxy settings
- [Docker Compose Profiles](https://docs.docker.com/compose/profiles/) - Profile management

---

## Getting Help

!!! question "Need assistance?"

    - **Issues:** [GitHub Issues](https://github.com/sdsc-ordes/debates-analytics/issues)
    - **Documentation:** This site you're reading!
