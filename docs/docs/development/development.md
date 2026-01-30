# Development Guide (Maintenance Mode)

!!! warning "Project Status: Frozen"
    This project is currently in a wrap-up state with no active development budget.

* **No Hot-Reload:** Development relies on rebuilding containers.
* **No Tests:** There is currently no automated test suite.
* **Workflow:** Make changes :material-arrow-right: Rebuild specific service :material-arrow-right: Verify manually.


## 1. Quick Start (Nix)

**Recommended.** Nix ensures a reproducible environment even if you pick this project up months later.

1. **Install:** [Nix](https://nixos.org/download/) and [direnv](https://direnv.net/docs/installation.html).
2. **Activate:**
```bash
cd debates-analytics
direnv allow
```

**Manual Alternative:**
If you cannot use Nix, ensure you have: **Docker**, **Git**, **Just**, **Bash**, and **Python 3.11+**.

---

## 2. Core Workflow

The project uses a simplified workflow without dedicated dev containers.

| Goal | Command |
| --- | --- |
| **Apply Code Changes** | `just up --build <service>` <br> *(e.g. `just up --build backend`)* |
| **Apply `.env` Changes** | `just up --force-recreate` |
| **Sync Frontend API** | `just api` <br> *(Run after changing Backend Pydantic models)* |
| **View Logs** | `just compose logs -f <service>` |
| **Shell Access** | `just compose exec <service> bash` |

---

## 3. Data & Search Management

Since there are no migrations, schema changes often require resetting the data.

### Solr (Search Index)

If you change `schema.xml` or search logic:

```bash
# 1. Reset Solr Volume
docker volume rm debates_solr

# 2. Restart & Reindex
just up -d solr
just compose exec backend python scripts/reindex_solr.py
```

### MongoDB

If you change the Document Structure:

```bash
# 1. Reset Mongo Volume (Deletes all data/users!)
docker volume rm debates-analytics_mongodb_data

# 2. Restart
just up -d mongo

```

---

## 4. Modification Cheatsheet

If you need to add a metadata field (e.g., `author`) in the future, you must update these 4 layers:

1. **Backend Models:** `backend/app/models/` (Pydantic schemas)
2. **Solr Schema:** `solr/conf/schema.xml` (Add `<field>` definition)
3. **Frontend Types:** `frontend/src/lib/types/` (Or run `just api` to auto-generate)
4. **UI Components:** `frontend/src/lib/components/` (To display the new data)

!!! tip "Reference"
    Grep for an existing field like `title` to see exactly which files require updates:
    `git grep -n "title" -- backend frontend`

---

## 5. Documentation

The documentation is built with MkDocs.

```bash
just serve-docs   # serve at http://localhost:8001
just build-docs   # build static site

```
