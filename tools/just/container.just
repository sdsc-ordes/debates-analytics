set positional-arguments
set shell := ["bash", "-cue"]

default:
    just --list --unsorted -f "{{source_file()}}"

# Run container manager defined in `$CONTAINER_MGR`.
[no-cd]
[group('container')]
mgr *args:
    #!/usr/bin/env bash
    set -eu

    if [ "${CONTAINER_MGR:-}" = "podman" ]; then
        podman "$@"
    elif [ "${CONTAINER_MGR:-}" = "docker" ]; then
        cmd=()

        if [ "{{os()}}" = "linux" ] ; then
            cmd+=(sudo)
        fi
        cmd+=(docker)

        "${cmd[@]}" "$@"
    fi
