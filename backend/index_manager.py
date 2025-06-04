import os
import json

metadata_file = os.path.join("data", "object_metadata.json")

def load_index(force_reload=False):
    """
    Load the object detection index from disk
    
    Args:
        force_reload (bool): If True, bypass any caching and reload directly from disk
        
    Returns:
        dict: The loaded index data
    """
    index_path = metadata_file
    
    try:
        if os.path.exists(index_path):
            with open(index_path, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading index: {e}")
    
    return {}

def save_index(index_data):
    os.makedirs(os.path.dirname(metadata_file), exist_ok=True)
    with open(metadata_file, "w") as f:
        json.dump(index_data, f, indent=4)
