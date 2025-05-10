import sys
import os
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Add project root to path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.config import LLM_CONFIG

class RiskIdentifier:
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

        # Define prompt template for risk identification
        self.prompt_template = PromptTemplate(
            input_variables=["context"],
            template="Identify and list potential risks mentioned in the following financial document excerpts. If no risks are mentioned, state 'No risks identified'.\nText: {context}\nIdentified Risks:"
        )

        self.chain = LLMChain(llm=self.llm, prompt=self.prompt_template)

    def identify_risks(self, context):
        """
        Identifies potential risks from the given financial text.

        Args:
            context (str): The text context from the financial document.

        Returns:
            str: A list of identified risks or "No risks identified".
        """
        try:
            response = self.chain.run(context=context)
            return response.strip()
        except Exception as e:
            print(f"Error during risk identification: {e}")
            return "Error during identification"

if __name__ == '__main__':
    # Example Usage with configuration
    if LLM_CONFIG["api_key"]:
        identifier = RiskIdentifier()
        dummy_context = "The company faces risks related to currency fluctuations and increased competition."
        risks = identifier.identify_risks(dummy_context)
        print(f"Context: {dummy_context}")
        print(f"Identified Risks: {risks}")
    else:
        print("OpenAI API key not configured. Set the OPENAI_API_KEY environment variable.")