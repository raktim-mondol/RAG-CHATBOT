import sys
import os
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Add project root to path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.config import LLM_CONFIG

class SummaryGenerator:
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

        # Define prompt template for summary generation
        self.prompt_template = PromptTemplate(
            input_variables=["context"],
            template="Provide a concise summary of the key financial information from the following text:\nText: {context}\nSummary:"
        )

        self.chain = LLMChain(llm=self.llm, prompt=self.prompt_template)

    def generate_summary(self, context):
        """
        Generates a concise summary of the given financial text.

        Args:
            context (str): The text context from the financial document.

        Returns:
            str: The generated summary.
        """
        try:
            response = self.chain.run(context=context)
            return response.strip()
        except Exception as e:
            print(f"Error during summary generation: {e}")
            return "Error during generation"

if __name__ == '__main__':
    # Example Usage with configuration
    if LLM_CONFIG["api_key"]:
        generator = SummaryGenerator()
        dummy_context = "The company announced its Q4 results. Revenue was up 15% year-over-year, reaching $1.5 billion. Net income increased by 20% to $400 million. The growth was primarily driven by strong sales in the European market."
        summary = generator.generate_summary(dummy_context)
        print(f"Context: {dummy_context}")
        print(f"Summary: {summary}")
    else:
        print("OpenAI API key not configured. Set the OPENAI_API_KEY environment variable.")