# Processing Architecture

The processing system is an event-driven pipeline coordinated by a Redis queue. It ensures that heavy tasks (conversion, transcription) are handled asynchronously and reliably.

!!! abstract "Overview"
    * **Control Plane:** A Redis queue orchestrates all background jobs.
    * **Identity:** Every file is assigned a unique `media_id` (UUID) which links data across S3, MongoDB, and Solr.
    * **Workflow:** Upload :material-arrow-right: Convert :material-arrow-right: Transcribe :material-arrow-right: Index.
    * **Monitoring:** The Dashboard tracks job status, history, and errors in real-time.

---

## 1. The Media ID (UUID)

The `media_id` is the backbone of the system. It acts as the primary key that ties together the disparate storage systems. This ensures that when you delete or re-index a file, the system knows exactly which assets belong together.

### Data Linkage Diagram

```mermaid
graph TD
    %% Central Node
    UUID([<b>Media ID</b><br>UUID])

    %% Systems
    Redis[<b>Redis</b><br>Job Queue]
    Mongo[<b>MongoDB</b><br>Metadata & Status]
    Solr[<b>Solr</b><br>Search Index]
    S3[<b>S3 Storage</b><br>Files & JSONs]

    %% Relationships
    UUID --- Redis
    UUID --- Mongo
    UUID --- Solr
    UUID --- S3

    %% Styling
    classDef id fill:#fff9c4,stroke:#fbc02d,stroke-width:2px;
    classDef sys fill:#e3f2fd,stroke:#1565c0,stroke-width:2px;

    class UUID id;
    class Redis,Mongo,Solr,S3 sys;
```

## 2. The Processing Pipeline

The pipeline is triggered automatically upon upload. Intermediate results are constantly saved to the S3 "Vault" to prevent data loss, while Redis handles the communication between workers.
Pipeline Flow Diagram

```mermaid
graph LR
    %% Nodes
    Upload((User<br>Upload))
    Redis{Redis<br>Queue}
    
    subgraph Workers ["Worker Pool"]
        Register[<b>Registration</b><br>Track in Mongo]
        Convert[<b>Converter</b><br>Video to Audio]
        Transcribe[<b>Transcriber</b><br>Whisper API Call]
        Indexer[<b>Indexer</b><br>Process Results]
    end

    subgraph Storage ["Persistent Storage"]
        S3[(S3 Bucket)]
    end

    subgraph AppData ["Application Indices"]
        Mongo[(MongoDB)]
        Solr[(Solr)]
    end

    %% Flow
    Upload -->|1. Trigger| Redis
    Redis -->|2. Job| Register
    Register -->|3. Save Raw| S3
    
    Register -->|4. Next| Redis
    Redis -->|5. Job| Convert
    Convert -->|6. Save Audio| S3
    
    Convert -->|7. Next| Redis
    Redis -->|8. Job| Transcribe
    Transcribe -->|9. Save JSON| S3

    %% New Indexing Steps
    Transcribe -->|10. Next| Redis
    Redis -->|11. Job| Indexer
    Indexer -->|12. Publish| Mongo
    Indexer -->|12. Publish| Solr

    %% Styling
    classDef trigger fill:#fff3e0,stroke:#e65100,stroke-width:2px;
    classDef queue fill:#fce4ec,stroke:#c2185b,stroke-width:2px;
    classDef worker fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    classDef store fill:#e3f2fd,stroke:#1565c0,stroke-width:2px;
    classDef target fill:#fff9c4,stroke:#fbc02d,stroke-width:2px;

    class Upload trigger;
    class Redis queue;
    class Register,Convert,Transcribe,Indexer worker;
    class S3 store;
    class Mongo,Solr target;
```

## 3. Monitoring & Error Handling

### Dashboard Tracking

The frontend Dashboard provides a real-time view of the processing queue.

* History: You can view the complete log of steps (e.g., "Conversion started," "Conversion finished").

* Errors: If a worker fails, the error message is captured and displayed.

!!! failure "Recovery Strategy"
    If a job fails (marked in Red), the recommended recovery is currently manual: 1. Delete the failed media entry via the Dashboard. 2. Re-upload the file to restart the pipeline from scratch.

## 4. Indexing

The system supports indexing pre-processed content. If you manually upload valid Whisper outputs to the S3 bucket, the system can ingest them. And you can start indexing via the dashboard:

File structure that is expected:

```title="expected files for a video upload"
   media_dir
    ├── source.mp4
    ├── audio.wav
    └── transcripts
        ├── subtitles-original.json
        └── subtitles-translation.json
```

```title="expected files for a audio upload"
   media_dir
    ├── source.wav
    └── transcripts
        ├── subtitles-original.json
        └── subtitles-translation.json
```

!!! Note
    Currently only the subtitle json files are used for indexing: all other files can be provided
    and will then be downloadable, but are not of operational importance