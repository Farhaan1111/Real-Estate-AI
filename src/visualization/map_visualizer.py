import folium
from folium import plugins
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ProjectMarker:
    """Data class to represent a project marker on the map"""
    project_name: str
    rera_number: str
    latitude: float
    longitude: float
    project_type: str
    completion_date: str
    total_units: int
    promoter: str
    district: str

class SimpleMapVisualizer:
    """
    A simple map visualizer for Real Estate AI system
    Creates interactive Folium maps with project locations
    """
    
    def __init__(self):
        self.default_location = [19.0760, 72.8777]  # Mumbai coordinates
        self.default_zoom = 10
        self.logger = logging.getLogger(__name__)
        
        # Color scheme for different project types
        self.project_type_colors = {
            'Residential': 'green',
            'Commercial': 'blue', 
            'Mixed': 'purple',
            'Residential / Group Housing': 'darkgreen',
            'Unknown': 'gray'
        }
        
        self.logger.info("SimpleMapVisualizer initialized")

    def extract_projects_from_ai_system(self, ai_system) -> List[ProjectMarker]:
        """
        Extract real projects with coordinates from the AI system
        
        Args:
            ai_system: The initialized AI system instance
            
        Returns:
            List[ProjectMarker]: List of projects with coordinates
        """
        projects = []
        
        if not ai_system:
            self.logger.error("AI system not provided")
            return projects
        
        try:
            # Access the vector store documents through the AI system
            if (hasattr(ai_system, 'vector_store') and 
                hasattr(ai_system.vector_store, 'documents')):
                
                documents = ai_system.vector_store.documents
                self.logger.info(f"Processing {len(documents)} documents for map data")
                
                coordinate_chunks = []
                project_registry = {}  # To avoid duplicates
                
                for doc in documents:
                    metadata = doc.get('metadata', {})
                    
                    # Look for documents that have coordinates
                    latitude = metadata.get('latitude')
                    longitude = metadata.get('longitude')
                    project_name = metadata.get('project_name', 'Unknown')
                    rera_number = metadata.get('registration_number', 'Unknown')
                    
                    # Check if this is a geolocation chunk and has valid coordinates
                    if (latitude and longitude and 
                        metadata.get('is_geolocation_chunk') and
                        rera_number != 'Unknown'):
                        
                        # Avoid duplicates by RERA number
                        if rera_number not in project_registry:
                            try:
                                # Convert to float and validate coordinates
                                lat_float = float(latitude)
                                lon_float = float(longitude)
                                
                                # Validate coordinate ranges (India coordinates)
                                if (8.0 <= lat_float <= 37.0 and 68.0 <= lon_float <= 98.0):
                                    project = ProjectMarker(
                                        project_name=project_name,
                                        rera_number=rera_number,
                                        latitude=lat_float,
                                        longitude=lon_float,
                                        project_type=metadata.get('project_type', 'Residential'),
                                        completion_date=metadata.get('completion_date', 'N/A'),
                                        total_units=metadata.get('total_units', 0),
                                        promoter=metadata.get('promoter_name', 'Unknown'),
                                        district=metadata.get('district', 'Unknown')
                                    )
                                    projects.append(project)
                                    project_registry[rera_number] = True
                                    coordinate_chunks.append({
                                        'project': project_name,
                                        'rera': rera_number,
                                        'coords': (lat_float, lon_float)
                                    })
                                    
                            except (ValueError, TypeError) as e:
                                self.logger.warning(f"Invalid coordinates for {project_name}: {e}")
                                continue
                
                self.logger.info(f"Extracted {len(projects)} unique projects with valid coordinates")
                self.logger.info(f"Coordinate chunks found: {coordinate_chunks}")
                
            else:
                self.logger.error("No vector store or documents found in AI system")
                
        except Exception as e:
            self.logger.error(f"Error extracting projects from AI system: {e}")
            
        return projects

    def create_real_map(self, ai_system) -> str:
        """
        Create a map with real project data from the AI system
        
        Args:
            ai_system: The initialized AI system instance
            
        Returns:
            str: HTML representation of the Folium map
        """
        self.logger.info("Creating map with real project data...")
        
        try:
            # Extract real projects from AI system
            real_projects = self.extract_projects_from_ai_system(ai_system)
            
            if real_projects:
                self.logger.info(f"Creating map with {len(real_projects)} real projects")
                return self._create_map_with_projects(real_projects, "Real RERA Projects")
            else:
                self.logger.warning("No real projects found, falling back to test data")
                return self.create_test_map()
            
        except Exception as e:
            self.logger.error(f"Error creating real map: {e}")
            return self.create_test_map()

    def create_test_map(self) -> str:
        """
        Create a simple test map with sample data to verify everything works
        """
        self.logger.info("Creating test map with sample data...")
        sample_projects = self._get_sample_projects()
        return self._create_map_with_projects(sample_projects, "Sample Projects (Test Data)")

    def _create_map_with_projects(self, projects: List[ProjectMarker], title: str) -> str:
        """Internal method to create map with given projects"""
        try:
            # Calculate center based on projects or use default
            if projects:
                avg_lat = sum(p.latitude for p in projects) / len(projects)
                avg_lon = sum(p.longitude for p in projects) / len(projects)
                center = [avg_lat, avg_lon]
                self.logger.info(f"Map center calculated: {center}")
            else:
                center = self.default_location
                self.logger.info("Using default map center")
            
            # Create base map
            m = folium.Map(
                location=center,
                zoom_start=self.default_zoom,
                tiles='OpenStreetMap',
                control_scale=True
            )
            
            # Add title to the map
            self._add_map_title(m, title, len(projects))
            
            # Add project markers
            self._add_markers_to_map(m, projects)
            
            # Add map controls
            self._add_map_controls(m)
            
            # Add custom styles
            self._add_custom_styles(m)
            
            self.logger.info(f"Map created successfully with {len(projects)} projects")
            return m._repr_html_()
            
        except Exception as e:
            self.logger.error(f"Error creating map with projects: {e}")
            return self._create_error_map(f"Failed to create map: {str(e)}")

    def _add_map_title(self, map_obj: folium.Map, title: str, project_count: int):
        """Add a title to the map"""
        title_html = f"""
        <div style="position: absolute; 
                   top: 10px; 
                   left: 50px; 
                   z-index: 1000; 
                   background: rgba(255, 255, 255, 0.95); 
                   padding: 15px 20px; 
                   border-radius: 10px; 
                   box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                   border-left: 4px solid #007bff;
                   font-family: Arial, sans-serif;">
            <h4 style="margin: 0 0 5px 0; color: #2c3e50;">{title}</h4>
            <p style="margin: 0; color: #666; font-size: 14px;">
                <i class="fas fa-map-marker-alt"></i> {project_count} projects displayed
            </p>
        </div>
        """
        map_obj.get_root().html.add_child(folium.Element(title_html))

    def _get_sample_projects(self) -> List[ProjectMarker]:
        """Get sample projects for testing when no real data is available"""
        return [
            ProjectMarker(
                project_name="UNNATHI WOODS PHASE VII A",
                rera_number="P51700000002",
                latitude=19.268511,
                longitude=72.97367,
                project_type="Residential",
                completion_date="2025-12-30",
                total_units=234,
                promoter="UNNATHI ESTATES",
                district="Mumbai Suburban"
            ),
            ProjectMarker(
                project_name="Commercial Complex Mumbai",
                rera_number="TEST001",
                latitude=19.0650,
                longitude=72.8777,
                project_type="Commercial",
                completion_date="2024-12-31", 
                total_units=150,
                promoter="Test Builders",
                district="Mumbai"
            ),
            ProjectMarker(
                project_name="Mixed Use Development",
                rera_number="TEST002", 
                latitude=18.5204,
                longitude=73.8567,
                project_type="Mixed",
                completion_date="2024-06-30",
                total_units=300,
                promoter="Urban Developers",
                district="Pune"
            )
        ]

    def _add_markers_to_map(self, map_obj: folium.Map, projects: List[ProjectMarker]):
        """Add project markers to the map"""
        
        # Create feature groups for different project types
        feature_groups = {}
        for project_type in self.project_type_colors.keys():
            feature_groups[project_type] = folium.FeatureGroup(
                name=project_type, 
                show=True
            )
        
        marker_count = 0
        for project in projects:
            try:
                # Determine color based on project type
                color = self.project_type_colors.get(project.project_type, 'gray')
                
                # Create popup content with project details
                popup_content = self._create_popup_content(project)
                
                # Create marker with custom icon
                marker = folium.Marker(
                    location=[project.latitude, project.longitude],
                    popup=folium.Popup(popup_content, max_width=300, min_width=200),
                    tooltip=self._create_tooltip_content(project),
                    icon=folium.Icon(
                        color=color, 
                        icon='home', 
                        prefix='fa',
                        icon_color='white'
                    )
                )
                
                # Add to appropriate feature group
                feature_group = feature_groups.get(
                    project.project_type, 
                    feature_groups.get('Unknown')
                )
                if feature_group:
                    marker.add_to(feature_group)
                    marker_count += 1
                    
            except Exception as e:
                self.logger.warning(f"Failed to add marker for {project.project_name}: {e}")
                continue
        
        # Add all feature groups to the map
        for feature_group in feature_groups.values():
            feature_group.add_to(map_obj)
            
        self.logger.info(f"Added {marker_count} markers to the map")

    def _create_popup_content(self, project: ProjectMarker) -> str:
        """Create HTML content for map popup"""
        return f"""
        <div style="width: 280px; font-family: Arial, sans-serif;">
            <h4 style="color: #2c3e50; margin-bottom: 10px; border-bottom: 2px solid #3498db; padding-bottom: 5px;">
                {project.project_name}
            </h4>
            <div style="font-size: 12px; line-height: 1.4; color: #555;">
                <p><b>🏢 RERA Number:</b> {project.rera_number}</p>
                <p><b>📊 Project Type:</b> {project.project_type}</p>
                <p><b>👷 Promoter:</b> {project.promoter}</p>
                <p><b>📍 District:</b> {project.district}</p>
                <p><b>🏠 Total Units:</b> {project.total_units}</p>
                <p><b>📅 Completion Date:</b> {project.completion_date}</p>
                <p><b>🌐 Coordinates:</b> {project.latitude:.4f}, {project.longitude:.4f}</p>
            </div>
            <button onclick="window.parent.postMessage({{type: 'PROJECT_SELECTED', reraNumber: '{project.rera_number}'}}, '*')" 
                    style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                           color: white; 
                           border: none; 
                           padding: 8px 16px; 
                           border-radius: 5px; 
                           cursor: pointer; 
                           width: 100%; 
                           margin-top: 10px;
                           font-size: 12px;">
                🔍 Query This Project in AI Chat
            </button>
        </div>
        """

    def _create_tooltip_content(self, project: ProjectMarker) -> str:
        """Create tooltip content for markers"""
        return f"""
        <div style="font-size: 12px;">
            <strong>{project.project_name}</strong><br>
            Type: {project.project_type}<br>
            Units: {project.total_units}<br>
            RERA: {project.rera_number}
        </div>
        """

    def _add_map_controls(self, map_obj: folium.Map):
        """Add controls to the map"""
        # Add layer control
        folium.LayerControl().add_to(map_obj)
        
        # Add fullscreen button
        plugins.Fullscreen().add_to(map_obj)
        
        # Add measure control
        plugins.MeasureControl().add_to(map_obj)

    def _add_custom_styles(self, map_obj: folium.Map):
        """Add custom CSS styles to the map for better appearance"""
        custom_css = """
        <style>
        .leaflet-popup-content-wrapper {
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            border: 2px solid #007bff;
        }
        .leaflet-popup-content {
            margin: 12px 15px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .leaflet-popup-tip {
            border: 2px solid #007bff;
        }
        </style>
        """
        map_obj.get_root().header.add_child(folium.Element(custom_css))

    def _create_error_map(self, error_message: str) -> str:
        """Create a fallback map showing an error message"""
        self.logger.error(f"Creating error map: {error_message}")
        
        try:
            m = folium.Map(
                location=self.default_location,
                zoom_start=self.default_zoom,
                tiles='OpenStreetMap'
            )
            
            error_html = f"""
            <div style="position: absolute; 
                       top: 50px; 
                       left: 50px; 
                       z-index: 1000; 
                       background: rgba(255, 255, 255, 0.95); 
                       padding: 25px; 
                       border-radius: 12px; 
                       box-shadow: 0 4px 20px rgba(0,0,0,0.3); 
                       max-width: 400px;
                       border-left: 5px solid #dc3545;">
                <h4 style="color: #dc3545; margin-bottom: 15px;">
                    <i class="fas fa-exclamation-triangle"></i>
                    Map Error
                </h4>
                <p style="margin-bottom: 20px; color: #666; line-height: 1.5;">
                    {error_message}
                </p>
                <button onclick="window.location.reload()" 
                        style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                               color: white; 
                               border: none; 
                               padding: 10px 20px; 
                               border-radius: 5px; 
                               cursor: pointer;
                               font-weight: bold;">
                    <i class="fas fa-sync-alt"></i> Retry Loading Map
                </button>
            </div>
            """
            
            m.get_root().html.add_child(folium.Element(error_html))
            return m._repr_html_()
            
        except Exception as e:
            self.logger.error(f"Failed to create error map: {e}")
            return f"""
            <div style="padding: 40px; text-align: center; background: #f8d7da; color: #721c24; border-radius: 10px;">
                <h3>❌ Map Loading Failed</h3>
                <p>{error_message}</p>
                <p><small>Please check the console for details.</small></p>
            </div>
            """

    def get_map_config(self) -> Dict[str, Any]:
        """Get map configuration information"""
        return {
            "default_location": self.default_location,
            "default_zoom": self.default_zoom,
            "available_tiles": ["OpenStreetMap", "CartoDB Positron", "CartoDB Dark_Matter"],
            "project_type_colors": self.project_type_colors,
            "version": "1.0.0"
        }