#!/usr/bin/env python3
"""
Real Estate AI with Hybrid RAG - Main Entry Point
"""

# Apply comprehensive compatibility patches FIRST
try:
    from huggingface_compat import apply_huggingface_patches
    apply_huggingface_patches()
except ImportError:
    # Fallback basic patches
    try:
        import torch.utils._pytree as pytree
        if not hasattr(pytree, 'register_pytree_node') and hasattr(pytree, '_register_pytree_node'):
            pytree.register_pytree_node = pytree._register_pytree_node
            print("✅ Applied basic PyTorch patch")
    except:
        pass

import argparse
import yaml
import logging
import sys
import os
from typing import Dict, Any, List

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data_processing.jsonl_processor import JSONLProcessor
from src.embedding.vector_store import VectorStore
from src.embedding.sparse_retriever import SparseRetriever
from src.hybrid_rag.router import QueryRouter
from src.hybrid_rag.fusion import HybridFusion
from src.hybrid_rag.retriever import AdaptiveRetriever
from src.hybrid_rag.generator import ResponseGenerator

class RealEstateAI:
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize the Real Estate AI system"""
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.vector_store = None
        self.sparse_retriever = None
        self.router = None
        self.fusion = None
        self.retriever = None
        self.generator = None
        self.data_processor = None
        
        self.logger.info("🚀 Real Estate AI System Initialized")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            print("✅ Configuration loaded successfully")
            return config
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            raise

    def _setup_logging(self):
        """Setup logging configuration with proper encoding"""
        logging_config = self.config.get('logging', {})
        level = logging_config.get('level', 'INFO')
        format_str = logging_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Remove emojis from format for Windows compatibility
        format_str = format_str.replace('🚀', '').replace('📊', '').replace('📄', '').replace('📝', '').replace('🔧', '').replace('🔍', '').replace('🎯', '').replace('🤖', '').replace('💬', '').replace('📋', '').replace('🏢', '').replace('📝', '').replace('📄', '').replace('💾', '').replace('✅', '').replace('❌', '').replace('⚠️', '').replace('🔨', '').replace('🎉', '')
        
        logging.basicConfig(
            level=getattr(logging, level),
            format=format_str,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('real_estate_ai.log', encoding='utf-8')
            ]
        )

    def setup_data(self):
        """Setup data processing and build indices"""
        self.logger.info("📊 Setting up data processing...")
        
        # Initialize data processor
        self.data_processor = JSONLProcessor(self.config)
        
        # Load and process data
        data = self.data_processor.load_jsonl_data()
        if not data:
            self.logger.error("❌ No data loaded")
            return False
        
        self.logger.info(f"📄 Loaded {len(data)} projects")
        
        # Extract document chunks
        documents = self.data_processor.extract_document_chunks(data)
        self.logger.info(f"📝 Created {len(documents)} document chunks")
        
        # Build vector store
        self.vector_store = VectorStore(self.config)
        self.vector_store.build_index(documents)
        self.logger.info("✅ Vector store built successfully")
        
        # Build sparse retriever
        self.sparse_retriever = SparseRetriever(self.config)
        self.sparse_retriever.build_index(documents)
        self.logger.info("✅ Sparse retriever built successfully")
        
        # Initialize other components
        self._initialize_components()
        
        self.logger.info("🎉 Data setup completed successfully")
        return True

    def _initialize_components(self):
        """Initialize RAG components"""
        self.router = QueryRouter(self.config)
        self.fusion = HybridFusion(self.config)
        self.retriever = AdaptiveRetriever(
            self.vector_store, self.sparse_retriever, self.router, self.fusion, self.config
        )
        self.generator = ResponseGenerator(self.config)
        
        self.logger.info("✅ RAG components initialized")

    def load_existing_model(self):
        """Load existing models and indices"""
        try:
            self.logger.info("🔧 Loading existing models...")
            
            # Load vector store
            self.vector_store = VectorStore(self.config)
            if not self.vector_store.load_existing():
                self.logger.error("❌ Could not load existing vector store")
                return False
            
            # Load sparse retriever
            self.sparse_retriever = SparseRetriever(self.config)
            if not self.sparse_retriever.load_existing():
                self.logger.error("❌ Could not load existing sparse retriever")
                return False
            
            # Initialize components
            self._initialize_components()
            
            self.logger.info("✅ Existing models loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error loading existing models: {e}")
            return False

    def process_query(self, query: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """Process a single query through the entire pipeline"""
        self.logger.info(f"🔍 Processing query: '{query}'")
        
        try:
            # Retrieve relevant documents
            retrieval_result = self.retriever.retrieve(query, conversation_history)
            
            # Generate response
            response = self.generator.generate_response(query, retrieval_result, conversation_history)
            
            result = {
                'query': query,
                'response': response,
                'retrieval_result': retrieval_result,
                'success': True
            }
            
            self.logger.info("✅ Query processed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error processing query: {e}")
            return {
                'query': query,
                'response': f"I encountered an error while processing your query: {str(e)}",
                'retrieval_result': None,
                'success': False,
                'error': str(e)
            }

    def test_retrieval(self, query: str):
        """Test retrieval without generating response"""
        self.logger.info(f"🧪 Testing retrieval for: '{query}'")
        
        try:
            retrieval_result = self.retriever.retrieve(query)
            
            print(f"\n🎯 QUERY: '{query}'")
            print(f"📊 Query Type: {retrieval_result.get('query_type', 'unknown')}")
            print(f"🏷️ Categories: {retrieval_result.get('categories', [])}")
            print(f"🔍 Entities: {retrieval_result.get('entities', {})}")
            print(f"🧠 Reasoning: {retrieval_result.get('reasoning', '')}")
            print(f"📄 Documents Found: {len(retrieval_result.get('documents', []))}")
            print(f"🔄 Use RAG: {retrieval_result.get('use_rag', False)}")
            
            # Show top documents
            documents = retrieval_result.get('documents', [])
            if documents:
                print(f"\n📋 TOP DOCUMENTS:")
                for i, doc in enumerate(documents[:3]):  # Show top 3
                    metadata = doc['document']['metadata']
                    score = doc.get('normalized_score', 0)
                    project_name = metadata.get('project_name', 'Unknown')
                    chunk_type = metadata.get('chunk_type', 'Unknown')
                    
                    print(f"  {i+1}. 📊 Score: {score:.3f}")
                    print(f"     🏢 Project: {project_name}")
                    print(f"     📝 Type: {chunk_type}")
                    print(f"     📄 Preview: {doc['document']['content'][:100]}...")
                    print()
            else:
                print("❌ No documents retrieved")
                
            return retrieval_result
            
        except Exception as e:
            print(f"❌ Error in retrieval test: {e}")
            return None
            

    def chat_mode(self):
        """Interactive chat mode"""
        if not self.load_existing_model():
            print("❌ Please run setup-data first to initialize the system")
            return
        
        print("\n" + "="*60)
        print("🏗️  REAL ESTATE AI CHAT MODE")
        print("="*60)
        print("Type 'quit' or 'exit' to end the chat")
        print("Type 'test' to see retrieval details")
        print("Type 'history' to see conversation history")
        print("="*60)
        
        conversation_history = []
        
        while True:
            try:
                query = input("\n💬 You: ").strip()
                
                if query.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Thank you for using Real Estate AI. Goodbye!")
                    break
                
                elif query.lower() == 'test':
                    test_query = input("Enter query to test retrieval: ").strip()
                    if test_query:
                        self.test_retrieval(test_query)
                    continue
                
                elif query.lower() == 'history':
                    print("\n📜 CONVERSATION HISTORY:")
                    for i, entry in enumerate(conversation_history[-5:], 1):  # Last 5 entries
                        print(f"  {i}. You: {entry.get('query', '')}")
                        print(f"     AI: {entry.get('response', '')[:100]}...")
                    continue
                
                elif not query:
                    continue
                
                # Process the query
                result = self.process_query(query, conversation_history)
                
                # Display response
                print(f"\n🤖 AI: {result['response']}")
                
                # Add to conversation history
                conversation_history.append({
                    'query': query,
                    'response': result['response'],
                    'timestamp': len(conversation_history)
                })
                
                # Keep history manageable
                if len(conversation_history) > 10:
                    conversation_history = conversation_history[-10:]
                    
            except KeyboardInterrupt:
                print("\n\n👋 Chat session ended.")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                continue

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Real Estate AI with Hybrid RAG")
    parser.add_argument("--setup-data", action="store_true", help="Setup data and build indices")
    parser.add_argument("--chat", action="store_true", help="Start interactive chat mode")
    parser.add_argument("--test", action="store_true", help="Test retrieval for a query")
    parser.add_argument("--query", type=str, help="Query to process")
    parser.add_argument("--config", type=str, default="config/config.yaml", help="Config file path")
    
    args = parser.parse_args()
    
    # Initialize the AI system
    ai_system = RealEstateAI(args.config)
    
    try:
        if args.setup_data:
            # Setup data and build indices
            success = ai_system.setup_data()
            if success:
                print("🎉 Data setup completed successfully!")
            else:
                print("❌ Data setup failed!")
                sys.exit(1)
                
        elif args.chat:
            # Start interactive chat
            ai_system.chat_mode()
            
        elif args.test and args.query:
            # Test retrieval for specific query
            if ai_system.load_existing_model():
                ai_system.test_retrieval(args.query)
            else:
                print("❌ Please run setup-data first")
                
        elif args.query:
            # Process single query
            if ai_system.load_existing_model():
                result = ai_system.process_query(args.query)
                print(f"\n🎯 QUERY: {result['query']}")
                print(f"🤖 RESPONSE: {result['response']}")
                
                if result['retrieval_result']:
                    retrieval = result['retrieval_result']
                    print(f"📊 Documents used: {len(retrieval.get('documents', []))}")
                    print(f"🧠 Reasoning: {retrieval.get('reasoning', '')}")
            else:
                print("❌ Please run setup-data first")
                
        else:
            # Show help
            parser.print_help()
            print("\n💡 Examples:")
            print("  python main.py --setup-data")
            print("  python main.py --chat")
            print("  python main.py --test --query \"projects in Mumbai\"")
            print("  python main.py --query \"Show me residential projects in Pune\"")
            
    except Exception as e:
        print(f"❌ Error in main: {e}")
        logging.error(f"Error in main: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()