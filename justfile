set positional-arguments
set shell := ["bash", "-cue"]
set dotenv-load := true
root_dir := `git rev-parse --show-toplevel`
flake_dir := root_dir / "tools/nix"
output_dir := root_dir / ".output"
build_dir := output_dir / "build"
docs_dir := root_dir / "components/docs"
backend_dir := root_dir / "components/backend"
export CONTAINER_MGR := env("CONTAINER_MGR", "docker")
export OPENAPI_URL := env("OPENAPI_URL", "")

# Nix functionality.
mod nix "./tools/just/nix.just"
# Container functionality.
mod container "./tools/just/container.just"

# Default target: List available recipes.
default:
    @echo "CONTAINER_MGR=${CONTAINER_MGR}"
    @echo "OPENAPI_URL=${OPENAPI_URL}"
    @just --list --unsorted

# Enter the default Nix development shell and execute the command `"$@`.
[group('general')]
develop *args:
    just nix::develop "default" "$@"

# Run commands over the ci development shell.
[group('general')]
ci *args:
    just nix::develop "ci" "$@"

# Format the project files using treefmt.
[group('general')]
format *args:
    # Ensure config files are up to date before running treefmt
    @echo "Setting up configuration files..."
    "{{root_dir}}/tools/scripts/setup-config-files.sh"
    @echo "Running treefmt..."
    nix run --accept-flake-config "{{flake_dir}}#treefmt" -- "$@"


# Setup the project (e.g., install dependencies, configure environment).
[group('general')]
setup *args:
    @echo "Running project setup script..."
    @cd "{{root_dir}}" && ./tools/scripts/setup.sh "$@"


# Start services in the background. Use the defined environment files.
[group('deploy')]
up *args:
    @echo "Starting services..."
    just compose up -d "$@"

# Build the compose setup.
[group('deploy')]
build *args:
    @echo "Build compose file..."
    just compose build "$@"

# Run the compose command.
[group('deploy')]
[no-cd]
compose *args:
    cd deploy/compose && \
    just container::mgr compose \
        --env-file .env --env-file .env.secret "$@"

# Update the API client (OpenAPI) in frontend.
[group('tools')]
api:
    @echo "Fetching OpenAPI spec from backend..."
    cd components/frontend && \
    pnpm dlx openapi-typescript {{OPENAPI_URL}} -o ./src/lib/api/schema.d.ts
    @echo "Copying OpenAPI spec for docs..."
    @curl -s {{OPENAPI_URL}} -o components/docs/docs/api/openapi.json \
        && echo "✅ OpenAPI spec copied to docs." \
        || echo "⚠️ Warning: Fetch failed"
    just format components/frontend/src/lib/api/schema.d.ts components/docs/docs/api/openapi.json \
    && echo "✅ API client and code formatted updated."

# Load or reindex solr for a media_id
[group('tools')]
reindex *args:
    just container::mgr exec -it backend python cli.py {{args}}

# Bulk upload a local folder to S3/Mongo
# Usage: just upload ./my-videos
[group('tools')]
upload host_path:
    @echo "📦 Preparing to upload from: {{host_path}}"

    # 1. Create a temp directory inside the container
    {{CONTAINER_MGR}} exec backend mkdir -p /tmp/bulk_import

    # 2. Copy local files to the container
    #    Note: We append '/.' to copy contents, not the folder itself
    {{CONTAINER_MGR}} cp "{{host_path}}/." backend:/tmp/bulk_import/

    # 3. Run the Python CLI command
    @echo "🚀 Starting Import Process..."
    {{CONTAINER_MGR}} exec backend python cli.py upload-folder /tmp/bulk_import

    # 4. Cleanup
    @echo "🧹 Cleaning up temp files..."
    {{CONTAINER_MGR}} exec backend rm -rf /tmp/bulk_import

# Build the documentation site (Strict mode for CI)
[group('docs')]
build-docs:
    @echo "Building documentation..."
    # Ensure dependencies are synced
    cd {{docs_dir}} && uv sync
    cd {{docs_dir}} && uv run mkdocs build --strict

# Serve the docs locally with live reload
[group('docs')]
serve-docs:
    @echo "📖 Starting MkDocs..."
    # We watch both 'docs' and 'backend' so changes trigger reloads
    cd {{docs_dir}} && uv run mkdocs serve
