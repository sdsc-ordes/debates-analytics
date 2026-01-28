# User Guide

Welcome to the **Political Debates** platform. This guide covers how to access the system and use the core analysis tools.

## Access & Roles

The platform strictly separates administrative duties from viewing duties. Please identify your role below to find your login details.

### :material-account-cog: Editor Role

**Best for:** Administrators, Data Managers.
Editors have full control over the data lifecycle. They can upload videos, delete files, and edit transcripts.

=== "VM Installation"
    **URL:** `https://debates.swisscustodian.ch/edit`

    > **Credentials:** Log in with the `editor` account.

=== "Local Installation"
    **URL:** `http://localhost:3000/edit`

    > Log in not needed.

### :material-account-eye: Reader Role

**Best for:** Analysts, General Users.
Readers can search the database, view videos, and read transcripts, but cannot modify any data.

=== "VM Installation"
    **URL:** `https://debates.swisscustodian.ch`

    > **Credentials:** Log in with the `reader` account.

=== "Local Installation"
    **URL:** `http://localhost:3000`

    > Log in not needed.

---

## Quick Links

Once logged in, navigate to the specific tool you need:

<div class="grid cards" markdown>

-   :material-view-dashboard: **[Dashboard](dashboard.md)**
    Upload, manage, and process media files (Editor only).

-   :material-magnify: **[Search Engine](searchpage.md)**
    Find specific statements across all processed debates.

-   :material-play-circle: **[Media Player](mediaplayer.md)**
    Watch debates with synchronized transcripts and translations.

</div>
