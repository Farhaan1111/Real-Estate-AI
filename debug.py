import os

def debug_paths():
    print("🔍 Debugging Paths...")
    
    current_dir = os.getcwd()
    print(f"Current working directory: {current_dir}")
    
    # Check from web_app directory
    web_app_dir = os.path.join(current_dir, 'web_app')
    if os.path.exists(web_app_dir):
        print(f"Web app directory exists: {web_app_dir}")
        
        # Check models path from web_app
        models_path_from_web_app = os.path.join(web_app_dir, '..', 'models', 'vector_store.faiss')
        models_path_abs = os.path.abspath(models_path_from_web_app)
        print(f"Models path from web_app: {models_path_abs}")
        print(f"Models exist from web_app: {os.path.exists(models_path_abs)}")
    
    # Check from project root
    models_path_from_root = os.path.join(current_dir, 'models', 'vector_store.faiss')
    print(f"Models path from root: {models_path_from_root}")
    print(f"Models exist from root: {os.path.exists(models_path_from_root)}")
    
    # List all files in models directory
    models_dir = os.path.join(current_dir, 'models')
    if os.path.exists(models_dir):
        print(f"\n📁 Files in models directory:")
        for file in os.listdir(models_dir):
            file_path = os.path.join(models_dir, file)
            size = os.path.getsize(file_path)
            print(f"  {file} ({size} bytes)")

if __name__ == "__main__":
    debug_paths()