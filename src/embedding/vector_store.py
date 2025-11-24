import faiss
import numpy as np
import pickle
import logging
import os
from typing import List, Dict, Any

# Apply compatibility patch before importing sentence-transformers
try:
    import torch
    import torch.utils._pytree as pytree
    if not hasattr(pytree, 'register_pytree_node') and hasattr(pytree, '_register_pytree_node'):
        pytree.register_pytree_node = pytree._register_pytree_node
except:
    pass

class VectorStore:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.embedding_model_name = config['embedding']['model_name']
        self.vector_store_path = config['embedding']['vector_store_path']
        
        self.embedder = None
        self.index = None
        self.documents = []
        
    def _load_embedder(self):
        """Load embedding model with error handling"""
        if self.embedder is not None:
            return self.embedder
            
        try:
            # Try multiple approaches to load the embedder
            self.embedder = self._try_load_sentence_transformers()
            return self.embedder
        except Exception as e:
            self.logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def _try_load_sentence_transformers(self):
        """Try to load sentence-transformers with compatibility fixes"""
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(self.embedding_model_name)
            self.logger.info(f"✅ Loaded sentence-transformers: {self.embedding_model_name}")
            return model
        except AttributeError as e:
            if "register_pytree_node" in str(e):
                # Apply specific patch for this error
                self._apply_pytree_patch()
                from sentence_transformers import SentenceTransformer
                model = SentenceTransformer(self.embedding_model_name)
                self.logger.info(f"✅ Loaded sentence-transformers with patch: {self.embedding_model_name}")
                return model
            else:
                raise
        except Exception as e:
            self.logger.warning(f"First attempt failed: {e}")
            # Try with a different model
            try:
                from sentence_transformers import SentenceTransformer
                model = SentenceTransformer('all-MiniLM-L6-v2')  # Fallback model
                self.logger.info(f"✅ Loaded fallback model: all-MiniLM-L6-v2")
                return model
            except Exception as e2:
                self.logger.error(f"Fallback also failed: {e2}")
                raise
    
    def _apply_pytree_patch(self):
        """Apply specific patch for PyTorch pytree issue"""
        try:
            import torch.utils._pytree as pytree
            import types
            
            if not hasattr(pytree, 'register_pytree_node'):
                # Create a wrapper that uses the internal method
                def register_pytree_node(typ, serializer, deserializer):
                    return pytree._register_pytree_node(typ, serializer, deserializer)
                
                pytree.register_pytree_node = register_pytree_node
                self.logger.info("✅ Applied pytree compatibility patch")
        except Exception as e:
            self.logger.warning(f"Could not apply pytree patch: {e}")
    
    def build_index(self, documents: List[Dict[str, Any]]):
        """Build FAISS index from documents"""
        self.logger.info("🔨 Building FAISS index...")
        
        if not documents:
            self.logger.error("❌ No documents provided for indexing")
            return False
        
        try:
            self.documents = documents
            texts = [doc['content'] for doc in documents]
            
            # Load embedder
            embedder = self._load_embedder()
            
            # Generate embeddings
            self.logger.info("📊 Generating embeddings...")
            embeddings = embedder.encode(texts, show_progress_bar=True)
            
            # Create FAISS index
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)
            
            # Normalize for cosine similarity
            faiss.normalize_L2(embeddings)
            self.index.add(embeddings.astype(np.float32))
            
            self.logger.info(f"✅ FAISS index built with {len(documents)} documents")
            
            # Save the index
            self._save_index()
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error building index: {e}")
            return False
    
    def search(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        if self.index is None or len(self.documents) == 0:
            self.logger.error("❌ Index not built or no documents available")
            return []
        
        try:
            # Load embedder
            embedder = self._load_embedder()
            
            # Generate query embedding
            query_embedding = embedder.encode([query])
            
            # Normalize for cosine similarity
            faiss.normalize_L2(query_embedding)
            
            # Search
            scores, indices = self.index.search(query_embedding.astype(np.float32), k)
            
            # Prepare results
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.documents):
                    results.append({
                        'document': self.documents[idx],
                        'score': float(score)
                    })
            
            self.logger.info(f"🔍 Found {len(results)} documents for query: '{query}'")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Error searching index: {e}")
            return []
    
    def _save_index(self):
        """Save FAISS index and documents"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.vector_store_path), exist_ok=True)
            
            # Save FAISS index
            faiss.write_index(self.index, self.vector_store_path)
            
            # Save documents metadata
            docs_path = self.vector_store_path.replace('.faiss', '_docs.pkl')
            with open(docs_path, 'wb') as f:
                pickle.dump(self.documents, f)
            
            self.logger.info(f"💾 Saved index to {self.vector_store_path}")
            
        except Exception as e:
            self.logger.error(f"❌ Error saving index: {e}")
    
    def load_existing(self) -> bool:
        """Load existing FAISS index"""
        try:
            if not os.path.exists(self.vector_store_path):
                self.logger.warning(f"⚠️ Index file not found: {self.vector_store_path}")
                return False
            
            # Load FAISS index
            self.index = faiss.read_index(self.vector_store_path)
            
            # Load documents
            docs_path = self.vector_store_path.replace('.faiss', '_docs.pkl')
            with open(docs_path, 'rb') as f:
                self.documents = pickle.load(f)
            
            self.logger.info(f"✅ Loaded existing index with {len(self.documents)} documents")
            return True
            
        except Exception as e:
            self.logger.warning(f"⚠️ Could not load existing index: {e}")
            return False