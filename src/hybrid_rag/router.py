from typing import Dict, Any, List
import re
import logging
from datetime import datetime

class QueryRouter:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.routing_threshold = config['adaptive_rag']['routing_threshold']
        self.logger = logging.getLogger(__name__)
        
        # Comprehensive query patterns for ALL categories
        self.query_patterns = {
            'micro_details': {
                'specific_numbers': r'\b(how many|what is|number of|count of|total)\b.*\b(floors?|units?|apartments?|buildings?|area|sqm|meters?)\b',
                'exact_values': r'\b(exactly|precisely|specifically|detail|details?)\b',
                'individual_items': r'\b(each|every|individual|specific|particular)\b.*\b(building|wing|floor|unit)\b',
                'measurement_queries': r'\b(measurement|dimension|size|area|sqm|square meters?)\b',
            },
            
            # 📍 Location Micro-Queries
            'location_micro': {
                'coordinate_queries': r'\b(latitude|longitude|coordinates?|gps|location pin)\b',
                'address_queries': r'\b(address|exact location|where exactly|precise location)\b',
                'boundary_queries': r'\b(boundaries?|north|south|east|west|surrounding)\b',
            },
            
            # 🏗️ Structural Micro-Queries  
            'structural_micro': {
                'floor_queries': r'\b(floors?|storeys?|levels?|basement|stilt|podium)\b',
                'building_specific': r'\b(building|tower|wing)\b.*\b(\w+)\b',
                'construction_queries': r'\b(construction|completion|progress|status|cc issued)\b',
            },

            # 🏗️ Project Identification
            'project_identification': {
                'rera_id': r'[A-Z]{2}\d{13}',
                'project_name': r'"(.*?)"|\b(MAULI DARSHAN|Guru Vedas Residency|Sai Dhaam|GOLDEN HEIGHTS|Oxyzen|15th Street Avenue|CHAITANYA|Birla Punya|Sigma Amber|New Dwarka)\b',
                'partial_name': r'project.*\b(\w+)\b|show.*projects.*\b(\w+)\b',
                'project_type': r'\b(residential|commercial|mixed|mixed.use)\b',
                'status': r'\b(completed|ongoing|new|under.construction|ready|possession)\b'
            },
            
            # 📅 Timeline & Registration
            'temporal': {
                'registration_date': r'registered.*(202[0-9])|registration.*date',
                'completion_date': r'completion.*(202[0-9])|complete.*by|possession.*date',
                'date_range': r'after.*(202[0-9])|before.*(202[0-9])|between.*(202[0-9]).*(202[0-9])',
                'recent': r'recent|new|latest|just.*registered',
                'extended': r'extended|delayed|revised.*date',
                'expiring': r'expiring|nearing.*completion|upcoming'
            },
            
            # 📍 Location-Based
            'location': {
                'district': r'\b(Mumbai|Pune|Thane|Nashik|Raigarh|Mumbai Suburban|Pune City)\b',
                'taluka': r'\b(Panvel|Gadhinglaj|Shahapur|Borivali)\b',
                'pincode': r'\b(410206|422004|421601|400098|411009|400092|411001)\b',
                'coordinates': r'coordinates?|latitude|longitude|GPS|lat.*long',
                'proximity': r'near|close to|within.*radius|distance.*from',
                'region': r'\b(east|west|north|south|central)\b'
            },
            
            # 🧱 Building & Structural
            'structural': {
                'floors': r'floors?|storeys?|levels?',
                'buildings': r'buildings?|towers?|wings?',
                'phases': r'phase|stage',
                'basement': r'basement|stilt|podium',
                'multi_tower': r'multi.*tower|multiple.*building'
            },
            
            # 🏠 Apartment & Unit
            'units': {
                'sold': r'sold|booked|occupied',
                'unsold': r'unsold|available|vacant',
                'commercial': r'commercial|shop|office|retail',
                'residential': r'residential|flat|apartment|1BHK|2BHK|3BHK',
                'rehab': r'rehab|reserved',
                'sold_out': r'sold.*out|fully.*sold'
            },
            
            # 🧭 Land & Plot
            'land': {
                'area': r'area|sqm|square.*meters|built.up|builtup',
                'plot': r'plot|survey|CTS|FP.*number',
                'open_space': r'open.*space|garden|recreational',
                'land_area': r'land.*area',
                'built_up': r'built.*up.*area|sanctioned.*area'
            },
            
            # 🧑‍💼 Promoter & Ownership
            'promoter': {
                'promoter_name': r'\b(Guru Sai Developer|GM Infrastructure|Sai Construction|S Square Landmark|OVK CO OPERATIVE HOUSING SOCIETY LIMITED)\b',
                'promoter_type': r'company|individual|LLP|partnership|society|co.operative',
                'multiple_projects': r'multiple.*projects|all.*projects.*by',
                'promoter_address': r'promoter.*address|builder.*contact'
            },
            
            # ⚖️ Legal & Financial
            'legal': {
                'litigation': r'litigation|dispute|case|court',
                'financial': r'financial|encumbrance|mortgage|loan',
                'extension': r'extension|revised|delayed|extended',
                'noc': r'NOC|permission|approval'
            },
            
            # 🔍 Analytical & Comparative
            'analytical': {
                'compare': r'compare|versus|vs|difference.*between',
                'ranking': r'rank|top|best|largest|biggest|highest',
                'statistics': r'average|total|count|how many|sum|aggregate',
                'trends': r'trend|analysis|over time|yearly|monthly',
                'distribution': r'distribution|share|percentage'
            },
            
            # 💬 Conversational
            'conversational': {
                'greeting': r'hello|hi|hey|good morning|good afternoon',
                'help': r'help|support|what can you do',
                'thanks': r'thank|thanks',
                'goodbye': r'bye|goodbye|see you'
            },
            
            # 🧮 Numeric & Filters
            'numeric': {
                'greater_than': r'more than|greater than|above|over',
                'less_than': r'less than|below|under',
                'range': r'between.*and',
                'top_n': r'top \d+|first \d+'
            }
        }

    def classify_query(self, query: str) -> str:
        """Simple query classification (backward compatibility)"""
        classification = self.classify_query_comprehensive(query)
        return classification['primary_type']

    def classify_query_comprehensive(self, query: str) -> Dict[str, Any]:
        """Comprehensive query classification for ALL categories"""
        query_lower = query.lower().strip()
        
        classification = {
            'primary_type': 'simple',  # exact, simple, complex, conversational
            'categories': [],
            'entities': {},
            'intent': 'information_retrieval',
            'complexity_score': 0
        }
        
        # Detect specific categories
        categories_detected = []
        entities_extracted = {}
        
        # Check each category pattern
        for category_name, patterns in self.query_patterns.items():
            if self._detect_pattern(query, patterns):
                categories_detected.append(category_name)
                
                # Extract entities for this category
                category_entities = self._extract_category_entities(query, category_name, patterns)
                entities_extracted.update(category_entities)
        
        # Determine primary type based on complexity
        complexity_factors = {
            'analytical': 2,
            'numeric': 1,
            'compare': 2,
            'multiple_categories': len(categories_detected) >= 2
        }
        
        complexity_score = sum(complexity_factors.get(cat, 0) for cat in categories_detected)
        if complexity_factors['multiple_categories']:
            complexity_score += 1
        
        # Set primary type
        if any(term in query_lower for term in ['hello', 'hi', 'hey', 'thank', 'bye']):
            classification['primary_type'] = 'conversational'
        elif complexity_score >= 2 or 'analytical' in categories_detected:
            classification['primary_type'] = 'complex'
        elif self._is_exact_match(query):
            classification['primary_type'] = 'exact'
        elif categories_detected:
            classification['primary_type'] = 'simple'
        else:
            classification['primary_type'] = 'conversational'
        
        classification['categories'] = categories_detected
        classification['entities'] = entities_extracted
        classification['complexity_score'] = complexity_score
        
        return classification

    def _detect_pattern(self, query: str, patterns: Dict) -> bool:
        """Detect if any pattern matches the query"""
        for pattern in patterns.values():
            if re.search(pattern, query, re.IGNORECASE):
                return True
        return False

    def _extract_category_entities(self, query: str, category: str, patterns: Dict) -> Dict:
        """Extract entities for specific category"""
        entities = {}
        
        if category == 'project_identification':
            # Extract RERA IDs
            rera_matches = re.findall(patterns['rera_id'], query)
            if rera_matches:
                entities['rera_ids'] = rera_matches
            
            # Extract project names
            name_matches = re.findall(patterns['project_name'], query, re.IGNORECASE)
            if name_matches:
                entities['project_names'] = [match[0] if match[0] else match[1] for match in name_matches if any(match)]
        
        elif category == 'temporal':
            # Extract years
            year_matches = re.findall(r'20[0-9]{2}', query)
            if year_matches:
                entities['years'] = year_matches
            
            # Extract date ranges
            range_match = re.search(r'between.*(20[0-9]{2}).*(20[0-9]{2})', query, re.IGNORECASE)
            if range_match:
                entities['date_range'] = [range_match.group(1), range_match.group(2)]
        
        elif category == 'location':
            # Extract districts
            district_matches = re.findall(patterns['district'], query, re.IGNORECASE)
            if district_matches:
                entities['districts'] = district_matches
            
            # Extract pincodes
            pincode_matches = re.findall(patterns['pincode'], query)
            if pincode_matches:
                entities['pincodes'] = pincode_matches
        
        elif category == 'numeric':
            # Extract numbers for filters
            number_matches = re.findall(r'\b(\d+)\b', query)
            if number_matches:
                entities['numbers'] = [int(num) for num in number_matches]
            
            # Extract top N
            top_match = re.search(r'top (\d+)', query, re.IGNORECASE)
            if top_match:
                entities['top_n'] = int(top_match.group(1))
        
        return entities

    def _is_exact_match(self, query: str) -> bool:
        """Check for exact match patterns"""
        query_clean = query.upper().strip()
        
        # RERA registration numbers
        if re.search(self.query_patterns['project_identification']['rera_id'], query_clean):
            return True
        
        # Specific project names
        if re.search(self.query_patterns['project_identification']['project_name'], query_clean):
            return True
        
        # Quoted phrases
        if '"' in query:
            return True
        
        return False

    def get_retrieval_params(self, query: str) -> Dict[str, Any]:
        """Enhanced for micro-detail queries"""
        classification = self.classify_query_comprehensive(query)
        categories = classification['categories']
        
        base_params = {
            'k': 15,  # Get more chunks for micro-details
            'score_threshold': 0.15,  # Very low threshold
            'query_expansion': True,
            'dense_weight': 0.6,  # Prefer semantic understanding for details
            'sparse_weight': 0.4,
            'force_sparse': False
        }
        
        # Micro-detail queries need maximum recall
        if any(cat in categories for cat in ['micro_details', 'structural_micro', 'location_micro']):
            base_params.update({
                'k': 20,
                'score_threshold': 0.1,  # Extremely low threshold
                'dense_weight': 0.8,  # Heavy dense weighting for semantic understanding
                'sparse_weight': 0.2
            })
        
        return base_params

    def should_use_rag(self, query: str, conversation_history: List[Dict] = None) -> bool:
        """Determine if RAG should be used for this query"""
        classification = self.classify_query_comprehensive(query)
        primary_type = classification['primary_type']
        
        # Always use RAG for these types
        if primary_type in ['exact', 'simple', 'complex']:
            return True
        
        # For conversational queries, use RAG only if there's relevant context
        if primary_type == 'conversational':
            if conversation_history:
                last_query = conversation_history[-1].get('query', '')
                last_classification = self.classify_query_comprehensive(last_query)
                if last_classification['primary_type'] in ['exact', 'simple', 'complex']:
                    return True  # Continue RAG context
            return False  # Pure conversational, no RAG
        
        return True  # Default to using RAG