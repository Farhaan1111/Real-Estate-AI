from typing import List, Dict, Any
import logging
import requests
import json
import os

class ResponseGenerator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # LLM configuration - Using OpenRouter
        self.llm_provider = "openrouter"
        self.model_name = "openai/gpt-3.5-turbo"  # Options: "openai/gpt-3.5-turbo", "openai/gpt-4", "anthropic/claude-3-sonnet", etc.
        
        # OpenRouter configuration - Get from environment variable or config
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY', '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')
        self.openrouter_base_url = "https://openrouter.ai/api/v1"
        # Query type specific instructions (keep the existing ones)
        self.query_type_instructions = {
            "exact": "Focus on providing precise, factual information from the documents. Include specific details like registration numbers, dates, and exact specifications. Be concise and accurate.",
            
            "simple": "Provide clear, factual answers based on the documents. Be concise but comprehensive. Include relevant numbers, dates, and specifics. Reference RERA registration numbers when available.",
            
            "complex": "Analyze the documents comprehensively. Compare projects if needed. Provide insights, recommendations, or analysis based on the available data. If making comparisons, be objective and data-driven. Include relevant statistics and trends.",
            
            "conversational": "Be friendly and helpful. If the conversation relates to real estate, use the document context. Otherwise, respond conversationally. Keep responses natural and engaging."
        }
        
        # Category-specific guidance (keep the existing ones)
        self.category_guidance = {
            'project_identification': "Focus on project details, registration information, and basic specifications.",
            'temporal': "Pay close attention to dates, timelines, and project status related to time.",
            'location': "Emphasize geographic details, addresses, and location-specific information.",
            'structural': "Highlight building specifications, floor counts, and structural details.",
            'units': "Focus on apartment counts, sold/unsold status, and unit distribution.",
            'land': "Discuss land area, built-up area, and plot-related information.",
            'promoter': "Provide details about developers, builders, and promoter information.",
            'legal': "Address legal status, financial encumbrances, and litigation details carefully.",
            'analytical': "Provide comparative analysis, rankings, and data-driven insights.",
            'numeric': "Include specific numbers, counts, and quantitative information."
        }

    def generate_response(self, query: str, retrieval_result: Dict[str, Any], 
                         conversation_history: List[Dict] = None) -> str:
        """Generate response optimized for query type and categories"""
        if not retrieval_result['use_rag']:
            return self._call_llm_direct(query)
        
        # RAG-based response
        context_docs = retrieval_result['documents']
        if not context_docs:
            return self._handle_no_documents(query, retrieval_result)
        
        # Build enhanced context
        context = self._build_enhanced_context(context_docs)
        
        # Build optimized prompt
        query_type = retrieval_result.get('query_type', 'simple')
        categories = retrieval_result.get('categories', [])
        entities = retrieval_result.get('entities', {})
        
        prompt = self._build_optimized_prompt(query, context, query_type, categories, entities)
        
        return self._call_llm(prompt)

    def _build_enhanced_context(self, context_docs: List[Dict]) -> str:
        """Build enhanced context with relevance scores and metadata"""
        context_parts = []
        
        for i, doc in enumerate(context_docs):
            metadata = doc['document']['metadata']
            normalized_score = doc.get('normalized_score', 0)
            project_name = metadata.get('project_name', 'Unknown Project')
            chunk_type = metadata.get('chunk_type', 'Unknown Type')
            registration = metadata.get('registration_number', 'Unknown Registration')
            
            context_header = f"Document {i+1} (Relevance: {normalized_score:.3f})"
            context_header += f" | Project: {project_name} | Type: {chunk_type}"
            if registration != 'Unknown Registration':
                context_header += f" | RERA: {registration}"
            
            context_parts.append(f"{context_header}")
            context_parts.append(f"{doc['document']['content']}")
            context_parts.append("")  # Empty line for separation
        
        return "\n".join(context_parts)

    def _build_optimized_prompt(self, query: str, context: str, query_type: str,
                          categories: List[str], entities: Dict) -> str:
        """Ultra-detailed prompt for micro-level queries"""
        
        micro_detail_instructions = ""
        if any(cat in categories for cat in ['micro_details', 'structural_micro', 'location_micro']):
            micro_detail_instructions = """
    CRITICAL INSTRUCTIONS FOR MICRO-DETAIL QUERIES:
    - Extract and provide EXACT values from the context
    - Be extremely precise with numbers, measurements, and specifications
    - If asking about specific items, provide details for EACH one individually
    - Include all numerical values exactly as they appear
    - Don't approximate or estimate - use exact numbers
    - For "how many" questions, provide the precise count
    - For structural details, specify which building/wing they belong to
    """

        user_prompt = f"""You are a PRECISE real estate expert. Answer the user's question with EXACT details from the provided context.

    CONTEXT DOCUMENTS:

    {context}

    QUESTION: {query}

    INSTRUCTIONS:
    {self.query_type_instructions.get(query_type, self.query_type_instructions["simple"])}
    {micro_detail_instructions}

    MANDATORY GUIDELINES FOR PRECISION:
    1. Extract EXACT numbers, dates, measurements from the context
    2. Be specific about which building/wing/floor you're referring to
    3. Provide complete details without omission
    4. If multiple values exist, list them all
    5. Use precise terminology from the context
    6. Never approximate - always use exact values

    ANSWER FORMAT FOR MICRO-DETAILS:
    - For numbers: "Exactly X" or "Precisely Y"
    - For lists: Provide complete enumeration
    - For measurements: Include units (sqm, floors, units, etc.)
    - For locations: Provide exact coordinates/addresses

    Answer with ULTIMATE PRECISION using only the provided context."""
        
        return user_prompt

    def _get_entity_instructions(self, entities: Dict) -> str:
        """Get specific instructions based on extracted entities"""
        instructions = []
        
        if 'rera_ids' in entities:
            instructions.append("Focus on the specific RERA registration numbers mentioned.")
        
        if 'project_names' in entities:
            instructions.append("Provide detailed information about the specific projects mentioned.")
        
        if 'districts' in entities:
            instructions.append("Emphasize location-specific details for the mentioned districts.")
        
        if 'years' in entities:
            instructions.append("Pay close attention to date-related information and timelines.")
        
        if 'numbers' in entities:
            instructions.append("Include specific numerical data and quantitative comparisons.")
        
        if 'top_n' in entities:
            instructions.append(f"Provide a ranked list of top {entities['top_n']} results.")
        
        return " " + ". ".join(instructions) if instructions else ""

    def _handle_no_documents(self, query: str, retrieval_result: Dict) -> str:
        """Handle cases where no documents are retrieved"""
        query_type = retrieval_result.get('query_type', 'simple')
        categories = retrieval_result.get('categories', [])
        
        if query_type == 'conversational':
            return "I'm here to help you with RERA project information! How can I assist you today?"
        
        elif 'location' in categories:
            return f"I don't have specific information about projects in that location in my current RERA database. Could you try a different district or location, or ask about general RERA project information?"
        
        elif 'project_identification' in categories:
            return f"I couldn't find specific information about that project in my RERA database. The project might not be in my current dataset, or you could try searching with the exact RERA registration number."
        
        else:
            return f"I don't have enough specific information in my RERA database to answer that question accurately. Could you please rephrase your question or ask about general RERA project information?"

    def _call_llm_direct(self, query: str) -> str:
        """Call LLM for direct conversational responses"""
        prompt = f"""You are a helpful real estate AI assistant. Answer the following question in a friendly, conversational manner.

Question: {query}

Provide a helpful and engaging response."""
        
        return self._call_llm(prompt)

    def _call_llm(self, prompt: str) -> str:
        """Call the LLM with OpenRouter"""
        try:
            if self.llm_provider == "openrouter":
                return self._call_openrouter(prompt)
            else:
                return self._fallback_response(prompt)
                
        except Exception as e:
            self.logger.error(f"LLM call failed: {e}")
            return self._fallback_response(prompt)

    def _call_openrouter(self, prompt: str) -> str:
        """Call OpenRouter API"""
        try:
            url = f"{self.openrouter_base_url}/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {self.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/your-repo",  # Optional but recommended
                "X-Title": "Real Estate AI"  # Optional but recommended
            }
            
            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a real estate expert AI assistant specialized in RERA (Real Estate Regulatory Authority) projects in India. Be accurate, factual, and helpful."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.1,
                "top_p": 0.9
            }
            
            self.logger.info("Calling OpenRouter API...")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0]['message']['content']
                    self.logger.info("✅ OpenRouter response received successfully")
                    return content
                else:
                    self.logger.error(f"OpenRouter response format unexpected: {result}")
                    return "I received an unexpected response format from the AI service."
            else:
                self.logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                return f"I encountered an error with the AI service (HTTP {response.status_code}). Please try again."
                
        except requests.exceptions.Timeout:
            self.logger.error("OpenRouter API timeout")
            return "The AI service is taking too long to respond. Please try again."
        except Exception as e:
            self.logger.error(f"OpenRouter API exception: {e}")
            return f"I encountered an error: {str(e)}"

    def _fallback_response(self, prompt: str) -> str:
        """Fallback response when LLM fails"""
        return """I found relevant RERA project documents for your query! 

The AI service is currently unavailable. Please check your OpenRouter API configuration.

To configure OpenRouter:
1. Update the 'openrouter_api_key' in the generator configuration
2. Ensure you have sufficient credits in your OpenRouter account
3. Check the model name is correct

For now, you can use the test mode to see the retrieved documents:
python main.py --test --query "your question" """