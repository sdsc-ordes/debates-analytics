set positional-arguments
set shell := ["bash", "-cue"]
set dotenv-load := true
root_dir := `git rev-parse --show-toplevel`
flake_dir := root_dir / "tools/nix"
output_dir := root_dir / ".output"
build_dir := output_dir / "build"

# Nix functionality.
mod nix "./tools/just/nix.just"
# Container functionality.
mod container "./tools/just/container.just"

# The default container manager (e.g 'podman' or 'docker').
export CONTAINER_MGR := env("CONTAINER_MGR", "docker")
# The default compose profile (production: "prod").
export COMPOSE_PROFILES := env("COMPOSE_PROFILES", "")

# Default target: List available recipes.
default:
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
    cd deploy/compose && \
        just compose up -d "$@"

# Build the compose setup.
[group('deploy')]
build *args:
    @echo "Build compose file..."
    cd deploy/compose && \
        just compose build "$@"

# Run the compose command.
[group('deploy')]
[no-cd]
compose *args:
    just container::mgr compose \
        --env-file .env --env-file .env.secret "$@"

# Update the API client (OpenAPI) in frontend.
[group('tools')]
api:
    # FIXME: must be part from build.
    @echo "Fetching OpenAPI spec from backend..."
    cd components/frontend && \
    pnpm dlx openapi-typescript http://localhost:8082/openapi.json -o ./src/lib/api/schema.d.ts

# Load or reindex solr for a media_id
[group('tools')]
reindex *args:
    just container::mgr exec -it backend python cli.py {{args}}
