import sys
import os
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Add project root to path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.config import LLM_CONFIG

class MetricExtractor:
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
                model_name=LLM_CONFIG["model"]  # Using model_name parameter with model value
            )
        else:
            self.llm = llm

        # Define prompt template for metric extraction
        self.prompt_template = PromptTemplate(
            input_variables=["context", "question"],
            template="Given the following financial document excerpts:\n{context}\n\nBased on the above, extract the following financial metric: {question}\nIf the information is not present, state 'Not found'.\nExtracted Metric:"
        )

        self.chain = LLMChain(llm=self.llm, prompt=self.prompt_template)

    def extract_metric(self, context, question):
        """
        Extracts a specific financial metric from the given context.

        Args:
            context (str): The text context from the financial document.
            question (str): The specific financial metric to extract (e.g., "Total Revenue", "Net Income").

        Returns:
            str: The extracted metric value or "Not found".
        """
        try:
            response = self.chain.run(context=context, question=question)
            return response.strip()
        except Exception as e:
            print(f"Error during metric extraction: {e}")
            return "Error during extraction"

if __name__ == '__main__':
    # Example Usage with configuration
    import os
    
    # Check if we have an API key configured
    if LLM_CONFIG["api_key"]:
        extractor = MetricExtractor()
        dummy_context = "The company's revenue for Q3 was $1.2 billion, with a net income of $300 million."
        metric_to_find = "Total Revenue"
        extracted_value = extractor.extract_metric(dummy_context, metric_to_find)
        print(f"Context: {dummy_context}")
        print(f"Metric to find: {metric_to_find}")
        print(f"Extracted Value: {extracted_value}")
    else:
        print("OpenAI API key not configured. Set the OPENAI_API_KEY environment variable.")