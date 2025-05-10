---

## 8. Working Procedure

### Step 1: Ingest Financial Documents

- Schedule downloads/scraping from SEC EDGAR, investor sites
- Normalize filenames and log source metadata

### Step 2: Preprocess Documents

- Convert to raw text using PDFMiner/PyMuPDF
- Apply segmentation rules: identify headers, footnotes, tables
- Clean and tokenize content

### Step 3: NLP Processing

- Embed segments using financial-specific embeddings
- Use retriever to fetch context for queries
- Call LLM agents with templates (zero-shot/few-shot)
- Aggregate insights with source references

### Step 4: Postprocess & Store

- Format insights (metric, value, timestamp, company)
- Save in SQL with references to original text and page numbers
- Index for search and retrieval

### Step 5: Interface & API

- Provide endpoints to:
  - Upload document and fetch insights
  - Run specific analysis (e.g., extract revenue)
- Integrate into tools via UI or CLI wrapper

### Step 6: Monitoring & Evaluation

- Compare outputs against human-labeled gold data
- Trigger alerts on drift or quality drop
- Log feedback into training datasets for fine-tuning