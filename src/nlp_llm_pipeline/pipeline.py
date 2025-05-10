import sys
import os
import datetime
from .embedding import FinancialEmbeddings
from .retrieval import DocumentRetriever
from .metric_extractor import MetricExtractor
from .sentiment_analyzer import SentimentAnalyzer
from .risk_identifier import RiskIdentifier
from .summary_generator import SummaryGenerator
from langchain.llms import OpenAI

# Add project root to path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.config import LLM_CONFIG
from src.monitoring_feedback import logger

class NLPLlmPipeline:
    def __init__(self, llm=None):
        # Initialize LLM using config if not provided
        if llm is None:
            # Use the configuration for OpenAI
            api_key = LLM_CONFIG["api_key"]
            if not api_key:
                print("WARNING: No OpenAI API key found in configuration.")
            os.environ["OPENAI_API_KEY"] = api_key
            self.llm = OpenAI(
                temperature=LLM_CONFIG["temperature"],
                model_name=LLM_CONFIG["model"]  # Changed from model_name to model
            )
        else:
            self.llm = llm
            
        # Initialize all pipeline components
        self.embeddings_model = FinancialEmbeddings()
        self.retriever = DocumentRetriever(self.embeddings_model)
        self.metric_extractor = MetricExtractor(llm=self.llm)
        self.sentiment_analyzer = SentimentAnalyzer(llm=self.llm)
        self.risk_identifier = RiskIdentifier(llm=self.llm)
        self.summary_generator = SummaryGenerator(llm=self.llm)

    def process_document(self, document_text, document_id=None, metadata=None, queries=None):
        """
        Processes a document through the NLP & LLM pipeline.

        Args:
            document_text (str): The text content of the financial document.
            document_id (str, optional): ID of the document for tracking. Defaults to None.
            metadata (dict, optional): Document metadata like company, date, etc. Defaults to None.
            queries (list, optional): A list of specific questions or metrics to extract. Defaults to None.

        Returns:
            dict: A dictionary containing the extracted insights.
        """
        if not document_text:
            return {"error": "Empty document text provided."}
            
        if metadata is None:
            metadata = {}
            
        # Default queries if none provided - common financial metrics
        if queries is None:
            queries = ["Total Revenue", "Net Income", "EPS", "Operating Margin", "Debt to Equity Ratio"]

        # Record start time for performance monitoring
        start_time = datetime.datetime.now()
        print(f"Starting document processing at {start_time}")
        
        # Initialize results dictionary
        insights = {
            "document_id": document_id,
            "company": metadata.get("company", "Unknown"),
            "processing_time": None,
            "model_version": LLM_CONFIG["model"],  # Changed from model_name to model
            "timestamp": datetime.datetime.now().isoformat(),
        }

        # 1. Create retrieval index from document (or document segments)
        print("Embedding document segments...")
        
        # In a real implementation, we should segment the document here
        # For now, we'll treat the entire document as a single segment
        document_segments = [document_text]
        
        # Create index for retrieval
        self.retriever.create_index(document_segments)
        print("Document embedded and indexed for retrieval.")

        # 2. Extract requested metrics
        insights["extracted_metrics"] = {}
        for query in queries:
            print(f"Extracting metric: {query}")
            # Retrieve relevant context for the query
            query_context = self.retriever.retrieve_context(query)
            
            # If no context returned, use the full document
            if not query_context:
                query_context = [document_text]
                
            # Extract the metric from the context
            context_text = " ".join(query_context)
            insights["extracted_metrics"][query] = self.metric_extractor.extract_metric(context_text, query)

        # 3. Analyze sentiment
        print("Analyzing document sentiment...")
        insights["sentiment"] = self.sentiment_analyzer.analyze_sentiment(document_text)

        # 4. Identify risks
        print("Identifying potential risks...")
        insights["risks"] = self.risk_identifier.identify_risks(document_text)

        # 5. Generate summary
        print("Generating document summary...")
        insights["summary"] = self.summary_generator.generate_summary(document_text)

        # 6. Add source references
        source_reference = {
            "document_id": document_id,
            "company": metadata.get("company", "Unknown"),
            "document_date": metadata.get("filing_date", "Unknown"),
            "document_type": metadata.get("doc_type", "Unknown"),
        }
        insights["source_reference"] = source_reference

        # Record end time and calculate processing duration
        end_time = datetime.datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        insights["processing_time"] = processing_time
        
        print(f"Document processing completed in {processing_time:.2f} seconds.")
        
        # Log the prediction if document_id is provided
        if document_id:
            logger.log_prediction(document_id, insights)
            
        return insights

    def process_document_segments(self, segments, document_id=None, metadata=None, queries=None):
        """
        Processes document segments through the NLP & LLM pipeline.
        
        Args:
            segments (list): A list of document segment dictionaries with 'text' and 'section_type'.
            document_id (str, optional): ID of the document for tracking. Defaults to None.
            metadata (dict, optional): Document metadata like company, date, etc. Defaults to None.
            queries (list, optional): A list of specific questions or metrics to extract. Defaults to None.
            
        Returns:
            dict: A dictionary containing the extracted insights.
        """
        if not segments:
            return {"error": "No document segments provided."}
            
        if metadata is None:
            metadata = {}
            
        # Extract text from segments
        segment_texts = [segment["text"] for segment in segments]
        
        # Combine all segments for analysis that requires the full document
        full_document = "\n\n".join(segment_texts)
        
        # Create retrieval index from segments
        print(f"Embedding {len(segments)} document segments...")
        self.retriever.create_index(segment_texts)
        
        # Process using the full document and retriever
        return self.process_document(
            document_text=full_document,
            document_id=document_id,
            metadata=metadata,
            queries=queries
        )

if __name__ == '__main__':
    # Example Usage
    # This requires setting up the OpenAI API key or using a different LLM
    if LLM_CONFIG["api_key"]:
        pipeline = NLPLlmPipeline()
        dummy_document = "Sample financial report text. Revenue was $100M. Net income was $20M. Risks include market volatility."
        analysis_queries = ["Total Revenue", "Net Income"]
        document_insights = pipeline.process_document(dummy_document, queries=analysis_queries)
        import json
        print(json.dumps(document_insights, indent=4))
    else:
        print("Example usage for NLPLlmPipeline needs API key in configuration.")