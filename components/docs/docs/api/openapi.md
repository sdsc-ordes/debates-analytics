# API Documentation

The API provides a machine readable interface to the application: all functionality is provided by the backend and can be triggered via the API by the frontend.


```mermaid
graph LR
    %% --- Nodes ---

    subgraph Client ["Client Side"]
        Frontend[Frontend Application<br>User Interface]
    end

    subgraph Server ["Server Side"]
        direction TB
        API[API<br>Machine Readable Interface]
        Backend[Backend<br>Core Functionality]
    end

    %% --- Relationships ---

    %% The Request Flow
    Frontend -->|1. Trigger via API| API
    API -->|2. Execute Logic| Backend

    %% The Response Flow
    Backend -.->|3. Return Result| API
    API -.->|4. JSON Response| Frontend

    %% --- Styling ---
    classDef client fill:#e3f2fd,stroke:#1565c0,stroke-width:2px;
    classDef interface fill:#fff9c4,stroke:#fbc02d,stroke-width:2px,stroke-dasharray: 5 5;
    classDef backend fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;

    class Frontend client;
    class API interface;
    class Backend backend;
```

## Structure

The API routes are structured into groups:

- **Ingestion**: Upload media files and start the processing
- **Admin**: Administer the uploaded media: allows to reindex and delete a media item together with its derived results
- **Metadata**: Display and update metadata on the speakers and debate, correct the AI derived transcriptions and translations
- **Search**: Fulltext search in speaker statements

## API Spec

<swagger-ui src="./openapi.json"/>
