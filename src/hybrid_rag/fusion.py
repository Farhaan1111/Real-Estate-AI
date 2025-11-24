from typing import List, Dict, Any
import numpy as np
import logging

class HybridFusion:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.fusion_method = config['adaptive_rag']['fusion_method']
        self.logger = logging.getLogger(__name__)

    def fuse_results(self, dense_results: List[Dict], sparse_results: List[Dict],
                    retrieval_params: Dict[str, Any] = None) -> List[Dict]:
        """Enhanced fusion with robust normalization"""
        if retrieval_params:
            dense_weight = retrieval_params.get('dense_weight', 0.6)
            sparse_weight = retrieval_params.get('sparse_weight', 0.4)
        else:
            dense_weight = self.config['adaptive_rag']['dense_weight']
            sparse_weight = self.config['adaptive_rag']['sparse_weight']
        
        return self._enhanced_weighted_fusion(dense_results, sparse_results, dense_weight, sparse_weight)

    def _enhanced_weighted_fusion(self, dense_results: List[Dict], sparse_results: List[Dict],
                                dense_weight: float, sparse_weight: float) -> List[Dict]:
        """Enhanced weighted fusion with robust score handling"""
        fused_results = {}
        
        # Normalize dense scores (FAISS distances to similarities)
        dense_scores = [result['score'] for result in dense_results]
        dense_normalized = self._robust_normalize(dense_scores, invert=True)  # Invert since FAISS returns distances
        
        # Normalize sparse scores (BM25 scores)
        sparse_scores = [result['score'] for result in sparse_results]
        sparse_normalized = self._robust_normalize(sparse_scores, invert=False)
        
        # Process dense results
        for i, result in enumerate(dense_results):
            doc_id = result['document']['metadata']['doc_id']
            dense_norm = dense_normalized[i] if i < len(dense_normalized) else 0.0
            
            fused_results[doc_id] = {
                'document': result['document'],
                'dense_score': dense_norm,
                'sparse_score': 0.0,
                'combined_score': dense_norm * dense_weight,
                'retrieval_types': ['dense'],
                'raw_dense_score': result['score'],
                'normalized_score': dense_norm
            }
        
        # Process sparse results and combine
        for i, result in enumerate(sparse_results):
            doc_id = result['document']['metadata']['doc_id']
            sparse_norm = sparse_normalized[i] if i < len(sparse_normalized) else 0.0
            
            if doc_id in fused_results:
                # Document exists in both, combine scores
                fused_results[doc_id]['sparse_score'] = sparse_norm
                fused_results[doc_id]['combined_score'] += sparse_norm * sparse_weight
                fused_results[doc_id]['retrieval_types'].append('sparse')
                fused_results[doc_id]['raw_sparse_score'] = result['score']
            else:
                # Document only in sparse results
                fused_results[doc_id] = {
                    'document': result['document'],
                    'dense_score': 0.0,
                    'sparse_score': sparse_norm,
                    'combined_score': sparse_norm * sparse_weight,
                    'retrieval_types': ['sparse'],
                    'raw_sparse_score': result['score'],
                    'normalized_score': sparse_norm
                }
        
        # Convert to list and sort by combined score
        final_results = list(fused_results.values())
        final_results.sort(key=lambda x: x['combined_score'], reverse=True)
        
        # Final normalization to 0-1 range
        if final_results:
            combined_scores = [result['combined_score'] for result in final_results]
            final_normalized = self._robust_normalize(combined_scores, invert=False)
            
            for i, result in enumerate(final_results):
                result['normalized_score'] = final_normalized[i] if i < len(final_normalized) else 0.0
        
        return final_results

    def _robust_normalize(self, scores: List[float], invert: bool = False) -> List[float]:
        """Robust normalization that handles edge cases"""
        if not scores:
            return []
        
        if invert:
            # Convert distances to similarities (lower distance = higher similarity)
            scores = [1 / (1 + score) for score in scores]
        
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score > min_score:
            return [(score - min_score) / (max_score - min_score) for score in scores]
        else:
            # All scores are the same
            return [1.0] * len(scores) if scores else []