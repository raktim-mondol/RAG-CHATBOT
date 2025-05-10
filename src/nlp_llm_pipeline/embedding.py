import torch
from transformers import AutoModel, AutoTokenizer
import sys
import os

# Add project root to path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.config import EMBEDDING_CONFIG

class FinancialEmbeddings:
    def __init__(self, model_name=None):
        # Use model name from config if not provided
        if model_name is None:
            model_name = EMBEDDING_CONFIG["model_name"]
            
        print(f"Loading embedding model: {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model_name = model_name

    def embed_text(self, text):
        """
        Generate embeddings for a text string using the financial language model.
        
        Args:
            text (str): The text to embed
            
        Returns:
            numpy.ndarray: The embedding vector
        """
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        with torch.no_grad():
            outputs = self.model(**inputs)
        # Use the mean of the last hidden states as the embedding
        embeddings = outputs.last_hidden_state.mean(dim=1).squeeze()
        return embeddings.numpy()
    
    def embed_documents(self, documents):
        """
        Generate embeddings for a list of texts using the financial language model.
        This is required to match the LangChain Embeddings interface.
        
        Args:
            documents (List[str]): List of text strings to embed
            
        Returns:
            List[numpy.ndarray]: List of embedding vectors
        """
        return [self.embed_text(doc) for doc in documents]

if __name__ == '__main__':
    # Example usage
    embeddings_model = FinancialEmbeddings()
    text_to_embed = "The company reported a significant increase in revenue."
    embedding = embeddings_model.embed_text(text_to_embed)
    print(f"Text: {text_to_embed}")
    print(f"Embedding shape: {embedding.shape}")
    print(f"Model used: {embeddings_model.model_name}")