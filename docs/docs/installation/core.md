# Core Installation (Docker Compose)

This guide sets up the complete stack (Frontend, Backend, Database, Storage) using Docker Compose.

!!! abstract "Two-Phase Setup Required"
    * **Goal:** Basic set up: sufficient on local, first step for a server setup
    * **Time:** ~15 minutes

## 1. Prerequisites

* **Git** & **Bash** terminal
* **Docker Engine** & the **Docker Compose V2 plugin** (the `docker compose`
  subcommand, *not* the legacy standalone `docker-compose`)
* **Just** runner, version **1.31 or newer**
  ([Installation Guide](https://github.com/casey/just#installation))

!!! warning "Check your versions first"
    Both are common install failures, so verify before you continue:

    ```bash
    just --version              # must be >= 1.31
    sudo docker compose version # must print "Docker Compose version v2..."
    ```

    * Distro packages of `just` are often older than 1.31 and cannot parse
      this repo's justfile. If `just --version` is too old, install a current
      binary and make sure it comes **first on your `PATH`**.
    * On Linux the recipes run `docker` through `sudo`, which is why the check
      above uses `sudo` too. A Compose plugin installed only under
      `~/.docker/cli-plugins/` is invisible to `sudo docker`; install it
      system-wide instead (on Debian/Ubuntu: `sudo apt install docker-compose-v2`).

## 2. Setup Flow

!!! tip "Two-Phase Setup Required"
    **Why?** You must start the storage service (Garage) *first* to generate the Access Keys needed by the application.

### Step 1: Initialize Configuration

Clone the repo and create the required environment files.

```bash
git clone git@github.com:sdsc-ordes/debates-analytics.git
cd debates-analytics

# 1. Config for the docker compose
cp config/.env.core.tmpl config/.env

# 2. Config for Application Secrets
cp config/.env.secret.tmpl config/.env.secret

```

**Action:** Open `config/.env.secret` and fill in the following (leave S3 blank for now):

1. **Mongo Passwords:** Generate random strings (e.g., `openssl rand -hex 4`).
2. **Hugging Face Token:** Your API token for model access.

### Step 2: Bootstrap Storage (Generate Keys)

Start the storage service to generate your S3 credentials.

1. **Start Garage:**
```bash
just up garage

```

*(Wait for `Container garage Started`)*

2. **Generate Credentials:**
```bash
just compose exec garage garage key create app-key
```

3. **Copy the Output:**
Note the `Key ID` and `Secret key` from the terminal output.

### Step 3: Finalize & Launch

1. **Update Secrets:** Open `config/.env.secret` again and paste your keys:
```ini
S3_ACCESS_KEY=GK8a...       # Your Key ID
S3_SECRET_KEY=1234...       # Your Secret Key
```

2. **Build and Run:**
```bash
just build                # Build images (takes a few mins)
just up --force-recreate  # Recreate every service with the new keys
```

!!! warning "Use `--force-recreate`, not `restart`"
    A container keeps the environment it was **created** with.
    `just compose restart` stops and starts the same container, so the keys
    you just pasted are ignored. Garage, the backend and the workers all
    read `S3_ACCESS_KEY` / `S3_SECRET_KEY`, so all of them must be
    recreated — which is what `--force-recreate` does.

## Verification

Once running, access your services:

| Service | URL | Note |
| --- | --- | --- |
| **Frontend** | `http://localhost:3000` | Main UI |
| **API Docs** | `http://localhost:8082/docs` | Backend Swagger |
| **Logs** | `http://localhost:8080/logs` | Container Logs |
| **Mongo UI** | `http://localhost:8081` | Use credentials from `.env` |
| **Solr UI** | `http://localhost:8983` | Use credentials from `.env.secret` |

!!! success "Next Steps"
    * **Local Use:** Go to the [User Guide](../userguide/roles.md).
    * **Public Access:** Continue to [Server Configuration](../installation/server.md).

## Troubleshooting

??? failure "`unknown flag: --env-file`"
    Your Docker has no `compose` subcommand, so it read `--env-file` as one of
    its own flags. Install the Compose V2 plugin **system-wide**:

    ```bash
    sudo apt install docker-compose-v2
    sudo docker compose version   # must work *with* sudo
    ```

    **The trap:** on Linux these recipes run `docker` as root. If Compose sits
    only in your own `~/.docker/cli-plugins/`, then `docker compose` works for
    you but not for `just` — `sudo` looks in root's home directory, not yours.
    You get this exact error even though Compose "is installed", so always
    check with `sudo`.

??? failure "`AccessDenied ... Forbidden: No such key:` in the backend log"
    The backend is talking to Garage with empty or unknown S3 credentials,
    usually because its container was created *before* you pasted the keys
    into `config/.env.secret`. Restarting does not help — recreate:

    ```bash
    just up --force-recreate
    ```

    Media items that already failed keep their error message in MongoDB and
    stay visible on the dashboard. They are history, not a live failure.

??? failure "The upload fails in the browser, but the backend log looks fine"
    An upload happens in three steps:

    1. the browser asks the backend for an upload URL
       (`POST /ingest/get-presigned-post`),
    2. **the browser sends the file straight to Garage on port 3900**,
    3. the browser tells the backend the file arrived (`POST /ingest/process`).

    Step 2 never touches the backend. So if the backend log shows step 1
    succeeding and step 3 never happening, the file transfer itself failed
    and the backend log cannot tell you why. Check Garage instead:

    ```bash
    # Did Garage configure browser (CORS) access at startup?
    just compose logs garage | tail -30
    # Expect: 🐍 Python: CORS configured successfully.

    # Does Garage allow the browser's origin?
    curl -i -X OPTIONS http://localhost:3900/debates/ \
      -H "Origin: http://localhost:3000" \
      -H "Access-Control-Request-Method: POST"
    # Expect: HTTP/1.1 200 and an access-control-allow-origin header
    ```

    Also confirm the browser can reach port 3900 at the same host name you
    use for the UI. The address handed to the browser is `S3_PUBLIC_URL` in
    `config/.env`; if you reach the UI through an SSH tunnel, port 3900 has
    to be forwarded too.

??? failure "`error: Unknown attribute 'group'`"
    Your `just` is older than 1.31. If you already installed a newer one, make
    sure it comes first on your `PATH`: `which -a just` should point at the new
    binary and `just --version` must report 1.31 or newer. Calling a new `just`
    by its full path is not enough on old versions of this repo, because the
    recipes call `just` again internally.
