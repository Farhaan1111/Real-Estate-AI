#!/usr/bin/env python3
"""
Real Estate AI Evaluation System
Run this directly to evaluate your RAG system
"""

import os
import sys
import json
import time
import numpy as np
from datetime import datetime
from typing import List, Dict, Any
import logging

# Add the project root to path to import your modules
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

class SimpleRAGEvaluator:
    """
    Lightweight RAG evaluation system - no extra installations needed
    """
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.metrics_history = []
        
    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def evaluate_retrieval(self, retrieved_docs: List[List[Dict]]) -> Dict[str, float]:
        """Evaluate retrieval quality using document scores"""
        scores = []
        doc_counts = []
        
        for docs in retrieved_docs:
            if docs:
                # Use normalized scores from retrieval
                doc_scores = [doc.get('normalized_score', 0) for doc in docs]
                avg_score = np.mean(doc_scores) if doc_scores else 0
                scores.append(avg_score)
                doc_counts.append(len(docs))
            else:
                scores.append(0)
                doc_counts.append(0)
        
        return {
            'retrieval_score_mean': float(np.mean(scores)),
            'retrieval_score_std': float(np.std(scores)),
            'retrieval_success_rate': float(np.mean([1 if score > 0.1 else 0 for score in scores])),
            'avg_docs_per_query': float(np.mean(doc_counts)),
            'empty_retrievals': float(np.mean([1 if count == 0 else 0 for count in doc_counts]))
        }
    
    def evaluate_response_quality(self, questions: List[str], responses: List[str]) -> Dict[str, float]:
        """Basic response quality evaluation using heuristics"""
        quality_scores = []
        relevance_scores = []
        length_scores = []
        
        # Real estate domain keywords
        real_estate_keywords = [
            'rera', 'project', 'building', 'apartment', 'floor', 'unit', 'floors',
            'registration', 'completion', 'promoter', 'location', 'area', 'land',
            'sqm', 'meters', 'residential', 'commercial', 'mumbai', 'pune', 'thane',
            'construction', 'developed', 'approved', 'sanctioned', 'built'
        ]
        
        for question, response in zip(questions, responses):
            response = response.lower().strip()
            question = question.lower()
            
            # Length score (ideal: 50-500 characters)
            response_len = len(response)
            if response_len < 50:
                length_score = response_len / 50
            elif response_len > 500:
                length_score = 500 / response_len
            else:
                length_score = 1.0
            length_scores.append(length_score)
            
            # Relevance score - check if response contains question keywords
            question_words = set(question.split())
            response_words = set(response.split())
            
            # Count relevant real estate keywords from question that appear in response
            relevant_keywords = [word for word in real_estate_keywords 
                               if word in question and word in response]
            relevance_score = len(relevant_keywords) / max(1, len([w for w in real_estate_keywords if w in question]))
            relevance_scores.append(relevance_score)
            
            # Quality score combination
            quality = 0.4 * length_score + 0.6 * relevance_score
            quality_scores.append(quality)
        
        return {
            'response_quality_mean': float(np.mean(quality_scores)),
            'response_relevance_mean': float(np.mean(relevance_scores)),
            'response_length_mean': float(np.mean([len(r) for r in responses])),
            'empty_responses': float(np.mean([1 if len(r.strip()) == 0 else 0 for r in responses])),
            'high_quality_responses': float(np.mean([1 if q > 0.7 else 0 for q in quality_scores]))
        }
    
    def evaluate_performance(self, processing_times: List[float]) -> Dict[str, float]:
        """Performance metrics evaluation"""
        if not processing_times:
            return {
                'avg_processing_time': 0.0,
                'p95_processing_time': 0.0,
                'queries_per_minute': 0.0
            }
        
        times_array = np.array(processing_times)
        
        return {
            'avg_processing_time': float(np.mean(times_array)),
            'p95_processing_time': float(np.percentile(times_array, 95)),
            'min_processing_time': float(np.min(times_array)),
            'max_processing_time': float(np.max(times_array)),
            'queries_per_minute': float(60 / np.mean(times_array) if np.mean(times_array) > 0 else 0)
        }
    
    def run_comprehensive_evaluation(self, ai_system, test_queries: List[str]) -> Dict[str, Any]:
        """Run complete evaluation on test queries"""
        self.logger.info("🚀 Starting comprehensive RAG evaluation...")
        self.logger.info(f"📝 Testing with {len(test_queries)} queries")
        
        all_responses = []
        all_retrieved_docs = []
        processing_times = []
        
        # Process each test query
        for i, query in enumerate(test_queries, 1):
            self.logger.info(f"🔍 Processing query {i}/{len(test_queries)}: '{query}'")
            
            start_time = time.time()
            
            try:
                # Use your existing system
                result = ai_system.process_query(query)
                processing_time = time.time() - start_time
                
                all_responses.append(result['response'])
                processing_times.append(processing_time)
                
                # Extract retrieved documents
                if result.get('retrieval_result') and result['retrieval_result'].get('documents'):
                    retrieved_docs = result['retrieval_result']['documents']
                    all_retrieved_docs.append(retrieved_docs)
                else:
                    all_retrieved_docs.append([])
                
                self.logger.info(f"✅ Query {i} completed in {processing_time:.2f}s")
                
            except Exception as e:
                self.logger.error(f"❌ Error processing query '{query}': {e}")
                all_responses.append("")
                all_retrieved_docs.append([])
                processing_times.append(0)
        
        # Calculate all metrics
        retrieval_metrics = self.evaluate_retrieval(all_retrieved_docs)
        response_metrics = self.evaluate_response_quality(test_queries, all_responses)
        performance_metrics = self.evaluate_performance(processing_times)
        
        # Composite overall score
        overall_score = (
            retrieval_metrics['retrieval_score_mean'] * 0.4 +
            response_metrics['response_quality_mean'] * 0.4 +
            (1 - min(performance_metrics['avg_processing_time'] / 10, 1)) * 0.2
        )
        
        final_metrics = {
            'timestamp': datetime.now().isoformat(),
            'overall_score': float(overall_score),
            'retrieval_metrics': retrieval_metrics,
            'response_metrics': response_metrics,
            'performance_metrics': performance_metrics,
            'test_queries_processed': len(test_queries),
            'successful_queries': len([r for r in all_responses if r.strip()])
        }
        
        self.metrics_history.append(final_metrics)
        self._save_metrics(final_metrics)
        
        return final_metrics
    
    def _save_metrics(self, metrics: Dict[str, Any]):
        """Save metrics to JSON file"""
        metrics_file = os.path.join(project_root, 'evaluation', 'metrics.json')
        
        # Create evaluation directory if it doesn't exist
        os.makedirs(os.path.dirname(metrics_file), exist_ok=True)
        
        # Load existing metrics or create new list
        if os.path.exists(metrics_file):
            with open(metrics_file, 'r') as f:
                existing_metrics = json.load(f)
        else:
            existing_metrics = []
        
        existing_metrics.append(metrics)
        
        with open(metrics_file, 'w') as f:
            json.dump(existing_metrics, f, indent=2)
        
        self.logger.info(f"💾 Metrics saved to {metrics_file}")
    
    def generate_report(self, metrics: Dict[str, Any]) -> str:
        """Generate a human-readable evaluation report"""
        report = [
            "=" * 60,
            "           REAL ESTATE AI - EVALUATION REPORT",
            "=" * 60,
            f"Evaluation Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Queries Processed: {metrics['test_queries_processed']}",
            f"Successful Queries: {metrics['successful_queries']}",
            "",
            "📊 OVERALL SCORES:",
            f"  Overall System Score: {metrics['overall_score']:.3f}/1.0",
            "",
            "🎯 RETRIEVAL METRICS:",
            f"  Retrieval Score: {metrics['retrieval_metrics']['retrieval_score_mean']:.3f}",
            f"  Success Rate: {metrics['retrieval_metrics']['retrieval_success_rate']:.3f}",
            f"  Docs per Query: {metrics['retrieval_metrics']['avg_docs_per_query']:.1f}",
            f"  Empty Retrievals: {metrics['retrieval_metrics']['empty_retrievals']:.3f}",
            "",
            "💬 RESPONSE METRICS:",
            f"  Response Quality: {metrics['response_metrics']['response_quality_mean']:.3f}",
            f"  Response Relevance: {metrics['response_metrics']['response_relevance_mean']:.3f}",
            f"  Avg Response Length: {metrics['response_metrics']['response_length_mean']:.1f} chars",
            f"  High Quality Responses: {metrics['response_metrics']['high_quality_responses']:.3f}",
            "",
            "⚡ PERFORMANCE METRICS:",
            f"  Avg Processing Time: {metrics['performance_metrics']['avg_processing_time']:.2f}s",
            f"  P95 Processing Time: {metrics['performance_metrics']['p95_processing_time']:.2f}s",
            f"  Queries per Minute: {metrics['performance_metrics']['queries_per_minute']:.1f}",
            "",
            "📈 INTERPRETATION:",
        ]
        
        # Add interpretation
        overall = metrics['overall_score']
        if overall >= 0.8:
            report.append("  🎉 EXCELLENT - System is performing very well!")
        elif overall >= 0.6:
            report.append("  ✅ GOOD - System is working properly")
        elif overall >= 0.4:
            report.append("  ⚠️  FAIR - System needs some improvements")
        else:
            report.append("  ❌ POOR - System requires significant improvements")
        
        report.append("=" * 60)
        
        return "\n".join(report)

def main():
    """Main function to run evaluation"""
    print("🚀 Starting Real Estate AI Evaluation...")
    
    try:
        # Import your existing system - fixed import
        print("🔧 Importing AI system...")
        
        # Try different import approaches
        try:
            # First try direct import
            from main import RealEstateAI
        except ImportError:
            # Try adding the path
            import sys
            sys.path.append(project_root)
            from main import RealEstateAI
        
        # Initialize your AI system
        print("🔧 Initializing AI system...")
        config_path = os.path.join(project_root, 'config', 'config.yaml')
        ai_system = RealEstateAI(config_path)
        
        if not ai_system.load_existing_model():
            print("❌ Failed to load AI models. Please run setup first.")
            print("💡 Run: python main.py --setup-data")
            return
        
        # Test queries for evaluation
        test_queries = [
            "Show me residential projects in Mumbai",
            "How many floors in UNNATHI WOODS project",
            "What is the RERA registration number for UNNATHI WOODS",
            "List projects by UNNATHI ESTATES",
            "Show me projects completed in 2024",
            "What is the land area of UNNATHI WOODS",
            "How many apartments in UNNATHI WOODS",
            "Show me projects in Pune district",
            "What is the promoter address for UNNATHI WOODS",
            "Compare residential projects in Mumbai and Pune"
        ]
        
        # Run evaluation
        evaluator = SimpleRAGEvaluator()
        metrics = evaluator.run_comprehensive_evaluation(ai_system, test_queries)
        
        # Generate and display report
        report = evaluator.generate_report(metrics)
        print("\n" + report)
        
        metrics_file = os.path.join(project_root, 'evaluation', 'metrics.json')
        print(f"\n💾 Full metrics saved to: {metrics_file}")
        
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        print(f"\n💡 Make sure you're running from the project root directory")
        print(f"💡 Current working directory: {os.getcwd()}")

if __name__ == "__main__":
    main()