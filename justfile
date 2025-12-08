set positional-arguments
set shell := ["bash", "-cue"]

# --- Project Configuration ---
root_dir := `git rev-parse --show-toplevel`
flake_dir := root_dir / "tools/nix"
output_dir := root_dir / ".output"
build_dir := output_dir / "build"
docker_compose_files := "--env-file config/.env.secret --env-file config/.env.test"

# --- Modularity ---
mod nix "./tools/just/nix.just"
mod container "./tools/just/container.just"

# --- Core Development Targets ---

# Default target: List available recipes.
default:
    @just --list --unsorted

# Enter the default Nix development shell and execute the command `"$@`.
develop *args:
    just nix::develop "default" "$@"

# Run commands over the ci development shell.
ci *args:
    just nix::develop "ci" "$@"

# Format the project files using treefmt.
format *args:
    # Ensure config files are up to date before running treefmt
    @echo "Setting up configuration files..."
    "{{root_dir}}/tools/scripts/setup-config-files.sh"
    @echo "Running treefmt..."
    nix run --accept-flake-config {{flake_dir}}#treefmt -- "$@"

# Setup the project (e.g., install dependencies, configure environment).
setup *args:
    @echo "Running project setup script..."
    @cd "{{root_dir}}" && ./tools/scripts/setup.sh "$@"

## 📦 Container Management Targets

# Start services in the background. Use the defined environment files.
up *args:
    @echo "Starting services..."
    docker compose {{docker_compose_files}} up -d {{args}}

build *args:
    docker compose {{docker_compose_files}} build --no-cache {{args}}

# View live logs for all or specific services.
logs *args:
    @echo "Tailing logs..."
    docker compose {{docker_compose_files}} logs -f {{args}}

# Stop and remove containers, networks, and volumes (for a clean slate).
down:
    @echo "Stopping and removing services..."
    docker compose {{docker_compose_files}} down -v

# Stop running services without removing them.
stop *args:
    @echo "Stopping services..."
    docker compose {{docker_compose_files}} stop {{args}}

# List containers.
ps *args:
    docker compose {{docker_compose_files}} ps {{args}}

# Restart services.
restart *args:
    @echo "Restarting services..."
    docker compose {{docker_compose_files}} restart {{args}}

# Load or reindex solr for a media_id
reindex *args:
    docker exec -it backend python cli.py {{args}}

api:
    @echo "Fetching OpenAPI spec from backend..."
    cd components/frontend && \
    pnpm dlx openapi-typescript http://localhost:8082/openapi.json -o ./src/lib/api/schema.d.ts
