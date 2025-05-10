---

## 6. System Architecture

```mermaid
graph TD
    A[Data Sources] --> B[Ingestion Pipeline]
    B --> C[Document Preprocessing]
    C --> D[NLP Agent Framework]
    D --> E1[Metric Extractor]
    D --> E2[Risk Extractor]
    D --> E3[Summary Generator]
    D --> E4[Sentiment Analyzer]
    E1 --> F[Insight Storage (PostgreSQL)]
    E2 --> F
    E3 --> F
    E4 --> F
    F --> G[REST API (FastAPI)]
    G --> H[Frontend or Analyst Tools]
    F --> I[Monitoring Dashboard]
    I --> J[Feedback Loop]