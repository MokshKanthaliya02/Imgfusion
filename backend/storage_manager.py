# backend/storage_manager.py
import json
import os

# Function to load metadata from JSON file
def load_metadata(metadata_file='data/metadata.json'):
    """Load metadata from the JSON file."""
    if os.path.exists(metadata_file):
        with open(metadata_file, 'r') as f:
            return json.load(f)
    return {}

# Function to save metadata to JSON file
def save_metadata(metadata, metadata_file='data/metadata.json'):
    """Save metadata to a JSON file."""
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=4)
