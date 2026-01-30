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

Should you change the metadata structure (adding fields for speaker or debate) the following components need to be adapted:

1. **Backend:** models and service
2. **Solr:** the managed schema file (add field types)
3. **Frontend:** components and the mediaplayer page

!!! tip "Reference"
    Grep for an existing field like `country` for speakers or debate_type for debate to see exactly which files require updates

### Solr (Search Index)

If you change the solr schema you need to do the following:
- delete the solr volume with `docker volume rm debates_solr`
- rebuild the solr image with `just up --build solr`
- after that you need to reindex all media, which can be done either via the [commandline](#commandline.md) or on the [dashboard page](../userguide/dashboard.md)

!!! warning
    Don't reset mongodb as all media is registered there.

### API changes

In case of API changes the openapi spec needs to get regenrated for the docs and for the frontend:

```bash title="regenrate api spec in docs and api client for frontend
just api
```

## 5. Documentation

The documentation is built with MkDocs.

```bash
just serve-docs   # serve at http://localhost:8001
just build-docs   # build static site
```

The documentation is automatically deployed to github pages via a github action.

## Code formatting

Run `just format` to format the code after changes: the ci is set to run that command as github action and will complain about format errors.
