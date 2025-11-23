set positional-arguments
set shell := ["bash", "-cue"]

# --- Project Configuration ---
root_dir := `git rev-parse --show-toplevel`
flake_dir := root_dir / "tools/nix"
output_dir := root_dir / ".output"
build_dir := output_dir / "build"
docker_compose_files := "--env-file config/.env.secret --env-file config/.env.test" # Centralized env files

# --- Modularity ---
mod nix "./tools/just/nix.just"
mod container "./tools/just/container.just" # Assuming this has generic container targets

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

# Build all container images in parallel.
[parallel]
image: image-backend image-frontend image-solr

# Build a single backend image.
[private]
[group("image")]
image-backend:
    @echo "Building backend image..."
    cd components/backend && just image

# Build a single frontend image.
[private]
[group("image")]
image-frontend:
    @echo "Building frontend image..."
    cd components/frontend && just image

# Build a single solr image.
[private]
[group("image")]
image-solr:
    @echo "Building solr image..."
    cd components/solr && just image

# Default target if you do not specify a target.
default:
    just --list --unsorted

start:
  just container::mgr compose -d up && \
  just container::mgr compose exec solr bash ~/load-data.sh

start-dev:
  just container::mgr compose -f docker-compose-dev.yml -d up && \
  just container::mgr compose exec \
    -f docker-compose-dev.yml \
    solr bash ~/load-data.sh
