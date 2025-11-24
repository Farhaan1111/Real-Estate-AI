from typing import List, Dict, Any
from ..embedding.vector_store import VectorStore
from ..embedding.sparse_retriever import SparseRetriever
from .router import QueryRouter
from .fusion import HybridFusion
import logging

class AdaptiveRetriever:
    def __init__(self, vector_store: VectorStore, sparse_retriever: SparseRetriever,
                 router: QueryRouter, fusion: HybridFusion, config: Dict[str, Any]):
        self.vector_store = vector_store
        self.sparse_retriever = sparse_retriever
        self.router = router
        self.fusion = fusion
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Enhanced query expansion for ALL categories
        self.expansion_rules = {
            'project_identification': ['project', 'development', 'property', 'real estate', 'construction'],
            'temporal': ['date', 'completion', 'registration', 'possession', 'timeline'],
            'location': ['location', 'address', 'area', 'district', 'taluka', 'village', 'city', 'region'],
            'structural': ['building', 'floor', 'tower', 'wing', 'phase', 'basement', 'stilt'],
            'units': ['unit', 'apartment', 'flat', 'sold', 'unsold', 'commercial', 'residential'],
            'land': ['land', 'area', 'plot', 'survey', 'builtup', 'square meters'],
            'promoter': ['promoter', 'developer', 'builder', 'company', 'construction'],
            'legal': ['legal', 'litigation', 'financial', 'encumbrance', 'mortgage'],
            'analytical': ['compare', 'analysis', 'statistics', 'trend', 'ranking', 'best'],
            'numeric': ['number', 'count', 'total', 'more than', 'less than']
        }
        
        # Comprehensive synonym mapping
        self.synonym_map = {
            'builder': ['promoter', 'developer', 'construction company'],
            'flat': ['apartment', 'unit', 'home', 'residence'],
            'possession': ['completion', 'handover', 'ready to move'],
            'ongoing': ['under construction', 'in progress', 'developing'],
            'new': ['recent', 'latest', 'just registered', 'newly launched'],
            'show': ['list', 'display', 'find', 'search', 'locate'],
            'near': ['close to', 'around', 'in the area of', 'proximity'],
            'project': ['development', 'property', 'real estate', 'construction'],
            'sold': ['booked', 'occupied', 'taken'],
            'unsold': ['available', 'vacant', 'free'],
            'commercial': ['shop', 'office', 'retail', 'business'],
            'residential': ['housing', 'apartment', 'flat', 'home'],
            'compare': ['versus', 'vs', 'difference between', 'contrast'],
            'best': ['top', 'excellent', 'great', 'quality'],
            'large': ['big', 'spacious', 'expansive', 'huge']
        }

    def retrieve(self, query: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """Enhanced hybrid retrieval for ALL query types"""
        # Classify query and get parameters
        classification = self.router.classify_query_comprehensive(query)
        query_type = self.router.classify_query(query)
        use_rag = self.router.should_use_rag(query, conversation_history)
        
        if not use_rag:
            return {
                'use_rag': False,
                'documents': [],
                'query_type': query_type,
                'categories': classification['categories'],
                'entities': classification['entities'],
                'reasoning': f'Conversational query ({query_type}), using LLM directly'
            }
        
        # Get retrieval parameters
        params = self.router.get_retrieval_params(query)
        
        # Apply enhanced query expansion
        expanded_query = self._expand_query_comprehensive(query, classification)
        if expanded_query != query:
            self.logger.info(f"Query expanded: '{query}' -> '{expanded_query}'")
        
        # Perform both dense and sparse retrieval with optimized parameters
        sparse_k = params['k'] * 2 if params.get('force_sparse', False) else params['k']
        
        dense_results = self.vector_store.search(expanded_query, k=params['k'])
        sparse_results = self.sparse_retriever.search(expanded_query, k=sparse_k)
        
        self.logger.info(f"Retrieved {len(dense_results)} dense + {len(sparse_results)} sparse documents")
        
        # Fuse results with dynamic weights
        fused_results = self.fusion.fuse_results(dense_results, sparse_results, params)
        
        # Apply score threshold with dynamic adjustment
        filtered_results = self._apply_dynamic_threshold(fused_results, params)
        
        # Take top k results
        final_results = filtered_results[:self.config['retrieval']['final_top_k']]
        
        # Generate detailed reasoning
        reasoning = self._generate_detailed_reasoning(classification, params, 
                                                     len(dense_results), len(sparse_results), 
                                                     len(final_results))
        
        return {
            'use_rag': True,
            'documents': final_results,
            'dense_results': dense_results,
            'sparse_results': sparse_results,
            'fused_results': fused_results,
            'query_type': query_type,
            'categories': classification['categories'],
            'entities': classification['entities'],
            'retrieval_params': params,
            'expanded_query': expanded_query if expanded_query != query else None,
            'reasoning': reasoning
        }

    def _expand_query_comprehensive(self, query: str, classification: Dict) -> str:
        """Enhanced query expansion for fine-grained details"""
        expanded_terms = [query]
        categories = classification['categories']
        entities = classification['entities']
        
        # Fine-grained expansion terms
        fine_grained_terms = {
            'structural': ['floors', 'storeys', 'levels', 'building', 'tower', 'wing', 'basement', 'stilt'],
            'units': ['apartments', 'flats', 'units', 'sold', 'unsold', 'commercial', 'residential', 'inventory'],
            'land': ['area', 'sqm', 'square meters', 'builtup', 'plot', 'survey', 'land area'],
            'numeric': ['number', 'count', 'total', 'more than', 'less than', 'units', 'flats'],
            'location': ['address', 'location', 'district', 'taluka', 'village', 'pincode', 'coordinates']
        }
        
        # Add category-specific fine-grained terms
        for category in categories:
            if category in fine_grained_terms:
                expanded_terms.extend(fine_grained_terms[category])
        
        # Remove duplicates and very short terms
        unique_terms = []
        for term in expanded_terms:
            if (term not in unique_terms and
                len(term) > 2 and
                not term.isdigit()):
                unique_terms.append(term)
        
        return " ".join(unique_terms)

    def _apply_dynamic_threshold(self, fused_results: List[Dict], params: Dict) -> List[Dict]:
        """Apply dynamic score threshold with multiple fallback strategies"""
        filtered_results = []
        
        # Apply primary threshold
        if fused_results:
            filtered_results = [
                result for result in fused_results
                if result.get('normalized_score', 0) >= params['score_threshold']
            ]
        
        self.logger.info(f"After threshold {params['score_threshold']}: {len(filtered_results)} results")
        
        # First fallback: Lower threshold
        if not filtered_results and fused_results:
            adjusted_threshold = params['score_threshold'] * 0.5  # 50% lower
            self.logger.info(f"Lowering score threshold from {params['score_threshold']} to {adjusted_threshold:.3f}")
            
            filtered_results = [
                result for result in fused_results
                if result.get('normalized_score', 0) >= adjusted_threshold
            ]
        
        # Second fallback: Take top results by score
        if not filtered_results and fused_results:
            self.logger.info("Taking top 3 results by normalized score (threshold bypass)")
            filtered_results = sorted(
                fused_results,
                key=lambda x: x.get('normalized_score', 0),
                reverse=True
            )[:3]
        
        # Third fallback: Ensure at least one result for exact matches
        if not filtered_results and fused_results and params.get('force_sparse', False):
            self.logger.info("Force including top sparse result for exact match")
            # Find the result with highest sparse score
            best_sparse = max(fused_results, 
                            key=lambda x: x.get('sparse_score', 0))
            filtered_results = [best_sparse]
        
        return filtered_results

    def _generate_detailed_reasoning(self, classification: Dict, params: Dict,
                                   dense_count: int, sparse_count: int, final_count: int) -> str:
        """Generate detailed reasoning for retrieval process"""
        reasoning_parts = [
            f"Query classified as '{classification['primary_type']}'",
            f"Categories: {', '.join(classification['categories']) if classification['categories'] else 'general'}",
            f"Complexity score: {classification['complexity_score']}",
            f"Retrieved {dense_count} dense + {sparse_count} sparse documents",
            f"Final results: {final_count} after fusion and filtering",
            f"Strategy: {params.get('dense_weight', 0.6):.1f}dense + {params.get('sparse_weight', 0.4):.1f}sparse"
        ]
        
        if classification['entities']:
            entity_info = []
            for entity_type, entities in classification['entities'].items():
                if entities:
                    entity_info.append(f"{entity_type}: {entities}")
            if entity_info:
                reasoning_parts.append(f"Entities: {'; '.join(entity_info)}")
        
        return ". ".join(reasoning_parts)