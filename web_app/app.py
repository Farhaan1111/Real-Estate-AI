from flask import Flask, render_template, request, jsonify, session
import os
import sys
import json
from datetime import datetime

# Add the project root to path and get absolute path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

app = Flask(__name__)
app.secret_key = 'real-estate-ai-secret-key-2024'

# Initialize the AI system
ai_system = None
system_initialized = False
initialization_error = None

# Initialize Map Visualizer
map_visualizer = None
MAPS_AVAILABLE = False

def initialize_map_visualizer():
    """Initialize the map visualizer with error handling"""
    global map_visualizer, MAPS_AVAILABLE
    
    try:
        # Try to import and initialize map visualizer
        from src.visualization.map_visualizer import SimpleMapVisualizer
        map_visualizer = SimpleMapVisualizer()
        MAPS_AVAILABLE = True
        print("✅ Map visualizer initialized successfully")
        return True
    except ImportError as e:
        print(f"⚠️ Map visualizer not available: {e}")
        MAPS_AVAILABLE = False
        return False
    except Exception as e:
        print(f"⚠️ Error initializing map visualizer: {e}")
        MAPS_AVAILABLE = False
        return False

def initialize_ai_system():
    """Initialize the AI system with comprehensive error handling"""
    global ai_system, system_initialized, initialization_error
    
    try:
        from main import RealEstateAI
        
        # Use absolute path to config
        config_path = os.path.join(project_root, 'config', 'config.yaml')
        print(f"📁 Config path: {config_path}")
        
        ai_system = RealEstateAI(config_path)
        
        # Try to load existing models first
        if ai_system.load_existing_model():
            print("✅ AI system initialized successfully with existing models")
            system_initialized = True
            initialization_error = None
            
            # Initialize map visualizer after AI system is ready
            initialize_map_visualizer()
            return True
        else:
            # If models don't exist, try to set up data
            print("⚠️ No existing models found. Attempting to set up data...")
            if ai_system.setup_data():
                print("✅ Data setup completed successfully")
                system_initialized = True
                initialization_error = None
                
                # Initialize map visualizer after AI system is ready
                initialize_map_visualizer()
                return True
            else:
                initialization_error = "Failed to set up data and no existing models found"
                print(f"❌ {initialization_error}")
                return False
                
    except Exception as e:
        initialization_error = f"Error initializing AI system: {str(e)}"
        print(f"❌ {initialization_error}")
        import traceback
        traceback.print_exc()
        system_initialized = False
        return False

@app.before_request
def before_request():
    """Initialize AI system before first request if not already done"""
    global system_initialized
    if not system_initialized and ai_system is None:
        initialize_ai_system()

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html', 
                         system_ready=system_initialized,
                         maps_available=MAPS_AVAILABLE)

@app.route('/chat')
def chat():
    """Chat interface"""
    if 'conversation_history' not in session:
        session['conversation_history'] = []
    
    return render_template('chat.html', 
                         system_ready=system_initialized,
                         maps_available=MAPS_AVAILABLE)

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """API endpoint for chat interactions"""
    global ai_system, system_initialized
    
    if not system_initialized or ai_system is None:
        return jsonify({
            'success': False,
            'response': '🚧 AI system is currently initializing. Please wait a moment and try again. If this persists, please run the data setup first.',
            'error': 'System not initialized',
            'system_ready': False
        })
    
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({
                'success': False,
                'response': 'Please enter a query.'
            })
        
        conversation_history = session.get('conversation_history', [])
        
        # Process the query
        result = ai_system.process_query(query, conversation_history)
        
        # Update conversation history
        conversation_history.append({
            'query': query,
            'response': result['response'],
            'timestamp': datetime.now().isoformat(),
            'success': result['success']
        })
        
        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]
        
        session['conversation_history'] = conversation_history
        
        response_data = {
            'success': result['success'],
            'response': result['response'],
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'system_ready': True
        }
        
        if result.get('retrieval_result'):
            retrieval = result['retrieval_result']
            response_data.update({
                'documents_used': len(retrieval.get('documents', [])),
                'query_type': retrieval.get('query_type', 'unknown'),
                'categories': retrieval.get('categories', []),
                'reasoning': retrieval.get('reasoning', '')
            })
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Error in api_chat: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'response': f'Sorry, I encountered an error while processing your query: {str(e)}',
            'error': str(e),
            'system_ready': system_initialized
        })

# ============================================================================
# MAP ROUTES - NEW ADDITIONS
# ============================================================================

@app.route('/map')
def map_view():
    """Interactive map view"""
    global ai_system, system_initialized, map_visualizer, MAPS_AVAILABLE
    
    if not MAPS_AVAILABLE or map_visualizer is None:
        return render_template('map.html',
                             system_ready=system_initialized,
                             map_available=False,
                             error="Map features are not available. Please check if Folium is installed.",
                             projects_count=0)
    
    try:
        # Use real project data from AI system
        map_html = map_visualizer.create_real_map(ai_system)
        
        # Count real projects (this is approximate - the actual count is in the map)
        projects_count = 0
        if hasattr(ai_system, 'vector_store') and hasattr(ai_system.vector_store, 'documents'):
            documents = ai_system.vector_store.documents
            # Count documents with coordinates
            projects_count = sum(1 for doc in documents 
                               if doc.get('metadata', {}).get('latitude') 
                               and doc.get('metadata', {}).get('longitude')
                               and doc.get('metadata', {}).get('is_geolocation_chunk'))
        
        return render_template('map.html',
                             system_ready=system_initialized,
                             map_available=True,
                             map_html=map_html,
                             projects_count=projects_count or 3)  # Fallback to 3 if count is 0
        
    except Exception as e:
        print(f"❌ Error generating map: {e}")
        return render_template('map.html',
                             system_ready=system_initialized,
                             map_available=False,
                             error=f"Error generating map: {str(e)}",
                             projects_count=0)

@app.route('/map-test')
def map_test():
    """Test endpoint to verify map functionality"""
    global map_visualizer, MAPS_AVAILABLE
    
    if not MAPS_AVAILABLE or map_visualizer is None:
        return jsonify({
            'success': False,
            'maps_available': False,
            'error': 'Map visualizer not initialized',
            'folium_available': False
        })
    
    try:
        # Test if we can create a simple map
        map_html = map_visualizer.create_test_map()
        
        return jsonify({
            'success': True,
            'maps_available': True,
            'folium_available': True,
            'message': 'Map functionality is working correctly',
            'test_data': 'Map with 3 sample projects generated successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'maps_available': False,
            'error': str(e),
            'folium_available': False
        })

@app.route('/api/map/projects')
def api_map_projects():
    """API endpoint to get projects data for mapping (for future use)"""
    global ai_system, system_initialized
    
    if not system_initialized or ai_system is None:
        return jsonify({
            'success': False,
            'error': 'AI system not initialized'
        })
    
    try:
        # This will be implemented later to get real project data
        # For now, return test data
        test_projects = [
            {
                "project_name": "UNNATHI WOODS PHASE VII A",
                "rera_number": "P51700000002", 
                "latitude": 19.268511,
                "longitude": 72.97367,
                "project_type": "Residential",
                "completion_date": "2025-12-30",
                "total_units": 234,
                "promoter": "UNNATHI ESTATES",
                "district": "Mumbai Suburban"
            }
        ]
        
        return jsonify({
            'success': True,
            'data': test_projects,
            'count': len(test_projects),
            'message': 'Test data - will be replaced with real project data'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

# ============================================================================
# EXISTING ROUTES (unchanged)
# ============================================================================

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    """Data setup page"""
    if request.method == 'POST':
        try:
            global ai_system
            if ai_system is None:
                from main import RealEstateAI
                config_path = os.path.join(project_root, 'config', 'config.yaml')
                ai_system = RealEstateAI(config_path)
            
            success = ai_system.setup_data()
            
            if success:
                global system_initialized, initialization_error
                system_initialized = True
                initialization_error = None
                
                # Initialize map visualizer after successful setup
                initialize_map_visualizer()
                
                return jsonify({
                    'success': True,
                    'message': '✅ Data setup completed successfully! You can now use the chat and map features.'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '❌ Data setup failed. Please check the console for errors.'
                })
                
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'❌ Error during setup: {str(e)}'
            })
    
    return render_template('setup.html', system_ready=system_initialized)

@app.route('/api/system_status')
def system_status():
    """Get system status"""
    return jsonify({
        'system_ready': system_initialized,
        'error': initialization_error,
        'ai_system_available': ai_system is not None,
        'maps_available': MAPS_AVAILABLE,
        'map_visualizer_ready': map_visualizer is not None
    })

@app.route('/api/clear_history', methods=['POST'])
def clear_history():
    """Clear conversation history"""
    session['conversation_history'] = []
    return jsonify({'success': True})

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get conversation history"""
    history = session.get('conversation_history', [])
    return jsonify({'history': history})

@app.route('/search')
def search():
    """Search interface"""
    return render_template('search.html', 
                         system_ready=system_initialized,
                         maps_available=MAPS_AVAILABLE)

@app.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint for search with detailed results"""
    global ai_system, system_initialized
    
    if not system_initialized or ai_system is None:
        return jsonify({
            'success': False,
            'response': 'AI system is not available. Please run the data setup first.',
            'error': 'System not initialized'
        })
    
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({
                'success': False,
                'response': 'Please enter a search query.'
            })
        
        retrieval_result = ai_system.test_retrieval(query)
        
        if retrieval_result is None:
            return jsonify({
                'success': False,
                'response': 'No results found for your query.'
            })
        
        conversation_history = []
        process_result = ai_system.process_query(query, conversation_history)
        
        response_data = {
            'success': True,
            'query': query,
            'ai_response': process_result.get('response', ''),
            'retrieval_info': {
                'query_type': retrieval_result.get('query_type', 'unknown'),
                'categories': retrieval_result.get('categories', []),
                'entities': retrieval_result.get('entities', {}),
                'documents_found': len(retrieval_result.get('documents', [])),
                'use_rag': retrieval_result.get('use_rag', False),
                'reasoning': retrieval_result.get('reasoning', '')
            },
            'documents': []
        }
        
        for doc in retrieval_result.get('documents', [])[:10]:
            document_data = {
                'score': round(doc.get('normalized_score', 0), 3),
                'project_name': doc['document']['metadata'].get('project_name', 'Unknown'),
                'chunk_type': doc['document']['metadata'].get('chunk_type', 'Unknown'),
                'registration_number': doc['document']['metadata'].get('registration_number', ''),
                'content_preview': doc['document']['content'][:200] + '...' if len(doc['document']['content']) > 200 else doc['document']['content'],
                'full_content': doc['document']['content'],
                'retrieval_types': doc.get('retrieval_types', [])
            }
            response_data['documents'].append(document_data)
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Error in api_search: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'response': f'Search error: {str(e)}',
            'error': str(e)
        })

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy' if system_initialized else 'unavailable',
        'system_ready': system_initialized,
        'error': initialization_error,
        'maps_available': MAPS_AVAILABLE,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/debug/projects-with-coords')
def debug_projects_with_coords():
    """Debug endpoint to check which projects have coordinates"""
    global ai_system, system_initialized
    
    if not system_initialized or ai_system is None:
        return jsonify({'error': 'AI system not initialized'})
    
    try:
        projects_with_coords = []
        
        if hasattr(ai_system, 'vector_store') and hasattr(ai_system.vector_store, 'documents'):
            documents = ai_system.vector_store.documents
            
            for i, doc in enumerate(documents):
                metadata = doc.get('metadata', {})
                latitude = metadata.get('latitude')
                longitude = metadata.get('longitude')
                project_name = metadata.get('project_name', 'Unknown')
                
                if latitude and longitude:
                    projects_with_coords.append({
                        'index': i,
                        'project_name': project_name,
                        'rera_number': metadata.get('registration_number', 'Unknown'),
                        'latitude': latitude,
                        'longitude': longitude,
                        'project_type': metadata.get('project_type', 'Unknown'),
                        'chunk_type': metadata.get('chunk_type', 'Unknown')
                    })
        
        return jsonify({
            'total_documents': len(documents) if 'documents' in locals() else 0,
            'projects_with_coordinates': projects_with_coords,
            'count': len(projects_with_coords)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    print("🚀 Starting Real Estate AI Web Application...")
    print(f"📁 Project root: {project_root}")
    
    # Initialize AI system
    initialize_ai_system()
    
    if system_initialized:
        print("✅ AI system ready")
    else:
        print("⚠️ AI system not ready - visit /setup to initialize")
    
    print("🌐 Web server starting on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
