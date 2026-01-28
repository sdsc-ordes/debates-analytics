# Data Storage Architecture

!!! abstract "Overview"
    * **Architecture:** A dual-layer system that separates long-term storage from application performance.
    * **Primary Store (The Vault):** S3/Garage stores the raw media and expensive AI results (permanent).
    * **Secondary Store (The Index):** MongoDB and Solr store metadata and search indices (fast & flexible).
    * **Strategy:** Ensures costly data is safe while allowing the application index to be rebuilt ("re-indexed") at any time.

## Architecture

The system uses a **Dual-Layer** storage strategy to balance data safety with application performance.

## Primary Storage (The "Vault")
* **Technology:** S3-compatible Object Store (via [Garage](https://garagehq.deuxfleurs.fr/))
* **Purpose:** Long-term preservation of costly data.
* **Content:** Raw media files (`.mp4`, `.wav`) and the expensive AI outputs (WhisperX JSONs, SRTs).
* **Philosophy:** This layer is treated as the "Single Source of Truth." Since generating transcripts takes significant GPU time and money, this data is stored permanently and safely here.

## Secondary Storage (The "Index")
* **Technology:** [MongoDB](https://www.mongodb.com/) & [Apache Solr](https://solr.apache.org/)
* **Purpose:** Fast access and flexibility for the User Interface.
* **Content:**
    * **MongoDB:** Tracks processing status, user edits, and metadata corrections.
    * **Solr:** Provides sub-second full-text search across millions of speaker statements.
* **Philosophy:** This layer is "derived." It can be wiped and rebuilt (re-indexed) at any time using the data from the Primary Storage. This allows you to change your database schema or search logic without ever losing the original AI transcriptions.

---

## Data Flow Diagram

This diagram illustrates how the costly data is safely isolated, while the secondary storage acts as a flexible cache for the application.

```mermaid
graph TD
    subgraph Layer1 ["Layer 1: Primary Storage (Permanent & Costly)"]
        S3[<b>Garage S3</b><br>Raw Media + AI Results]
    end

    subgraph Layer2 ["Layer 2: Secondary Storage (Fast & Flexible)"]
        Mongo[<b>MongoDB</b><br>Metadata & User Edits]
        Solr[<b>Solr</b><br>Search Index]
    end

    subgraph App ["User Interface"]
        UI[Dashboard & Player]
    end

    %% --- Relationships ---

    %% The Re-index Flow
    S3 ==>|Re-Index / Sync| Mongo
    S3 ==>|Re-Index / Sync| Solr

    %% App Usage
    Mongo <-->|Reads/Writes Metadata| UI
    Solr -.->|Search Queries| UI

    %% Streaming
    S3 -.->|Streams Video| UI

    %% --- Styling ---
    classDef primary fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    classDef secondary fill:#fff3e0,stroke:#e65100,stroke-width:2px,stroke-dasharray: 5 5;
    classDef app fill:#e3f2fd,stroke:#1565c0,stroke-width:2px;

    class S3 primary;
    class Mongo,Solr secondary;
    class UI app;
```

## Strategy

!!! tip "Production Advice: Choose Stable S3"
    In a production environment, the **Primary Storage** is your most critical asset. If you lose this data, you lose the expensive compute results.

    * **Recommendation:** Replace the local Garage container with a managed S3 service (e.g., AWS S3, MinIO Cluster) or ensure your hosting volume has rigorous daily backups.
    * **Contrast:** The **Secondary Storage** (MongoDB/Solr) is less critical. It can be treated as "part of the app"—if it fails, you can simply spin up empty databases and re-index everything from your safe Primary Storage.
