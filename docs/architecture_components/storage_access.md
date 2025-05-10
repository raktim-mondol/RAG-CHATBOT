# Storage & Access Design

## Overview

The Storage & Access component is responsible for persistently storing the extracted insights and original document metadata, and providing efficient mechanisms for retrieving and querying this information.

## Functional Requirements (from `requirements.md`)

*   Store extracted insights in PostgreSQL with metadata indexing
*   Track source reference and model versioning

## Working Procedure Steps (from `working_procedure.md`)

*   Format insights (metric, value, timestamp, company)
*   Save in SQL with references to original text and page numbers
*   Index for search and retrieval

## Detailed Design

### Database Choice (PostgreSQL)

*   PostgreSQL is chosen for its robustness, support for structured and semi-structured data (JSONB), and strong indexing capabilities.

### Database Schema Design

*   Design a relational schema to store:
    *   **Documents:** Metadata about the original ingested documents (company, date, type, source URL, filename).
    *   **Segments:** Information about the segmented sections of each document (segment type, start/end page/character index).
    *   **Insights:** The extracted information (metric name, value, associated text snippet, reference to document and segment, model version used for extraction, timestamp of extraction).
    *   **Tables/Figures (Optional):** Potentially store extracted table data or figure captions.
*   Utilize PostgreSQL's JSONB type to store the semi-structured output from the data processing step or additional metadata for insights.

### Indexing Strategy

*   Implement appropriate indexing on frequently queried fields such as company ID, document type, filing date, metric name, and potentially on the JSONB data for faster querying of insights.
*   Consider using full-text search capabilities within PostgreSQL for searching through the extracted text snippets or document content.

### Source Reference and Model Versioning

*   Ensure that each extracted insight is linked back to the specific document, segment, and even the exact text span from which it was extracted. This is crucial for explainability and debugging.
*   Store the version of the NLP/LLM model used to generate each insight. This allows for tracking changes in extraction results over time and potentially re-processing documents with newer models.

### Data Access and Querying

*   Design database queries for efficient retrieval of insights based on various criteria (e.g., all metrics for a specific company within a date range, all risk factors from a set of documents).
*   These queries will be exposed through the API layer.

### Data Security and Access Control

*   Implement role-based access control within the database to ensure only authorized users or services can access sensitive financial data.
*   Ensure data encryption at rest (database storage) and in transit (connections to the database).