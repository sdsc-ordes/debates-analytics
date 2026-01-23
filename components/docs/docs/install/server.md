# Server setup

The setup on a server is similar to the compose setup. The only difference is
the nginx server that is handeling the authentication.

## 1. Clone repository

```bash
git clone git@github.com:sdsc-ordes/debates-analytics.git
```

## 2. Setup the environment

### 2a set env variables for the build process

Such as `docker` and compose `profile` `prod`:

```bash
# env variables for the build process
cp .env.prod.tmpl .env
cp components/frontend/.env.tmpl .env
```

### 2b set env variables for compose and prepare secrets

```bash
cd deploy/compose/
```

```bash
cd debates-analytics/deploy/compose
# secrets
cp .env.secrets.prod.tmpl .env.secrets
# other env variables
cp .env.prod.tmpl .env
```

Generate garage secret key and mongo passwords

```bash
openssl rand -hex 32
openssl rand -hex 4
openssl rand -hex 4
```

Add those generated secrets in the `deploy/compose/.env.secrets`:

```md
# S3

# get once garage service is up

S3_ACCESS_KEY=

# generate with openssl rand -hex 32

S3_SECRET_KEY=

# Mongo

MONGO_USER=admin

# generate with openssl rand -hex 4

MONGO_PASSWORD= MONGO_EXPRESS_USER=admin

# genrate with openssl rand -hex 4

MONGO_EXPRESS_PASSWORD=

# Huggin Face: get from hugging face account

HF_TOKEN=

# Nginx Settings (all files local to host)

# FIXME: Describe in documentation.

SSL_CERTIFICATE=.secrets/ssl/cert.pem
SSL_CERTIFICATE_KEY=.secrets/ssl/private-key.pem

HTPASSWD_COMBINED=.secrets/nginx/combined.htpasswd
HTPASSWD_EDITOR=.secrets/nginx/editor.htpasswd
HTPASSWD_READER=.secrets/nginx/reader.htpasswd
```

Add Symlinks for Nginx Settings:

```
ln -s [TARGET_FILE] [LINK_NAME]

ln -s /run/secrets/htpasswd_editor .secrets/nginx/editor.htpasswd
```

ln -s [TARGET_FILE] [LINK_NAME]

## 3. Build garage service to generate key pair

```
# move back to the project root
cd ../../
```

First build the garage service:

```bash
just up garage

 ✔ Network debates_debates_network Created                                                                                                                  0.2s
 ✔ Volume "debates_garage"          Created                                                                                                                  0.0s
 ✔ Container garage                 Started
```

Then generate the key pair:

```bash
just compose exec garage garage key create app-key
cd deploy/compose && just container::mgr compose --env-file .env --env-file .env.secret "$@"
2026-01-23T16:37:35.562363Z  INFO garage_net::netapp: Connected to 127.0.0.1:3901, negotiating handshake...
2026-01-23T16:37:35.604699Z  INFO garage_net::netapp: Connection established to dbb44ec10ef95e7a
==== ACCESS KEY INFORMATION ====
Key ID:              [some-key]
Key name:            app-key
Secret key:          [some-secret]
Created:             2026-01-23 16:37:35.605 +00:00
Validity:            valid
Expiration:          never

Can create buckets:  false

==== BUCKETS FOR THIS KEY ====
Permissions  ID  Global aliases  Local aliases
```

Now open again: `.env.secret`

```
# get once garage service is up
S3_ACCESS_KEY=[some-key]
# generate with openssl rand -hex 32
S3_SECRET_KEY=[some-secret]
```

## 4. Restart Garage Service

```
just compose restart garage
```

## 5. Build the Application

```
just build --profile prod
```

Once the images have been build:

```
just up --profile prod
```
