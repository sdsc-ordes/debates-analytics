## Architecture

The application consists of the following parts:

- **Frontend**: in svelte kit with a generated API client (generated from the
  backend)

- **Backend**: in python with a FastAPI interface: all actions happen here and
  can be started either via the frontend or per API

- **Workers**: via redis queue: to decouple the time consuming processing from
  access requests on the data and metadata a redis queue has been established to
  pipe the uploaded media files through a pipeline of workers, that convert
  videos to audio, derive the transcripts and translations via an external
  interface to an AI tool, stored on Hugging Face. After processing the data is
  stored on an S3 and then loaded into secondary data storages such as Mongo DB
  and Solr

- **Whisper**: the external Whisper component that is accessed via API to do the
  hard work of transcribing the videos is hosted on Hugging Face. A personal
  Hugging Face account and token is needed to gain access for the processing of
  the media files

```mermaid
graph TD
    subgraph Clients ["User Interaction"]
        FE[Frontend<br>SvelteKit + Generated Client]
    end

    subgraph App_Layer ["Application Core"]
        BE[Backend<br>Python FastAPI]
    end

    subgraph Async_Layer ["Asynchronous Processing: Workers"]
        Redis[Redis Queue]
        subgraph Workers1 ["Convert"]
        end
        subgraph Workers2 ["Transcribe"]
        end
        subgraph Workers3 ["Reindex"]
        end
    end

    subgraph External ["External AI Services"]
        Whisper[Whisper Model<br>Hugging Face]
    end

    subgraph Storage1 ["Primary Data Storage"]
        S3[S3 Storage<br>Media & Artifacts]
    end

    subgraph Storage2 ["Secondary Datastorage"]
        Mongo[MongoDB]
        Solr[Solr Search]
    end

    %% Define Relationships
    FE -->|API Requests| BE

    BE -->|Enqueue Jobs| Redis
    BE -->|Load Data    | S3
    BE -->|Load Data    | Storage2


    Workers1 -->|1. Convert Video to Audio| Workers2
    Workers2 -->|2. Transcription| Whisper
    Workers3 -->|3. Index Metadata | Storage2

    S3 -.->|Load Data| Mongo
    S3 -.->|Load Data| Solr

    %% Styling
    classDef primary fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef secondary fill:#f3e5f5,stroke:#4a148c,stroke-width:2px;
    classDef storage fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px;
    classDef external fill:#fff3e0,stroke:#e65100,stroke-width:2px,stroke-dasharray: 5 5;

    class FE,API_User,BE primary;
    class Redis,Worker secondary;
    class S3,Mongo,Solr,Secondary_DBs storage;
    class Whisper external;
```

- [**loading results into secondary databases**](dataloader.md): the processed
  data is loaded into structured databases to improve findability

```mermaid
flowchart LR
  S[(Object Store S3)] --load--> E{SRT Parser}
  E --metadata--> B[(Structured Metadata MongoDB)]
  E --segments--> C[(Search Engine Solr)]
```

- [**serving and enriching metadata via a WebUI**](webui.md): the Webui allows
  to search in the debates and to annotate and correct the speaker statements

```mermaid
flowchart LR
    subgraph Backend[Debates Backend]
        M{Debates API}
        C[(Search Engine Solr)]
        S[(Object Store S3)]
        B[(Structured Metadata MongoDB)]
    end
    subgraph UI[Debates GUI]
        F(GUI Searchpage)
        E(GUI Videoplayer)
    end
    M -- serve --> F
    M -- serve --> E
    C -- load --> M
    B -- load --> M
    S -- signed urls --> M
    E -- correct --> M
    style UI fill:white
    style Backend fill:white
```
