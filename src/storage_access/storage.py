import psycopg2
from psycopg2 import sql
import sys
import os

# Add project root to path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.config import DB_CONFIG

# Database connection details from config
DB_HOST = DB_CONFIG["host"]
DB_NAME = DB_CONFIG["database"]
DB_USER = DB_CONFIG["user"]
DB_PASSWORD = DB_CONFIG["password"]

def create_insights_table():
    """Creates the insights table in the PostgreSQL database."""
    conn = None
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS insights (
                id SERIAL PRIMARY KEY,
                metric VARCHAR(255) NOT NULL,
                value TEXT,
                timestamp TIMESTAMP NOT NULL,
                company VARCHAR(255) NOT NULL,
                source_reference TEXT,
                model_version VARCHAR(50),
                original_text TEXT,
                page_numbers INT[]
            );
        """)
        conn.commit()
        print("Insights table created successfully.")
    except (Exception, psycopg2.Error) as error:
        print(f"Error while connecting to PostgreSQL or creating table: {error}")
    finally:
        if conn:
            cur.close()
            conn.close()

def create_documents_table():
    """Creates the documents table to store metadata about ingested documents."""
    conn = None
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                company VARCHAR(255) NOT NULL,
                doc_type VARCHAR(50) NOT NULL,
                filing_date TIMESTAMP,
                source_url TEXT,
                file_path TEXT,
                processed BOOLEAN DEFAULT FALSE,
                ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        print("Documents table created successfully.")
    except (Exception, psycopg2.Error) as error:
        print(f"Error while creating documents table: {error}")
    finally:
        if conn:
            cur.close()
            conn.close()

def create_segments_table():
    """Creates the segments table to store document segments."""
    conn = None
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS segments (
                id SERIAL PRIMARY KEY,
                document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
                section_type VARCHAR(100),
                text TEXT,
                start_page INTEGER,
                end_page INTEGER,
                embedding_available BOOLEAN DEFAULT FALSE
            );
        """)
        conn.commit()
        print("Segments table created successfully.")
    except (Exception, psycopg2.Error) as error:
        print(f"Error while creating segments table: {error}")
    finally:
        if conn:
            cur.close()
            conn.close()

def save_document(document_data):
    """
    Saves document metadata into the documents table.
    Returns document_id if successful, None otherwise.
    """
    conn = None
    document_id = None
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cur = conn.cursor()
        insert_query = sql.SQL("""
            INSERT INTO documents (company, doc_type, filing_date, source_url, file_path, processed)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """)
        cur.execute(insert_query, (
            document_data.get('company'),
            document_data.get('doc_type'),
            document_data.get('filing_date'),
            document_data.get('source_url'),
            document_data.get('file_path'),
            document_data.get('processed', False)
        ))
        document_id = cur.fetchone()[0]
        conn.commit()
        print(f"Document saved successfully with ID: {document_id}")
    except (Exception, psycopg2.Error) as error:
        print(f"Error while saving document: {error}")
    finally:
        if conn:
            cur.close()
            conn.close()
    return document_id

def save_segments(segments, document_id):
    """
    Saves document segments into the segments table.
    """
    conn = None
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cur = conn.cursor()
        
        for segment in segments:
            insert_query = sql.SQL("""
                INSERT INTO segments (document_id, section_type, text, start_page, end_page)
                VALUES (%s, %s, %s, %s, %s)
            """)
            cur.execute(insert_query, (
                document_id,
                segment.get('section_type'),
                segment.get('text'),
                segment.get('start_page', 0),  # Default to page 0 if not specified
                segment.get('end_page', 0)     # Default to page 0 if not specified
            ))
        
        conn.commit()
        print(f"Saved {len(segments)} segments for document ID: {document_id}")
    except (Exception, psycopg2.Error) as error:
        print(f"Error while saving segments: {error}")
    finally:
        if conn:
            cur.close()
            conn.close()

def save_insight(insight_data):
    """
    Saves a single insight into the database.
    insight_data is expected to be a dictionary with keys:
    metric, value, timestamp, company, source_reference, model_version, original_text, page_numbers
    """
    conn = None
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cur = conn.cursor()
        insert_query = sql.SQL("""
            INSERT INTO insights (metric, value, timestamp, company, source_reference, model_version, original_text, page_numbers)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """)
        cur.execute(insert_query, (
            insight_data.get('metric'),
            insight_data.get('value'),
            insight_data.get('timestamp'),
            insight_data.get('company'),
            insight_data.get('source_reference'),
            insight_data.get('model_version'),
            insight_data.get('original_text'),
            insight_data.get('page_numbers')
        ))
        insight_id = cur.fetchone()[0]
        conn.commit()
        print(f"Insight saved successfully with ID: {insight_id}")
        return insight_id
    except (Exception, psycopg2.Error) as error:
        print(f"Error while saving insight: {error}")
        return None
    finally:
        if conn:
            cur.close()
            conn.close()

def create_indexes():
    """Creates indexes on the insights table for efficient search and retrieval."""
    conn = None
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cur = conn.cursor()
        cur.execute("CREATE INDEX IF NOT EXISTS idx_insights_metric ON insights (metric);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_insights_company ON insights (company);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_insights_timestamp ON insights (timestamp);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_insights_page_numbers ON insights USING GIN (page_numbers);")
        
        # Indexes for the documents table
        cur.execute("CREATE INDEX IF NOT EXISTS idx_documents_company ON documents (company);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_documents_doc_type ON documents (doc_type);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_documents_filing_date ON documents (filing_date);")
        
        # Indexes for segments table
        cur.execute("CREATE INDEX IF NOT EXISTS idx_segments_document_id ON segments (document_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_segments_section_type ON segments (section_type);")
        
        conn.commit()
        print("Indexes created successfully.")
    except (Exception, psycopg2.Error) as error:
        print(f"Error while creating indexes: {error}")
    finally:
        if conn:
            cur.close()
            conn.close()

def get_all_insights():
    """Retrieves all insights from the database."""
    conn = None
    insights = []
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cur = conn.cursor()
        cur.execute("SELECT id, metric, value, timestamp, company, source_reference, model_version, original_text, page_numbers FROM insights;")
        insights = cur.fetchall()
    except (Exception, psycopg2.Error) as error:
        print(f"Error while retrieving all insights: {error}")
    finally:
        if conn:
            cur.close()
            conn.close()
    return insights

def get_document_by_id(document_id):
    """Retrieves a document by ID."""
    conn = None
    document = None
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cur = conn.cursor()
        cur.execute("SELECT id, company, doc_type, filing_date, source_url, file_path, processed, ingestion_timestamp FROM documents WHERE id = %s;", (document_id,))
        result = cur.fetchone()
        if result:
            document = {
                "id": result[0],
                "company": result[1],
                "doc_type": result[2],
                "filing_date": result[3],
                "source_url": result[4],
                "file_path": result[5],
                "processed": result[6],
                "ingestion_timestamp": result[7]
            }
    except (Exception, psycopg2.Error) as error:
        print(f"Error while retrieving document by ID: {error}")
    finally:
        if conn:
            cur.close()
            conn.close()
    return document

def get_document_segments(document_id):
    """Retrieves all segments for a document."""
    conn = None
    segments = []
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cur = conn.cursor()
        cur.execute("SELECT id, section_type, text, start_page, end_page FROM segments WHERE document_id = %s ORDER BY id;", (document_id,))
        results = cur.fetchall()
        for result in results:
            segments.append({
                "id": result[0],
                "section_type": result[1],
                "text": result[2],
                "start_page": result[3],
                "end_page": result[4]
            })
    except (Exception, psycopg2.Error) as error:
        print(f"Error while retrieving document segments: {error}")
    finally:
        if conn:
            cur.close()
            conn.close()
    return segments

def query_insights(metric=None, date=None, company=None):
    """Queries insights based on metric, date, and company."""
    conn = None
    insights = []
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cur = conn.cursor()
        query = "SELECT id, metric, value, timestamp, company, source_reference, model_version, original_text, page_numbers FROM insights WHERE 1=1"
        params = []
        if metric:
            query += " AND metric = %s"
            params.append(metric)
        if date:
            query += " AND DATE(timestamp) = %s"
            params.append(date)
        if company:
            query += " AND company = %s"
            params.append(company)

        cur.execute(query, params)
        insights = cur.fetchall()
    except (Exception, psycopg2.Error) as error:
        print(f"Error while querying insights: {error}")
    finally:
        if conn:
            cur.close()
            conn.close()
    return insights

def get_insights_by_document(document_id):
    """Retrieves all insights related to a specific document."""
    conn = None
    insights = []
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cur = conn.cursor()
        # We assume that source_reference contains the document ID
        cur.execute("""
            SELECT id, metric, value, timestamp, company, source_reference, model_version, original_text, page_numbers 
            FROM insights WHERE source_reference LIKE %s;
        """, (f"%document_id={document_id}%",))
        insights = cur.fetchall()
    except (Exception, psycopg2.Error) as error:
        print(f"Error while retrieving insights by document: {error}")
    finally:
        if conn:
            cur.close()
            conn.close()
    return insights

def initialize_database():
    """Initialize the database schema by creating all necessary tables and indexes."""
    create_insights_table()
    create_documents_table()
    create_segments_table()
    create_indexes()

if __name__ == '__main__':
    initialize_database()