import json
import logging
from typing import Dict, List, Any, Optional

class JSONLProcessor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
   
    def load_jsonl_data(self, file_path: Optional[str] = None) -> List[Dict]:
        """Load JSONL data from file"""
        if file_path is None:
            file_path = self.config['data']['jsonl_file']
       
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = [json.loads(line) for line in f]
            self.logger.info(f"Loaded {len(data)} records from {file_path}")
            return data
        except Exception as e:
            self.logger.error(f"Error loading JSONL data: {e}")
            return []
    
    def _create_geolocation_chunk(self, item: Dict[str, Any], doc_id: str) -> Dict[str, Any]:
        """Create a dedicated chunk for map visualization"""
        area_detail = item.get('project_area_detail', {})
        project_detail = item.get('project_detail', {})
        project_name = project_detail.get('project_name', 'Unknown Project')
        registration_number = project_detail.get('registration_number', 'Unknown')
        
        latitude = area_detail.get('latitude')
        longitude = area_detail.get('longitude')
        
        if latitude and longitude:
            content = f"""
    MAP VISUALIZATION DATA:
    Project: {project_name}
    RERA: {registration_number}
    Latitude: {latitude}
    Longitude: {longitude}
    Coordinates: ({latitude}, {longitude})
    GeoJSON Ready: YES
    """
            return {
                'content': content.strip(),
                'metadata': {
                    'doc_id': doc_id,
                    'chunk_type': 'geolocation',
                    'project_name': project_name,
                    'registration_number': registration_number,
                    'latitude': float(latitude),
                    'longitude': float(longitude),
                    'has_coordinates': True,
                    'is_geolocation_chunk': True
                }
            }
        return None

    def extract_document_chunks(self, data: List[Dict]) -> List[Dict[str, Any]]:
        """Ultra-fine-grained document chunking for micro-details"""
        documents = []
        
        for i, item in enumerate(data):
            doc_id = f"doc_{i}"
            project_name = item.get('project_detail', {}).get('project_name', 'Unknown Project')
            registration_number = item.get('project_detail', {}).get('registration_number', 'Unknown')
            
            self.logger.info(f"Processing project: {project_name} ({registration_number})")
            
            # Create MICRO-level chunks for every possible detail
            chunks = [
                # Registration & Basic Info
                self._create_registration_micro_chunk(item, doc_id),
                self._create_project_status_chunk(item, doc_id),
                self._create_timeline_detailed_chunk(item, doc_id),
                
                # Location - Ultra Detailed
                self._create_geolocation_chunk(item, doc_id),
                self._create_location_micro_chunk(item, doc_id),
                self._create_coordinates_chunk(item, doc_id),
                self._create_boundaries_detailed_chunk(item, doc_id),
                self._create_address_breakdown_chunk(item, doc_id),
                
                # Land & Area - Every measurement
                self._create_land_area_micro_chunk(item, doc_id),
                self._create_plot_details_chunk(item, doc_id),
                self._create_area_breakdown_chunk(item, doc_id),
                
                # Promoter - Detailed
                self._create_promoter_micro_chunk(item, doc_id),
                self._create_promoter_address_chunk(item, doc_id),
                
                # Legal & Financial
                self._create_legal_status_chunk(item, doc_id),
                self._create_financial_details_chunk(item, doc_id),
                self._create_ownership_structure_chunk(item, doc_id),
            ]
            
            # Building-level micro chunks - ONE PER BUILDING
            buildings = item.get('building_details', [])
            for j, building in enumerate(buildings):
                building_chunks = self._create_building_micro_chunks(item, doc_id, building, j)
                chunks.extend(building_chunks)
            
            # Apartment-level micro chunks - ONE PER APARTMENT SUMMARY
            apartments = item.get('apartments_summary', [])
            for k, apt in enumerate(apartments):
                apartment_chunks = self._create_apartment_micro_chunks(item, doc_id, apt, k)
                chunks.extend(apartment_chunks)
            
            # Project-level summaries
            chunks.extend([
                self._create_project_summary_chunk(item, doc_id),
                self._create_quick_facts_chunk(item, doc_id),
                self._create_statistics_chunk(item, doc_id)
            ])
            
            # Add non-empty chunks
            for chunk in chunks:
                if chunk and chunk.get('content', '').strip():
                    documents.append(chunk)
            
            self.logger.info(f"Created {len([c for c in chunks if c])} micro-chunks for project {project_name}")
        
        self.logger.info(f"Created {len(documents)} ULTRA-DETAILED document chunks from {len(data)} projects")
        return documents

    def _create_registration_micro_chunk(self, item: Dict[str, Any], doc_id: str) -> Dict[str, Any]:
        """Micro chunk for registration details"""
        project_detail = item.get('project_detail', {})
        project_name = project_detail.get('project_name', 'Unknown Project')
        registration_number = project_detail.get('registration_number', 'Unknown')
        
        content = f"""
RERA REGISTRATION MICRO-DETAILS:
Project Name: {project_name}
RERA Registration Number: {registration_number}
Registration Date: {project_detail.get('date_of_registration', 'N/A')}
Project Type: {project_detail.get('project_type', 'N/A')}
Project Location: {project_detail.get('project_location', 'N/A')}

EXACT REGISTRATION INFORMATION:
- RERA ID: {registration_number}
- Project Name: {project_name}
- Type: {project_detail.get('project_type', 'N/A')}
- Registration Date: {project_detail.get('date_of_registration', 'N/A')}
- Location: {project_detail.get('project_location', 'N/A')}
- Status: ACTIVE - RERA REGISTERED
"""
        return {
            'content': content.strip(),
            'metadata': {
                'doc_id': doc_id,
                'chunk_type': 'registration_micro',
                'project_name': project_name,
                'registration_number': registration_number,
                'project_type': project_detail.get('project_type', ''),
                'registration_date': project_detail.get('date_of_registration', ''),
                'location': project_detail.get('project_location', ''),
                'is_registration_chunk': True
            }
        }

    def _create_project_status_chunk(self, item: Dict[str, Any], doc_id: str) -> Dict[str, Any]:
        """Chunk for project status details"""
        project_detail = item.get('project_detail', {})
        project_name = project_detail.get('project_name', 'Unknown Project')
        registration_number = project_detail.get('registration_number', 'Unknown')
        
        content = f"""
PROJECT STATUS DETAILS:
Project: {project_name}
RERA: {registration_number}

DEVELOPMENT STATUS:
Multiple Phases: {project_detail.get('is_this_project_being_developed_in_multiple_phases', 'N/A')}
Landowner Type: {project_detail.get('landowner_types_in_the_project', 'N/A')}
External Investors: {project_detail.get('are_there_any_investor_other_than_the_promoter_in_the_project', 'N/A')}

STATUS BREAKDOWN:
- Multiple Phases: {project_detail.get('is_this_project_being_developed_in_multiple_phases', 'N/A')}
- Landowner: {project_detail.get('landowner_types_in_the_project', 'N/A')}
- External Investors: {project_detail.get('are_there_any_investor_other_than_the_promoter_in_the_project', 'N/A')}
- Overall Status: UNDER CONSTRUCTION
"""
        return {
            'content': content.strip(),
            'metadata': {
                'doc_id': doc_id,
                'chunk_type': 'project_status',
                'project_name': project_name,
                'registration_number': registration_number,
                'multiple_phases': project_detail.get('is_this_project_being_developed_in_multiple_phases', ''),
                'landowner_type': project_detail.get('landowner_types_in_the_project', ''),
                'external_investors': project_detail.get('are_there_any_investor_other_than_the_promoter_in_the_project', '')
            }
        }

    def _create_timeline_detailed_chunk(self, item: Dict[str, Any], doc_id: str) -> Dict[str, Any]:
        """Detailed timeline chunk"""
        project_detail = item.get('project_detail', {})
        project_name = project_detail.get('project_name', 'Unknown Project')
        registration_number = project_detail.get('registration_number', 'Unknown')
        
        content = f"""
PROJECT TIMELINE DETAILS:
Project: {project_name}
RERA: {registration_number}

KEY DATES:
Registration Date: {project_detail.get('date_of_registration', 'N/A')}
Original Completion Date: {project_detail.get('proposed_completion_date_original', 'N/A')}
Revised Completion Date: {project_detail.get('proposed_completion_date_revised', 'N/A')}

TIMELINE BREAKDOWN:
- Registered: {project_detail.get('date_of_registration', 'N/A')}
- Original Completion: {project_detail.get('proposed_completion_date_original', 'N/A')}
- Revised Completion: {project_detail.get('proposed_completion_date_revised', 'N/A')}
- Current Status: UNDER CONSTRUCTION
- Timeline Status: {'ON SCHEDULE' if not project_detail.get('proposed_completion_date_revised') else 'REVISED'}
"""
        return {
            'content': content.strip(),
            'metadata': {
                'doc_id': doc_id,
                'chunk_type': 'timeline_detailed',
                'project_name': project_name,
                'registration_number': registration_number,
                'registration_date': project_detail.get('date_of_registration', ''),
                'completion_date': project_detail.get('proposed_completion_date_original', ''),
                'revised_date': project_detail.get('proposed_completion_date_revised', '')
            }
        }

    def _create_location_micro_chunk(self, item: Dict[str, Any], doc_id: str) -> Dict[str, Any]:
        """Micro chunk for location details"""
        area_detail = item.get('project_area_detail', {})
        project_detail = item.get('project_detail', {})
        project_name = project_detail.get('project_name', 'Unknown Project')
        registration_number = project_detail.get('registration_number', 'Unknown')
        
        content = f"""
LOCATION MICRO-DETAILS:
Project: {project_name}
RERA: {registration_number}

GEOGRAPHICAL HIERARCHY:
Country: INDIA
State: {area_detail.get('state_ut', 'N/A')}
District: {area_detail.get('district', 'N/A')}
Taluka: {area_detail.get('taluka', 'N/A')}
Village: {area_detail.get('village', 'N/A')}
PIN Code: {area_detail.get('pin_code', 'N/A')}

EXACT LOCATION COORDINATES:
Latitude: {area_detail.get('latitude', 'N/A')}
Longitude: {area_detail.get('longitude', 'N/A')}
Geo-coordinates: ({area_detail.get('latitude', 'N/A')}, {area_detail.get('longitude', 'N/A')})

LOCATION BREAKDOWN:
- State: {area_detail.get('state_ut', 'N/A')}
- District: {area_detail.get('district', 'N/A')}
- Taluka: {area_detail.get('taluka', 'N/A')}
- Village: {area_detail.get('village', 'N/A')}
- PIN: {area_detail.get('pin_code', 'N/A')}
"""
        return {
            'content': content.strip(),
            'metadata': {
                'doc_id': doc_id,
                'chunk_type': 'location_micro',
                'project_name': project_name,
                'registration_number': registration_number,
                'state': area_detail.get('state_ut', ''),
                'district': area_detail.get('district', ''),
                'taluka': area_detail.get('taluka', ''),
                'village': area_detail.get('village', ''),
                'pincode': area_detail.get('pin_code', ''),
                'latitude': area_detail.get('latitude', ''),
                'longitude': area_detail.get('longitude', ''),
                'is_location_chunk': True
            }
        }

    def _create_coordinates_chunk(self, item: Dict[str, Any], doc_id: str) -> Dict[str, Any]:
        """Dedicated chunk for coordinates only"""
        area_detail = item.get('project_area_detail', {})
        project_detail = item.get('project_detail', {})
        project_name = project_detail.get('project_name', 'Unknown Project')
        registration_number = project_detail.get('registration_number', 'Unknown')
        
        content = f"""
GEOGRAPHICAL COORDINATES:
Project: {project_name}
RERA: {registration_number}
Latitude: {area_detail.get('latitude', 'N/A')}
Longitude: {area_detail.get('longitude', 'N/A')}
GPS Coordinates: ({area_detail.get('latitude', 'N/A')}, {area_detail.get('longitude', 'N/A')})

EXACT COORDINATES:
- Latitude: {area_detail.get('latitude', 'N/A')}
- Longitude: {area_detail.get('longitude', 'N/A')}
- GPS: {area_detail.get('latitude', 'N/A')}, {area_detail.get('longitude', 'N/A')}
"""
        return {
            'content': content.strip(),
            'metadata': {
                'doc_id': doc_id,
                'chunk_type': 'coordinates',
                'project_name': project_name,
                'registration_number': registration_number,
                'latitude': area_detail.get('latitude', ''),
                'longitude': area_detail.get('longitude', ''),
                'is_coordinates_chunk': True
            }
        }

    def _create_boundaries_detailed_chunk(self, item: Dict[str, Any], doc_id: str) -> Dict[str, Any]:
        """Detailed boundaries chunk"""
        area_detail = item.get('project_area_detail', {})
        project_detail = item.get('project_detail', {})
        project_name = project_detail.get('project_name', 'Unknown Project')
        registration_number = project_detail.get('registration_number', 'Unknown')
        
        content = f"""
PROJECT BOUNDARIES DETAILED:
Project: {project_name}
RERA: {registration_number}

BOUNDARY DESCRIPTIONS:
North Boundary: {area_detail.get('boundaries_north', 'N/A')}
South Boundary: {area_detail.get('boundaries_south', 'N/A')}
East Boundary: {area_detail.get('boundaries_east', 'N/A')}
West Boundary: {area_detail.get('boundaries_west', 'N/A')}

COMPLETE BOUNDARY INFORMATION:
- North: {area_detail.get('boundaries_north', 'N/A')}
- South: {area_detail.get('boundaries_south', 'N/A')}
- East: {area_detail.get('boundaries_east', 'N/A')}
- West: {area_detail.get('boundaries_west', 'N/A')}
"""
        return {
            'content': content.strip(),
            'metadata': {
                'doc_id': doc_id,
                'chunk_type': 'boundaries_detailed',
                'project_name': project_name,
                'registration_number': registration_number,
                'north_boundary': area_detail.get('boundaries_north', ''),
                'south_boundary': area_detail.get('boundaries_south', ''),
                'east_boundary': area_detail.get('boundaries_east', ''),
                'west_boundary': area_detail.get('boundaries_west', '')
            }
        }

    def _create_address_breakdown_chunk(self, item: Dict[str, Any], doc_id: str) -> Dict[str, Any]:
        """Address breakdown chunk"""
        area_detail = item.get('project_area_detail', {})
        project_detail = item.get('project_detail', {})
        project_name = project_detail.get('project_name', 'Unknown Project')
        registration_number = project_detail.get('registration_number', 'Unknown')
        
        content = f"""
ADDRESS BREAKDOWN:
Project: {project_name}
RERA: {registration_number}

COMPLETE ADDRESS:
Village: {area_detail.get('village', 'N/A')}
Taluka: {area_detail.get('taluka', 'N/A')}
District: {area_detail.get('district', 'N/A')}
State: {area_detail.get('state_ut', 'N/A')}
PIN Code: {area_detail.get('pin_code', 'N/A')}

ADDRESS FORMAT:
{area_detail.get('village', 'N/A')}, {area_detail.get('taluka', 'N/A')}
{area_detail.get('district', 'N/A')}, {area_detail.get('state_ut', 'N/A')} - {area_detail.get('pin_code', 'N/A')}
"""
        return {
            'content': content.strip(),
            'metadata': {
                'doc_id': doc_id,
                'chunk_type': 'address_breakdown',
                'project_name': project_name,
                'registration_number': registration_number,
                'village': area_detail.get('village', ''),
                'taluka': area_detail.get('taluka', ''),
                'district': area_detail.get('district', ''),
                'state': area_detail.get('state_ut', ''),
                'pincode': area_detail.get('pin_code', '')
            }
        }

    def _create_land_area_micro_chunk(self, item: Dict[str, Any], doc_id: str) -> Dict[str, Any]:
        """Micro chunk for land area details"""
        land_detail = item.get('project_land_area_detail', {})
        project_detail = item.get('project_detail', {})
        project_name = project_detail.get('project_name', 'Unknown Project')
        registration_number = project_detail.get('registration_number', 'Unknown')
        
        content = f"""
LAND AREA MICRO-DETAILS:
Project: {project_name}
RERA: {registration_number}

PLOT INFORMATION:
Final Plot/CTS/Survey Number: {land_detail.get('final_plot_bearing_no_cts_number_survey_number', 'N/A')}

AREA MEASUREMENTS (Square Meters):
Total Approved Layout Area: {land_detail.get('total_land_area_of_approved_layout_sq_mts', 'N/A')} sqm
Land Area for Registration: {land_detail.get('land_area_for_project_applied_for_this_registration_sq_mts', 'N/A')} sqm
Permissible Built-up Area: {land_detail.get('permissible_built_up_area', 'N/A')} sqm
Sanctioned Built-up Area: {land_detail.get('sanctioned_built_up_area_of_the_project_applied_for_registration', 'N/A')} sqm
Recreational Open Space: {land_detail.get('aggregate_area_in_sq_mts_of_recreational_open_space_as_per_layout_dp_remarks', 'N/A')} sqm

EXACT AREA SPECIFICATIONS:
- Plot Number: {land_detail.get('final_plot_bearing_no_cts_number_survey_number', 'N/A')}
- Total Land: {land_detail.get('total_land_area_of_approved_layout_sq_mts', 'N/A')} sqm
- Registered Land: {land_detail.get('land_area_for_project_applied_for_this_registration_sq_mts', 'N/A')} sqm
- Permissible Built-up: {land_detail.get('permissible_built_up_area', 'N/A')} sqm
- Sanctioned Built-up: {land_detail.get('sanctioned_built_up_area_of_the_project_applied_for_registration', 'N/A')} sqm
- Open Space: {land_detail.get('aggregate_area_in_sq_mts_of_recreational_open_space_as_per_layout_dp_remarks', 'N/A')} sqm
"""
        return {
            'content': content.strip(),
            'metadata': {
                'doc_id': doc_id,
                'chunk_type': 'land_area_micro',
                'project_name': project_name,
                'registration_number': registration_number,
                'land_area': land_detail.get('land_area_for_project_applied_for_this_registration_sq_mts', ''),
                'built_up_area': land_detail.get('sanctioned_built_up_area_of_the_project_applied_for_registration', ''),
                'plot_number': land_detail.get('final_plot_bearing_no_cts_number_survey_number', ''),
                'open_space': land_detail.get('aggregate_area_in_sq_mts_of_recreational_open_space_as_per_layout_dp_remarks', ''),
                'is_land_chunk': True
            }
        }

    def _create_plot_details_chunk(self, item: Dict[str, Any], doc_id: str) -> Dict[str, Any]:
        """Plot details chunk"""
        land_detail = item.get('project_land_area_detail', {})
        project_detail = item.get('project_detail', {})
        project_name = project_detail.get('project_name', 'Unknown Project')
        registration_number = project_detail.get('registration_number', 'Unknown')
        
        content = f"""
PLOT DETAILS:
Project: {project_name}
RERA: {registration_number}

PLOT IDENTIFICATION:
Final Plot/CTS/Survey Number: {land_detail.get('final_plot_bearing_no_cts_number_survey_number', 'N/A')}

PLOT INFORMATION:
- Plot Number: {land_detail.get('final_plot_bearing_no_cts_number_survey_number', 'N/A')}
- This is the official land identification number
"""
        return {
            'content': content.strip(),
            'metadata': {
                'doc_id': doc_id,
                'chunk_type': 'plot_details',
                'project_name': project_name,
                'registration_number': registration_number,
                'plot_number': land_detail.get('final_plot_bearing_no_cts_number_survey_number', ''),
                'is_plot_chunk': True
            }
        }

    def _create_area_breakdown_chunk(self, item: Dict[str, Any], doc_id: str) -> Dict[str, Any]:
        """Area breakdown chunk"""
        land_detail = item.get('project_land_area_detail', {})
        project_detail = item.get('project_detail', {})
        project_name = project_detail.get('project_name', 'Unknown Project')
        registration_number = project_detail.get('registration_number', 'Unknown')
        
        content = f"""
AREA BREAKDOWN:
Project: {project_name}
RERA: {registration_number}

AREA COMPARISON:
Total Layout Area: {land_detail.get('total_land_area_of_approved_layout_sq_mts', 'N/A')} sqm
Registered Land Area: {land_detail.get('land_area_for_project_applied_for_this_registration_sq_mts', 'N/A')} sqm
Difference: {float(land_detail.get('total_land_area_of_approved_layout_sq_mts', 0) or 0) - float(land_detail.get('land_area_for_project_applied_for_this_registration_sq_mts', 0) or 0)} sqm

BUILT-UP AREAS:
Permissible: {land_detail.get('permissible_built_up_area', 'N/A')} sqm
Sanctioned: {land_detail.get('sanctioned_built_up_area_of_the_project_applied_for_registration', 'N/A')} sqm
"""
        return {
            'content': content.strip(),
            'metadata': {
                'doc_id': doc_id,
                'chunk_type': 'area_breakdown',
                'project_name': project_name,
                'registration_number': registration_number,
                'total_layout_area': land_detail.get('total_land_area_of_approved_layout_sq_mts', ''),
                'registered_area': land_detail.get('land_area_for_project_applied_for_this_registration_sq_mts', ''),
                'permissible_area': land_detail.get('permissible_built_up_area', ''),
                'sanctioned_area': land_detail.get('sanctioned_built_up_area_of_the_project_applied_for_registration', '')
            }
        }

    def _create_promoter_micro_chunk(self, item: Dict[str, Any], doc_id: str) -> Dict[str, Any]:
        """Micro chunk for promoter details"""
        promoter_details = item.get('promoter_details', {})
        project_detail = item.get('project_detail', {})
        project_name = project_detail.get('project_name', 'Unknown Project')
        registration_number = project_detail.get('registration_number', 'Unknown')
        
        content = f"""
PROMOTER MICRO-DETAILS:
Project: {project_name}
RERA: {registration_number}

PROMOTER INFORMATION:
Promoter Type: {promoter_details.get('promoter_type', 'N/A')}
Promoter Name: {promoter_details.get('name_of_partnership', 'N/A')}

PROMOTER BREAKDOWN:
- Type: {promoter_details.get('promoter_type', 'N/A')}
- Name: {promoter_details.get('name_of_partnership', 'N/A')}
- Entity: {promoter_details.get('name_of_partnership', 'N/A')} ({promoter_details.get('promoter_type', 'N/A')})
"""
        return {
            'content': content.strip(),
            'metadata': {
                'doc_id': doc_id,
                'chunk_type': 'promoter_micro',
                'project_name': project_name,
                'registration_number': registration_number,
                'promoter_name': promoter_details.get('name_of_partnership', ''),
                'promoter_type': promoter_details.get('promoter_type', ''),
                'is_promoter_chunk': True
            }
        }

    def _create_promoter_address_chunk(self, item: Dict[str, Any], doc_id: str) -> Dict[str, Any]:
        """Promoter address chunk"""
        promoter_address = item.get('promoter_official_communication_address', {})
        project_detail = item.get('project_detail', {})
        project_name = project_detail.get('project_name', 'Unknown Project')
        registration_number = project_detail.get('registration_number', 'Unknown')
        
        content = f"""
PROMOTER ADDRESS:
Project: {project_name}
RERA: {registration_number}

COMMUNICATION ADDRESS:
Unit Number: {promoter_address.get('unit_number', 'N/A')}
Building Name: {promoter_address.get('building_name', 'N/A')}
Street Name: {promoter_address.get('street_name', 'N/A')}
Locality: {promoter_address.get('locality', 'N/A')}
Landmark: {promoter_address.get('landmark', 'N/A')}
State: {promoter_address.get('state_ut', 'N/A')}
District: {promoter_address.get('district', 'N/A')}
Taluka: {promoter_address.get('taluka', 'N/A')}
Village: {promoter_address.get('village', 'N/A')}
PIN Code: {promoter_address.get('pin_code', 'N/A')}

COMPLETE ADDRESS:
{promoter_address.get('unit_number', '')} {promoter_address.get('building_name', '')}
{promoter_address.get('street_name', '')}, {promoter_address.get('locality', '')}
Landmark: {promoter_address.get('landmark', '')}
{promoter_address.get('village', '')}, {promoter_address.get('taluka', '')}
{promoter_address.get('district', '')}, {promoter_address.get('state_ut', '')} - {promoter_address.get('pin_code', '')}
"""
        return {
            'content': content.strip(),
            'metadata': {
                'doc_id': doc_id,
                'chunk_type': 'promoter_address',
                'project_name': project_name,
                'registration_number': registration_number,
                'promoter_building': promoter_address.get('building_name', ''),
                'promoter_street': promoter_address.get('street_name', ''),
                'promoter_locality': promoter_address.get('locality', ''),
                'promoter_district': promoter_address.get('district', ''),
                'promoter_state': promoter_address.get('state_ut', '')
            }
        }

    def _create_legal_status_chunk(self, item: Dict[str, Any], doc_id: str) -> Dict[str, Any]:
        """Legal status chunk"""
        project_detail = item.get('project_detail', {})
        project_name = project_detail.get('project_name', 'Unknown Project')
        registration_number = project_detail.get('registration_number', 'Unknown')
        
        content = f"""
LEGAL STATUS:
Project: {project_name}
RERA: {registration_number}

LEGAL COMPLIANCE:
Litigation Status: {project_detail.get('is_there_any_litigation_against_this_proposed_project', 'N/A')}
Multiple Phases: {project_detail.get('is_this_project_being_developed_in_multiple_phases', 'N/A')}

LEGAL BREAKDOWN:
- Litigation: {project_detail.get('is_there_any_litigation_against_this_proposed_project', 'N/A')}
- Multiple Phases: {project_detail.get('is_this_project_being_developed_in_multiple_phases', 'N/A')}
- RERA Status: REGISTERED
"""
        return {
            'content': content.strip(),
            'metadata': {
                'doc_id': doc_id,
                'chunk_type': 'legal_status',
                'project_name': project_name,
                'registration_number': registration_number,
                'litigation_status': project_detail.get('is_there_any_litigation_against_this_proposed_project', ''),
                'multiple_phases': project_detail.get('is_this_project_being_developed_in_multiple_phases', '')
            }
        }

    def _create_financial_details_chunk(self, item: Dict[str, Any], doc_id: str) -> Dict[str, Any]:
        """Financial details chunk"""
        project_detail = item.get('project_detail', {})
        project_name = project_detail.get('project_name', 'Unknown Project')
        registration_number = project_detail.get('registration_number', 'Unknown')
        
        content = f"""
FINANCIAL DETAILS:
Project: {project_name}
RERA: {registration_number}

FINANCIAL STATUS:
Financial Encumbrance: {project_detail.get('do_you_have_financial_encumberance', 'N/A')}

FINANCIAL BREAKDOWN:
- Financial Encumbrance: {project_detail.get('do_you_have_financial_encumberance', 'N/A')}
- Status: {'NO FINANCIAL ENCUMBRANCE' if project_detail.get('do_you_have_financial_encumberance') == False else 'HAS FINANCIAL ENCUMBRANCE'}
"""
        return {
            'content': content.strip(),
            'metadata': {
                'doc_id': doc_id,
                'chunk_type': 'financial_details',
                'project_name': project_name,
                'registration_number': registration_number,
                'financial_encumbrance': project_detail.get('do_you_have_financial_encumberance', ''),
                'is_financial_chunk': True
            }
        }

    def _create_ownership_structure_chunk(self, item: Dict[str, Any], doc_id: str) -> Dict[str, Any]:
        """Ownership structure chunk"""
        project_detail = item.get('project_detail', {})
        project_name = project_detail.get('project_name', 'Unknown Project')
        registration_number = project_detail.get('registration_number', 'Unknown')
        
        content = f"""
OWNERSHIP STRUCTURE:
Project: {project_name}
RERA: {registration_number}

OWNERSHIP DETAILS:
Landowner Types: {project_detail.get('landowner_types_in_the_project', 'N/A')}
External Investors: {project_detail.get('are_there_any_investor_other_than_the_promoter_in_the_project', 'N/A')}

OWNERSHIP BREAKDOWN:
- Landowner: {project_detail.get('landowner_types_in_the_project', 'N/A')}
- External Investors: {project_detail.get('are_there_any_investor_other_than_the_promoter_in_the_project', 'N/A')}
- Structure: {project_detail.get('landowner_types_in_the_project', 'N/A')} with {'external investors' if project_detail.get('are_there_any_investor_other_than_the_promoter_in_the_project') else 'no external investors'}
"""
        return {
            'content': content.strip(),
            'metadata': {
                'doc_id': doc_id,
                'chunk_type': 'ownership_structure',
                'project_name': project_name,
                'registration_number': registration_number,
                'landowner_type': project_detail.get('landowner_types_in_the_project', ''),
                'external_investors': project_detail.get('are_there_any_investor_other_than_the_promoter_in_the_project', '')
            }
        }

    def _create_building_micro_chunks(self, item: Dict[str, Any], doc_id: str, building: Dict, index: int) -> List[Dict[str, Any]]:
        """Create multiple micro-chunks for a single building"""
        project_detail = item.get('project_detail', {})
        project_name = project_detail.get('project_name', 'Unknown Project')
        registration_number = project_detail.get('registration_number', 'Unknown')
        building_name = building.get('identification_of_building_wing_as_per_sanctioned_plan', f'Building_{index+1}')
        
        chunks = []
        
        # Chunk 1: Building Basic Info
        chunks.append({
            'content': f"""
BUILDING BASIC INFORMATION:
Project: {project_name}
RERA: {registration_number}
Building Name: {building_name}
Building Index: {index + 1}
Wing: {building.get('identification_of_wing_as_per_sanctioned_plan', 'N/A')}

BUILDING IDENTIFICATION:
- Name: {building_name}
- Wing: {building.get('identification_of_wing_as_per_sanctioned_plan', 'N/A')}
- Number: {index + 1}
""".strip(),
            'metadata': {
                'doc_id': doc_id,
                'chunk_type': 'building_basic',
                'project_name': project_name,
                'registration_number': registration_number,
                'building_name': building_name,
                'building_index': index,
                'wing': building.get('identification_of_wing_as_per_sanctioned_plan', ''),
                'is_building_chunk': True
            }
        })
        
        # Chunk 2: Building Structure & Floors
        chunks.append({
            'content': f"""
BUILDING STRUCTURE DETAILS:
Project: {project_name}
Building: {building_name}

FLOOR INFORMATION:
Total Floors (including basement/stilt): {building.get('number_of_sanctioned_floors_including_basement_stilt_podium_service_habitable_excluding_terrace', 'N/A')}
Habitable Floors Only: {building.get('total_no_of_building_sanctioned_habitable_floor', 'N/A')}

FLOOR BREAKDOWN:
- Total Floors: {building.get('number_of_sanctioned_floors_including_basement_stilt_podium_service_habitable_excluding_terrace', 'N/A')}
- Habitable Floors: {building.get('total_no_of_building_sanctioned_habitable_floor', 'N/A')}
- Includes basement/stilt/podium: YES
""".strip(),
            'metadata': {
                'doc_id': doc_id,
                'chunk_type': 'building_structure',
                'project_name': project_name,
                'registration_number': registration_number,
                'building_name': building_name,
                'total_floors': building.get('number_of_sanctioned_floors_including_basement_stilt_podium_service_habitable_excluding_terrace', ''),
                'habitable_floors': building.get('total_no_of_building_sanctioned_habitable_floor', ''),
                'is_building_chunk': True
            }
        })
        
        # Chunk 3: Building Units & Construction
        chunks.append({
            'content': f"""
BUILDING UNITS & CONSTRUCTION:
Project: {project_name}
Building: {building_name}

UNIT COUNT:
Sanctioned Apartments/Units: {building.get('sanctioned_apartments_unit_nrr', 'N/A')}

CONSTRUCTION STATUS:
Construction Complete Up To: {building.get('cc_issued_upto_no_of_floors', 'N/A')}

CONSTRUCTION PROGRESS:
- Total Units: {building.get('sanctioned_apartments_unit_nrr', 'N/A')}
- CC Issued Up To: {building.get('cc_issued_upto_no_of_floors', 'N/A')}
- Construction Status: IN PROGRESS
""".strip(),
            'metadata': {
                'doc_id': doc_id,
                'chunk_type': 'building_units',
                'project_name': project_name,
                'registration_number': registration_number,
                'building_name': building_name,
                'building_units': building.get('sanctioned_apartments_unit_nrr', ''),
                'construction_status': building.get('cc_issued_upto_no_of_floors', ''),
                'is_building_chunk': True
            }
        })
        
        return chunks

    def _create_apartment_micro_chunks(self, item: Dict[str, Any], doc_id: str, apartment: Dict, index: int) -> List[Dict[str, Any]]:
        """Create multiple micro-chunks for apartment summary"""
        project_detail = item.get('project_detail', {})
        project_name = project_detail.get('project_name', 'Unknown Project')
        registration_number = project_detail.get('registration_number', 'Unknown')
        building_name = apartment.get('identification_of_building_wing_as_per_sanctioned_plan', f'Building_{index+1}')
        
        chunks = []
        
        # Chunk 1: Apartment Basic Info
        chunks.append({
            'content': f"""
APARTMENT SUMMARY BASIC:
Project: {project_name}
RERA: {registration_number}
Building: {building_name}
Wing: {apartment.get('identification_of_wing_as_per_sanctioned_plan', 'N/A')}
Summary Index: {index + 1}

APARTMENT IDENTIFICATION:
- Building: {building_name}
- Wing: {apartment.get('identification_of_wing_as_per_sanctioned_plan', 'N/A')}
- Floor Type: {apartment.get('floor_type', 'N/A')}
""".strip(),
            'metadata': {
                'doc_id': doc_id,
                'chunk_type': 'apartment_basic',
                'project_name': project_name,
                'registration_number': registration_number,
                'building_name': building_name,
                'wing': apartment.get('identification_of_wing_as_per_sanctioned_plan', ''),
                'floor_type': apartment.get('floor_type', ''),
                'is_apartment_chunk': True
            }
        })
        
        # Chunk 2: Apartment Unit Counts
        chunks.append({
            'content': f"""
APARTMENT UNIT COUNTS:
Project: {project_name}
Building: {building_name}

UNIT TYPE BREAKDOWN:
Residential Units: {apartment.get('total_no_of_residential_apartments_units', 'N/A')}
Commercial Units: {apartment.get('total_no_of_nonresidential_apartments_units', 'N/A')}
Total Units: {apartment.get('total_apartments_unit_nrr', 'N/A')}

UNIT DISTRIBUTION:
- Residential: {apartment.get('total_no_of_residential_apartments_units', 'N/A')}
- Commercial: {apartment.get('total_no_of_nonresidential_apartments_units', 'N/A')}
- Total: {apartment.get('total_apartments_unit_nrr', 'N/A')}
""".strip(),
            'metadata': {
                'doc_id': doc_id,
                'chunk_type': 'apartment_units',
                'project_name': project_name,
                'registration_number': registration_number,
                'building_name': building_name,
                'residential_units': apartment.get('total_no_of_residential_apartments_units', ''),
                'commercial_units': apartment.get('total_no_of_nonresidential_apartments_units', ''),
                'total_units': apartment.get('total_apartments_unit_nrr', ''),
                'is_apartment_chunk': True
            }
        })
        
        # Chunk 3: Apartment Sales Status
        chunks.append({
            'content': f"""
APARTMENT SALES STATUS:
Project: {project_name}
Building: {building_name}

SALES INVENTORY:
Sold Units: {apartment.get('total_no_of_sold_units', 'N/A')}
Unsold Units: {apartment.get('total_no_of_unsold_units', 'N/A')}
Rehabilitation Units: {apartment.get('total_no_of_rehab_units', 'N/A')}

SALES BREAKDOWN:
- Sold: {apartment.get('total_no_of_sold_units', 'N/A')}
- Unsold: {apartment.get('total_no_of_unsold_units', 'N/A')}
- Rehab: {apartment.get('total_no_of_rehab_units', 'N/A')}
- Available for Sale: {apartment.get('total_no_of_unsold_units', 'N/A')}
""".strip(),
            'metadata': {
                'doc_id': doc_id,
                'chunk_type': 'apartment_sales',
                'project_name': project_name,
                'registration_number': registration_number,
                'building_name': building_name,
                'sold_units': apartment.get('total_no_of_sold_units', ''),
                'unsold_units': apartment.get('total_no_of_unsold_units', ''),
                'rehab_units': apartment.get('total_no_of_rehab_units', ''),
                'is_apartment_chunk': True
            }
        })
        
        # Chunk 4: Apartment Additional Status
        chunks.append({
            'content': f"""
APARTMENT ADDITIONAL STATUS:
Project: {project_name}
Building: {building_name}

OTHER STATUSES:
Booked Units: {apartment.get('total_no_of_booked', 'N/A')}
Mortgage Units: {apartment.get('total_no_of_mortgage', 'N/A')}
Reservation Units: {apartment.get('total_no_of_reservation', 'N/A')}
Land Owner Shares for Sale: {apartment.get('total_no_of_land_owner_investor_share_for_sale', 'N/A')}
Land Owner Shares Not for Sale: {apartment.get('total_no_of_land_owner_investor_share_not_for_sale', 'N/A')}

STATUS BREAKDOWN:
- Booked: {apartment.get('total_no_of_booked', 'N/A')}
- Mortgage: {apartment.get('total_no_of_mortgage', 'N/A')}
- Reservation: {apartment.get('total_no_of_reservation', 'N/A')}
- Land Owner Sale: {apartment.get('total_no_of_land_owner_investor_share_for_sale', 'N/A')}
- Land Owner No Sale: {apartment.get('total_no_of_land_owner_investor_share_not_for_sale', 'N/A')}
""".strip(),
            'metadata': {
                'doc_id': doc_id,
                'chunk_type': 'apartment_status',
                'project_name': project_name,
                'registration_number': registration_number,
                'building_name': building_name,
                'booked_units': apartment.get('total_no_of_booked', ''),
                'mortgage_units': apartment.get('total_no_of_mortgage', ''),
                'reservation_units': apartment.get('total_no_of_reservation', ''),
                'is_apartment_chunk': True
            }
        })
        
        return chunks

    def _create_project_summary_chunk(self, item: Dict[str, Any], doc_id: str) -> Dict[str, Any]:
        """Project summary chunk"""
        project_detail = item.get('project_detail', {})
        buildings = item.get('building_details', [])
        apartments = item.get('apartments_summary', [])
        area_detail = item.get('project_area_detail', {})
        
        total_units = sum(int(apt.get('total_apartments_unit_nrr', 0)) for apt in apartments if apt.get('total_apartments_unit_nrr'))
        
        content = f"""
PROJECT SUMMARY:
Project: {project_detail.get('project_name', 'N/A')}
RERA: {project_detail.get('registration_number', 'N/A')}

OVERVIEW:
Type: {project_detail.get('project_type', 'N/A')}
Location: {area_detail.get('district', 'N/A')}, {area_detail.get('state_ut', 'N/A')}
Buildings: {len(buildings)}
Total Units: {total_units}
Completion: {project_detail.get('proposed_completion_date_original', 'N/A')}

SUMMARY STATS:
- Project Type: {project_detail.get('project_type', 'N/A')}
- Location: {area_detail.get('village', 'N/A')}, {area_detail.get('district', 'N/A')}
- Buildings: {len(buildings)}
- Total Units: {total_units}
- Status: UNDER CONSTRUCTION
"""
        return {
            'content': content.strip(),
            'metadata': {
                'doc_id': doc_id,
                'chunk_type': 'project_summary',
                'project_name': project_detail.get('project_name', ''),
                'registration_number': project_detail.get('registration_number', ''),
                'num_buildings': len(buildings),
                'total_units': total_units,
                'district': area_detail.get('district', ''),
                'is_summary_chunk': True
            }
        }

    def _create_quick_facts_chunk(self, item: Dict[str, Any], doc_id: str) -> Dict[str, Any]:
        """Quick facts chunk for overview"""
        project_detail = item.get('project_detail', {})
        buildings = item.get('building_details', [])
        apartments = item.get('apartments_summary', [])
        area_detail = item.get('project_area_detail', {})
        
        total_units = sum(int(apt.get('total_apartments_unit_nrr', 0)) for apt in apartments if apt.get('total_apartments_unit_nrr'))
        
        content = f"""
QUICK FACTS:
Project: {project_detail.get('project_name', 'N/A')}
RERA: {project_detail.get('registration_number', 'N/A')}
Buildings: {len(buildings)}
Total Units: {total_units}
Type: {project_detail.get('project_type', 'N/A')}
Location: {area_detail.get('district', 'N/A')}
Completion: {project_detail.get('proposed_completion_date_original', 'N/A')}

KEY FACTS:
- Name: {project_detail.get('project_name', 'N/A')}
- RERA: {project_detail.get('registration_number', 'N/A')}
- Buildings: {len(buildings)}
- Units: {total_units}
- Location: {area_detail.get('district', 'N/A')}
- Completion: {project_detail.get('proposed_completion_date_original', 'N/A')}
"""
        return {
            'content': content.strip(),
            'metadata': {
                'doc_id': doc_id,
                'chunk_type': 'quick_facts',
                'project_name': project_detail.get('project_name', ''),
                'registration_number': project_detail.get('registration_number', ''),
                'num_buildings': len(buildings),
                'total_units': total_units,
                'district': area_detail.get('district', ''),
                'is_summary_chunk': True
            }
        }

    def _create_statistics_chunk(self, item: Dict[str, Any], doc_id: str) -> Dict[str, Any]:
        """Statistics chunk"""
        project_detail = item.get('project_detail', {})
        buildings = item.get('building_details', [])
        apartments = item.get('apartments_summary', [])
        
        total_units = sum(int(apt.get('total_apartments_unit_nrr', 0)) for apt in apartments if apt.get('total_apartments_unit_nrr'))
        total_residential = sum(int(apt.get('total_no_of_residential_apartments_units', 0)) for apt in apartments if apt.get('total_no_of_residential_apartments_units'))
        total_commercial = sum(int(apt.get('total_no_of_nonresidential_apartments_units', 0)) for apt in apartments if apt.get('total_no_of_nonresidential_apartments_units'))
        
        content = f"""
PROJECT STATISTICS:
Project: {project_detail.get('project_name', 'N/A')}
RERA: {project_detail.get('registration_number', 'N/A')}

STATISTICAL BREAKDOWN:
Total Buildings: {len(buildings)}
Total Units: {total_units}
Residential Units: {total_residential}
Commercial Units: {total_commercial}

NUMERICAL SUMMARY:
- Buildings: {len(buildings)}
- Total Units: {total_units}
- Residential: {total_residential}
- Commercial: {total_commercial}
- Residential %: {round((total_residential/total_units)*100, 2) if total_units > 0 else 0}%
- Commercial %: {round((total_commercial/total_units)*100, 2) if total_units > 0 else 0}%
"""
        return {
            'content': content.strip(),
            'metadata': {
                'doc_id': doc_id,
                'chunk_type': 'statistics',
                'project_name': project_detail.get('project_name', ''),
                'registration_number': project_detail.get('registration_number', ''),
                'num_buildings': len(buildings),
                'total_units': total_units,
                'residential_units': total_residential,
                'commercial_units': total_commercial,
                'is_statistics_chunk': True
            }
        }