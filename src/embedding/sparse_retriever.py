import pickle
import logging
import os
from typing import List, Dict, Any
import numpy as np
from rank_bm25 import BM25Okapi
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
except:
    pass

class SparseRetriever:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.sparse_index_path = config['embedding']['vector_store_path'].replace('.faiss', '_sparse.pkl')
        self.bm25 = None
        self.documents = []
        self.stop_words = set(stopwords.words('english'))
        
    def _preprocess_text(self, text: str) -> List[str]:
        """Preprocess text for BM25"""
        if not text:
            return []
        
        try:
            # Tokenize and lowercase
            tokens = word_tokenize(text.lower())
            
            # Remove stopwords and non-alphanumeric tokens
            tokens = [token for token in tokens 
                     if token.isalnum() and token not in self.stop_words and len(token) > 2]
            
            return tokens
        except:
            # Fallback simple tokenization
            return [word.lower() for word in text.split() 
                   if word.isalnum() and len(word) > 2]
    
    def build_index(self, documents: List[Dict[str, Any]]):
        """Build BM25 index from documents"""
        self.logger.info("Building BM25 index...")
        
        if not documents:
            self.logger.error("No documents provided for indexing")
            return False
        
        try:
            self.documents = documents
            texts = [doc['content'] for doc in documents]
            
            # Preprocess all documents
            self.logger.info("Preprocessing documents for BM25...")
            tokenized_corpus = [self._preprocess_text(text) for text in texts]
            
            # Create BM25 index
            self.bm25 = BM25Okapi(tokenized_corpus)
            
            self.logger.info(f"BM25 index built with {len(documents)} documents")
            
            # Save the index
            self._save_index()
            return True
            
        except Exception as e:
            self.logger.error(f"Error building BM25 index: {e}")
            return False
    
    def search(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """Search using BM25 similarity"""
        if self.bm25 is None or len(self.documents) == 0:
            self.logger.error("Index not built or no documents available")
            return []
        
        try:
            # Preprocess query
            query_tokens = self._preprocess_text(query)
            
            if not query_tokens:
                self.logger.warning(f"No valid tokens found in query: '{query}'")
                return []
            
            # Get BM25 scores
            scores = self.bm25.get_scores(query_tokens)
            
            # Get top k results
            top_indices = np.argsort(scores)[::-1][:k]
            
            # Prepare results
            results = []
            for idx in top_indices:
                if scores[idx] > 0:  # Only include relevant results
                    results.append({
                        'document': self.documents[idx],
                        'score': float(scores[idx])
                    })
            
            self.logger.info(f"Found {len(results)} BM25 results for query: '{query}'")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in BM25 search: {e}")
            return []
    
    def _save_index(self):
        """Save BM25 index"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.sparse_index_path), exist_ok=True)
            
            with open(self.sparse_index_path, 'wb') as f:
                pickle.dump({
                    'bm25': self.bm25,
                    'documents': self.documents
                }, f)
            
            self.logger.info(f"Saved BM25 index to {self.sparse_index_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving BM25 index: {e}")
    
    def load_existing(self) -> bool:
        """Load existing BM25 index"""
        try:
            if not os.path.exists(self.sparse_index_path):
                self.logger.warning(f"BM25 index file not found: {self.sparse_index_path}")
                return False
            
            with open(self.sparse_index_path, 'rb') as f:
                data = pickle.load(f)
            
            self.bm25 = data['bm25']
            self.documents = data['documents']
            
            self.logger.info(f"Loaded existing BM25 index with {len(self.documents)} documents")
            return True
            
        except Exception as e:
            self.logger.warning(f"Could not load existing BM25 index: {e}")
            return False