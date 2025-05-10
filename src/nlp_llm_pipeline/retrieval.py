import os
import sys
import numpy as np
import faiss
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from langchain.embeddings.base import Embeddings

# Add project root to path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.config import EMBEDDING_CONFIG

class DocumentRetriever:
    def __init__(self, embeddings_model, index_path=None):
        """
        Initialize the DocumentRetriever with an embeddings model.
        
        Args:
            embeddings_model: An embedding model that implements the embed_text and embed_documents methods
            index_path (str, optional): Path to save/load the FAISS index. Defaults to config setting.
        """
        self.embeddings_model = embeddings_model
        self.index_path = index_path if index_path else EMBEDDING_CONFIG["index_path"]
        self.vectorstore = None
        
        # Create the LangChain wrapper for our embedding model if needed
        if not isinstance(embeddings_model, Embeddings):
            self.langchain_embeddings = LangchainEmbeddingsWrapper(embeddings_model)
        else:
            self.langchain_embeddings = embeddings_model

    def create_index(self, documents):
        """
        Create a FAISS index from documents.
        
        Args:
            documents: Either a list of strings or a list of LangChain Document objects
        """
        if not documents:
            print("No documents provided to create index.")
            return
            
        # Convert documents to LangChain Document objects if they're strings
        if isinstance(documents[0], str):
            docs = [Document(page_content=text) for text in documents]
        else:
            docs = documents
            
        print(f"Creating FAISS index from {len(docs)} documents...")
        try:
            # Create FAISS index
            self.vectorstore = FAISS.from_documents(docs, self.langchain_embeddings)
            print(f"FAISS index created successfully with {len(docs)} documents")
            
            # Save the index
            self.save_index()
        except Exception as e:
            print(f"Error creating FAISS index: {e}")

    def save_index(self):
        """Save the FAISS index to disk."""
        if self.vectorstore:
            try:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
                self.vectorstore.save_local(self.index_path)
                print(f"FAISS index saved to {self.index_path}")
            except Exception as e:
                print(f"Error saving FAISS index: {e}")
        else:
            print("No vectorstore to save.")

    def load_index(self):
        """Load the FAISS index from disk."""
        try:
            self.vectorstore = FAISS.load_local(self.index_path, self.langchain_embeddings)
            print(f"FAISS index loaded from {self.index_path}")
            return True
        except Exception as e:
            print(f"Could not load FAISS index: {e}")
            self.vectorstore = None
            return False

    def retrieve_context(self, query, k=5):
        """
        Retrieve the most relevant document contexts for a given query.
        
        Args:
            query (str): The query text
            k (int, optional): Number of documents to retrieve. Defaults to 5.
            
        Returns:
            list: List of document contents
        """
        if self.vectorstore is None:
            print("Vectorstore not loaded or created.")
            return []
            
        try:
            docs = self.vectorstore.similarity_search(query, k=k)
            return [doc.page_content for doc in docs]
        except Exception as e:
            print(f"Error during similarity search: {e}")
            return []
            
    def add_documents(self, documents):
        """
        Add documents to an existing FAISS index.
        
        Args:
            documents: Either a list of strings or a list of LangChain Document objects
        """
        if not documents:
            print("No documents provided to add to index.")
            return
            
        # Convert documents to LangChain Document objects if they're strings
        if isinstance(documents[0], str):
            docs = [Document(page_content=text) for text in documents]
        else:
            docs = documents
            
        if self.vectorstore is None:
            # If no index exists yet, create one
            self.create_index(docs)
            return
            
        print(f"Adding {len(docs)} documents to existing FAISS index...")
        try:
            self.vectorstore.add_documents(docs)
            print(f"Added {len(docs)} documents to FAISS index")
            
            # Save the updated index
            self.save_index()
        except Exception as e:
            print(f"Error adding documents to FAISS index: {e}")

class LangchainEmbeddingsWrapper(Embeddings):
    """
    Wrapper to make our embedding model compatible with LangChain's Embeddings interface.
    """
    def __init__(self, embeddings_model):
        self.embeddings_model = embeddings_model
        
    def embed_documents(self, texts):
        """Embed a list of texts."""
        return self.embeddings_model.embed_documents(texts)
        
    def embed_query(self, text):
        """Embed a single query text."""
        return self.embeddings_model.embed_text(text)

if __name__ == '__main__':
    # Example Usage with FinancialEmbeddings
    from embedding import FinancialEmbeddings
    
    try:
        embeddings_model = FinancialEmbeddings()
        retriever = DocumentRetriever(embeddings_model)
        
        # Example documents
        documents = [
            "The company reported a quarterly revenue of $1.2 billion.",
            "Net income fell by 15% due to increased operational costs.",
            "The board approved a dividend increase of $0.05 per share.",
            "The company faces risks from new regulations in the European market."
        ]
        
        # Create an index
        retriever.create_index(documents)
        
        # Test retrieval
        query = "revenue growth"
        results = retriever.retrieve_context(query, k=2)
        
        print(f"Query: {query}")
        print("Retrieved contexts:")
        for i, result in enumerate(results):
            print(f"{i+1}. {result}")
            
    except Exception as e:
        print(f"Error in example usage: {e}")