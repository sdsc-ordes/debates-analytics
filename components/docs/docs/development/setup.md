# Development Guide

This guide covers the development workflow for working on the application codebase.

!!! abstract "Overview"
    The application currently uses a **simplified development approach** without hot-reloading or dedicated dev containers. Development happens by rebuilding services as needed and using the same Docker Compose setup as deployment.

    **Key Points:**

    - Development uses the same Docker Compose stack as deployment
    - Changes require rebuilding containers (`just up --build`)
    - Documentation can be built and served locally
    - Nix provides a consistent development environment (recommended)
    - No automated tests currently exist (contributions welcome!)

---

## Development Environment Setup

### Recommended: Using Nix

Nix provides a reproducible development environment with all required tools pre-installed.

#### Install Nix and direnv

=== "Linux/macOS"

    ```bash
    # Install Nix (multi-user installation)
    sh <(curl -L https://nixos.org/nix/install) --daemon

    # Install direnv
    # On macOS with Homebrew:
    brew install direnv

    # On Linux:
    sudo apt-get install direnv  # Debian/Ubuntu
    # or
    sudo dnf install direnv      # Fedora
    ```

=== "Configuration"

    Add direnv to your shell:

    ```bash
    # For Bash (~/.bashrc)
    eval "$(direnv hook bash)"

    # For Zsh (~/.zshrc)
    eval "$(direnv hook zsh)"

    # For Fish (~/.config/fish/config.fish)
    direnv hook fish | source
    ```
See also:

- [nix installation](https://nixos.org/download/)
- [direnv installation](https://direnv.net/docs/installation.html)

#### Enable Nix Environment

Navigate to the project directory and allow direnv:

```bash
cd debates-analytics
direnv allow
```

!!! success "Environment Ready"
    The Nix environment will automatically load when you enter the project directory, providing all necessary development tools.

### Without Nix

If not using Nix, ensure you have these tools installed manually:

#### Core Requirements

- **Docker** & **Docker Compose** - Container runtime and orchestration
- **Git** - Version control (`git rev-parse` used in Justfile)
- **Just** - Command runner for task automation
- **Bash** - Shell (version 4.0+)
- **curl** - For fetching OpenAPI specs

#### For API Client Generation

- **pnpm** - Node.js package manager (required for `just api` command)

#### For Documentation

- **Python 3.11+** - Required for MkDocs
- **uv** - Python package installer and resolver

#### Optional (for direct development)

- **Node.js 18+** - If working directly on frontend code
- **Python 3.11+** - If running backend outside containers
---

## Working with the Codebase

### Making Code Changes

When you modify application code, rebuild the affected service:

```bash
# Rebuild and restart a specific service
just up --build <service>
```

**Examples:**

```bash
# After changing backend code
just up --build backend

# After changing frontend code
just up --build frontend

# After changing Nginx configuration
just up --build nginx
```

### Updating Environment Variables

When you change environment variables in `.env` or `.env.secrets`:

```bash
# Recreate containers with new environment
just up --force-recreate
```

!!! warning "Environment Changes"
    Use `--force-recreate` instead of `--build` when only environment variables change. This avoids unnecessary image rebuilds.

---

## Keeping API Client in Sync

The frontend uses an auto-generated client based on the OpenAPI specification. After making backend API changes:

```bash
# Regenerate API client and documentation
just api
```

!!! info "Prerequisites"
    This command requires `pnpm` to be installed for Node.js package management.

**What this does:**

- Extracts the OpenAPI specification from the backend
- Regenerates the TypeScript client for the frontend
- Updates API documentation

### API-First Development

The application follows an **API-first architecture**:

- **Backend** defines the data contracts via OpenAPI/FastAPI
- **Frontend** is a thin client consuming the API
- Changes typically start with backend API modifications

---

## Documentation

### Building Documentation Locally

The documentation site (this site) is built with MkDocs Material.

```bash
# Build the documentation
just build-docs

# Serve documentation locally (with hot-reload)
just serve-docs
```

Access the documentation at: `http://localhost:8001`

!!! tip "Live Reload"
    The `serve-docs` command includes hot-reload—changes to markdown files automatically refresh the browser.

---

## Database Management

### Solr (Search Index)

#### When to Rebuild Solr

You need to reindex Solr when:

- Changing Solr schema configuration
- Modifying search-related metadata fields
- After database corruption or inconsistencies

#### Rebuilding Solr Index

**Option 1: From Dashboard**

1. Navigate to the media management interface
2. For each media item, trigger reindexing manually

**Option 2: From Command Line**

```bash
# Remove Solr volume
docker volume rm debates-analytics_solr_data

# Restart with fresh Solr instance
just up solr

# Reindex all media (run indexing script)
just compose exec backend python scripts/reindex_solr.py
```

!!! danger "Data Loss Warning"
    Removing the Solr volume deletes all search indexes. You must reindex after this operation.

### MongoDB (Database)

#### When to Rebuild MongoDB

You may need to update MongoDB when:

- Changing document schema structure
- Adding or removing metadata fields
- Database migration or schema updates

#### Handling Schema Changes

After modifying the MongoDB schema:

```bash
# If needed, remove and recreate database
docker volume rm debates-analytics_mongodb_data

# Restart MongoDB
just up mongo

# Run migration scripts if available
just compose exec backend python scripts/migrate_db.py
```

!!! warning "Schema Migrations"
    Currently, there are no automated migration scripts. Schema changes may require manual data updates or reindexing.

---

## Adding Metadata Fields

Adding new metadata fields requires coordinated changes across multiple components.

### Required Changes

When adding a new metadata field (e.g., `author`, `publication_date`):

1. **Backend (FastAPI)**
   - Update Pydantic models in `backend/app/models/`
   - Update API endpoints in `backend/app/routers/`
   - Update database schemas

2. **Frontend (SvelteKit)**
   - Update TypeScript types in `frontend/src/lib/types/`
   - Update forms and display components
   - Regenerate API client (`just api`)

3. **Solr Schema**
   - Update `solr/conf/schema.xml`
   - Add field definitions
   - Rebuild Solr index

4. **MongoDB Schema**
   - Update collection schemas if using schema validation
   - Run migration scripts if needed

### Finding Examples

!!! tip "Learn by Example"
    Search the codebase for existing fields (e.g., `title`, `description`) to see all the places that need updates:
    
    ```bash
    # Find all references to an existing field
    git grep -n "title" -- backend frontend
    ```

### Future Improvements

This process could be simplified with:

- Code generation from schema definitions
- Automated migration scripts
- Dynamic field configuration

Contributions in this area are welcome!

---

## Testing

!!! warning "Testing Status"
    Currently, **no automated tests** exist for the application. This is a known gap.

### Testing Priorities

If contributing tests, focus on these areas in order:

1. **Backend API Tests** (highest priority)
   - API endpoints and responses
   - Data validation
   - Business logic

2. **Integration Tests**
   - Database interactions
   - Search functionality
   - File upload/storage

3. **Frontend Tests** (lower priority)
   - Since the frontend is a thin client, backend testing is more critical

### Running Tests (Future)

Once tests are added, they should follow this pattern:

```bash
# Backend tests
just test-backend

# Frontend tests
just test-frontend

# All tests
just test
```

---

## Common Development Tasks

### View Logs

Monitor service logs during development:

```bash
# All services
just compose logs -f

# Specific service
just compose logs -f backend
just compose logs -f frontend

# Follow logs with grep filter
just compose logs -f backend | grep ERROR
```

### Access Service Shells

Get a shell inside a running container:

```bash
# Backend container (Python)
just compose exec backend bash

# Frontend container (Node)
just compose exec frontend sh

# MongoDB shell
just compose exec mongo mongosh
```

### Reset Development Environment

Start fresh by removing all containers and volumes:

```bash
# Stop all services
just down

# Remove volumes (WARNING: deletes all data)
docker volume prune -f

# Rebuild and start
just build
just up
```

!!! danger "Data Loss"
    Volume removal deletes all database content, uploads, and search indexes. Use with caution.

---

## Development Workflow Example

Here's a typical development workflow:

```bash
# 1. Start the development environment
cd debates-analytics
direnv allow  # If using Nix

# 2. Make your changes to the code
# Edit backend/app/routers/media.py

# 3. Rebuild the affected service
just up --build backend

# 4. If you changed the API, regenerate client
just api

# 5. Rebuild frontend if API changed
just up --build frontend

# 6. Check logs for errors
just compose logs -f backend

# 7. Test your changes in the browser
# Navigate to http://localhost:3000
```

---

## Code Style and Conventions

### Backend (Python)

- **Formatter:** Black (if configured)
- **Linter:** Ruff or Flake8 (if configured)
- **Type hints:** Use type hints throughout

### Frontend (TypeScript/Svelte)

- **Formatter:** Prettier (if configured)
- **Linter:** ESLint (if configured)
- **Style:** Follow existing component patterns

!!! info "Linting Status"
    Formal linting configurations may not be fully set up yet. Follow existing code style in the meantime.

---

## Troubleshooting Development Issues

??? question "Changes not appearing after rebuild"
    
    **Try force recreating instead of just rebuilding:**
    ```bash
    just down
    just up --force-recreate
    ```
    
    **Or remove the specific container:**
    ```bash
    docker rm -f <container-name>
    just up --build <service>
    ```

??? question "Port already in use"
    
    **Find and stop the conflicting process:**
    ```bash
    # Find process using port 3000
    lsof -i :3000
    
    # Stop the process
    kill -9 <PID>
    ```
    
    **Or change the port in docker-compose.yml**

??? question "Database connection errors after changes"
    
    **Restart dependent services in order:**
    ```bash
    just compose restart mongo
    just compose restart backend
    just compose restart frontend
    ```

??? question "Solr not finding documents after reindex"
    
    **Verify Solr core exists:**
    ```bash
    curl http://localhost:8983/solr/admin/cores?action=STATUS
    ```
    
    **Check indexing logs:**
    ```bash
    just compose logs backend | grep -i solr
    ```

---

## Contributing Guidelines

### Before Submitting Changes

1. **Test your changes** manually (automated tests coming soon!)
2. **Update documentation** if you've changed behavior or added features
3. **Regenerate API client** if you modified backend endpoints (`just api`)
4. **Check logs** for errors after your changes

### Pull Request Checklist

- [ ] Code follows existing style and conventions
- [ ] Documentation updated (if applicable)
- [ ] API client regenerated (if backend changed)
- [ ] Manually tested in local environment
- [ ] No errors in service logs
- [ ] Database migrations noted (if applicable)

---

## Getting Help

!!! question "Development Questions?"

    - **Issues:** [GitHub Issues](https://github.com/sdsc-ordes/debates-analytics/issues)
    - **Contributing:** See CONTRIBUTING.md in the repository

---

## Next Steps

- Review the [Architecture Documentation](../architecture/overview.md) to understand the system design
- Check existing [Issues](https://github.com/sdsc-ordes/debates-analytics/issues) for tasks to work on