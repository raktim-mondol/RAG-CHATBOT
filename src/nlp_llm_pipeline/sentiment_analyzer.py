import sys
import os
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Add project root to path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.config import LLM_CONFIG

class SentimentAnalyzer:
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

        # Define prompt template for sentiment analysis
        self.prompt_template = PromptTemplate(
            input_variables=["context"],
            template="Analyze the sentiment of the following financial text and categorize it as Positive, Negative, or Neutral. Provide a brief explanation.\nText: {context}\nSentiment:"
        )

        self.chain = LLMChain(llm=self.llm, prompt=self.prompt_template)

    def analyze_sentiment(self, context):
        """
        Analyzes the sentiment of the given financial text.

        Args:
            context (str): The text context from the financial document.

        Returns:
            str: The sentiment analysis result (Positive, Negative, Neutral) and explanation.
        """
        try:
            response = self.chain.run(context=context)
            return response.strip()
        except Exception as e:
            print(f"Error during sentiment analysis: {e}")
            return "Error during analysis"

if __name__ == '__main__':
    # Example Usage with configuration
    if LLM_CONFIG["api_key"]:
        analyzer = SentimentAnalyzer()
        dummy_context = "Despite challenging market conditions, the company's performance exceeded expectations."
        sentiment_result = analyzer.analyze_sentiment(dummy_context)
        print(f"Context: {dummy_context}")
        print(f"Sentiment Analysis Result: {sentiment_result}")
    else:
        print("OpenAI API key not configured. Set the OPENAI_API_KEY environment variable.")