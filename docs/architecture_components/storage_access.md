# Storage & Access Design

## Overview

The Storage & Access component is responsible for persistently storing the extracted insights and original document metadata in MongoDB, and providing efficient mechanisms for retrieving and querying this information.

## Functional Requirements (from `requirements.md`)

*   Store extracted insights in MongoDB with metadata indexing
*   Track source reference and model versioning

## Working Procedure Steps (from `working_procedure.md`)

*   Format insights (metric, value, timestamp, company)
*   Save in MongoDB collections with references to original text and page numbers
*   Index for search and retrieval

## Detailed Design

### Database Choice (MongoDB)

*   MongoDB is chosen for its flexibility with semi-structured data, scalability, and ease of use with Python (PyMongo).

### Database Schema Design (Collections)

*   Design collections to store:
    *   **Documents:** Metadata about the original ingested documents (company, date, type, source URL, filename).
    *   **Segments:** Individual text segments extracted from documents, linked to their parent document.
    *   **Insights:** Extracted information (metrics, risks, summaries) linked to documents and/or segments.
    *   **Tables/Figures (Optional):** Potentially store extracted table data or figure captions.
*   Utilize MongoDB's flexible schema to store the semi-structured output from the data processing step or additional metadata for insights.

### Indexing Strategy

*   Create indexes on frequently queried fields within MongoDB collections (e.g., `document_id`, `company`, `doc_type`, `metric_name`, `date`).
*   Ensure data encryption at rest (MongoDB Atlas offers this, or implement filesystem encryption for self-hosted) and in transit (TLS/SSL connections to MongoDB).