set positional-arguments
set shell := ["bash", "-cue"]
root_dir := `git rev-parse --show-toplevel`
flake_dir := root_dir / "tools/nix"
output_dir := root_dir / ".output"
build_dir := output_dir / "build"

mod nix "./tools/just/nix.just"
mod container "./tools/just/container.just"

# Default target if you do not specify a target.
default:
    just --list --unsorted

# Enter the default Nix development shell and execute the command `"$@`.
develop *args:
    just nix::develop "default" "$@"

# Format the project.
format *args:
    "{{root_dir}}/tools/scripts/setup-config-files.sh"
    nix run --accept-flake-config {{flake_dir}}#treefmt -- "$@"

# Setup the project.
setup *args:
    cd "{{root_dir}}" && ./tools/scripts/setup.sh

[parallel]
image: image-backend image-frontend image-solr

[private]
[group("image")]
image-backend:
    cd components/backend && just image

[private]
[group("image")]
image-frontend:
    cd components/frontend && just image

[private]
[group("image")]
image-solr:
    cd components/solr && just image

up *args:
    docker compose --env-file config/.env.secret --env-file config/.env.test up -d {{args}}

logs *args:
    docker compose --env-file config/.env.secret --env-file config/.env.test logs -f {{args}}

down:
    docker compose --env-file config/.env.secret --env-file config/.env.test down

stop *args:
    docker compose --env-file config/.env.secret --env-file config/.env.test stop {{args}}

ps *args:
    docker compose --env-file config/.env.secret --env-file config/.env.test ps {{args}}

# Run commands over the ci development shell.
ci *args:
    just nix::develop "ci" "$@"
