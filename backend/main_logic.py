import os
import cv2
import face_recognition
import shutil
import json
from collections import defaultdict
import numpy as np

# Metadata file path
METADATA_PATH = "face_metadata.json"

def get_images_missing_from_metadata(input_folder, metadata_file=METADATA_PATH):
    """
    Returns a list of image filenames in input_folder that are missing from metadata.
    """
    # Get all image files in the input folder
    image_files = [
        f for f in os.listdir(input_folder) 
        if f.lower().endswith(('.jpg', '.jpeg', '.png'))
    ]
    
    if not os.path.exists(metadata_file):
        return image_files

    try:
        with open(metadata_file, "r") as f:
            metadata = json.load(f)

        # Get all image paths from metadata
        known_images = set()
        for face_data in metadata.values():
            for img_path in face_data.get("images", []):
                known_images.add(os.path.basename(img_path))

        # Find images not in metadata
        missing = [f for f in image_files if f not in known_images]
        return missing
        
    except Exception as e:
        print(f"Error checking missing images: {e}")
        return image_files

def detect_and_cluster_faces(input_folder, output_folder="face_detected", metadata_file=METADATA_PATH, only_process=None):
    """
    Detect faces in images and cluster them by similarity.
    
    Args:
        input_folder: Path to folder containing images
        output_folder: Path to save organized images
        metadata_file: Path to save face metadata
        only_process: Optional list of specific image filenames to process
        
    Returns:
        Tuple of (face_id_map, status_message)
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    face_id_map = defaultdict(list)

    # Load existing metadata if it exists
    metadata = {}
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
        except Exception as e:
            print(f"Error loading metadata: {e}")

    # Process only specified files or all files
    files_to_process = only_process if only_process else [
        f for f in os.listdir(input_folder) 
        if f.lower().endswith(('.jpg', '.jpeg', '.png'))
    ]

    # Track processed files to avoid duplication
    processed_count = 0
    
    for filename in files_to_process:
        filepath = os.path.join(input_folder, filename)
        if not os.path.exists(filepath):
            continue
            
        # Skip files we've already processed
        is_processed = False
        for face_info in metadata.values():
            if any(os.path.basename(img) == filename for img in face_info.get("images", [])):
                is_processed = True
                break
                
        if is_processed:
            continue

        # Load and process the image
        image = cv2.imread(filepath)
        if image is None:
            continue

        # Convert to RGB for face_recognition
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Detect faces
        face_locations = face_recognition.face_locations(rgb_image)
        face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
        
        # Skip if no faces detected
        if not face_encodings:
            continue

        processed_count += 1
            
        # Process each detected face
        for encoding in face_encodings:
            # Check if face matches any existing clusters
            match = None
            for face_id, data in metadata.items():
                if "encoding" not in data:
                    continue
                    
                known_encoding = np.array(data["encoding"])
                if face_recognition.compare_faces([known_encoding], encoding, tolerance=0.5)[0]:
                    match = face_id
                    break

            # Create new face ID if no match
            if match is None:
                match = f"Face_{len(metadata):03d}"
                metadata[match] = {
                    "images": [],
                    "encoding": encoding.tolist()
                }

            # Create directory for face if it doesn't exist
            face_dir = os.path.join(output_folder, match)
            os.makedirs(face_dir, exist_ok=True)
            
            # Copy image to face directory
            saved_path = os.path.join(face_dir, filename)
            
            # Handle filename conflicts
            if os.path.exists(saved_path):
                base, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(saved_path):
                    saved_path = os.path.join(face_dir, f"{base}_{counter}{ext}")
                    counter += 1
                    
            shutil.copy(filepath, saved_path)
            
            # Update tracking data
            face_id_map[match].append(saved_path)
            
            # Update metadata
            if saved_path not in metadata[match]["images"]:
                metadata[match]["images"].append(saved_path)

    # Save updated metadata
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=4)

    return face_id_map, f"Processed {processed_count} images. Found {len(face_id_map)} distinct faces."

def load_face_metadata(metadata_file=METADATA_PATH):
    """
    Load face metadata from file.
    
    Returns:
        Tuple of (face_id_map, status_message)
    """
    if not os.path.exists(metadata_file):
        return {}, "Metadata file not found."

    try:
        with open(metadata_file, "r") as f:
            metadata = json.load(f)

        face_id_map = {}
        for face_id, info in metadata.items():
            # Filter to only existing image files
            face_id_map[face_id] = [
                path for path in info.get("images", []) 
                if os.path.exists(path)
            ]

        return face_id_map, "Metadata loaded successfully."
        
    except Exception as e:
        return {}, f"Error loading metadata: {e}"

def rename_face_id(base_path, old_face_id, new_face_name, metadata_file=METADATA_PATH):
    """
    Renames a face group. If the new name exists, merge images.
    
    Returns:
        bool: Success or failure
    """
    old_folder = os.path.join(base_path, old_face_id)
    new_folder = os.path.join(base_path, new_face_name)

    if not os.path.exists(old_folder):
        print(f"Source folder {old_folder} does not exist.")
        return False

    try:
        # Load metadata
        if not os.path.exists(metadata_file):
            return False
            
        with open(metadata_file, "r") as f:
            metadata = json.load(f)

        if new_face_name == old_face_id:
            return False  # Nothing to do

        # Create target directory
        os.makedirs(new_folder, exist_ok=True)
        
        # Track existing files to avoid conflicts
        existing_files = set(os.listdir(new_folder)) if os.path.exists(new_folder) else set()
        
        # Track new paths for metadata update
        old_to_new_paths = {}
        
        # Move files from old to new directory
        for i, file_name in enumerate(os.listdir(old_folder)):
            src_file = os.path.join(old_folder, file_name)
            
            # Generate new filename to avoid conflicts
            base_name, ext = os.path.splitext(file_name)
            new_file_name = file_name
            counter = 1
            
            while new_file_name in existing_files:
                new_file_name = f"{base_name}_{counter}{ext}"
                counter += 1
                
            existing_files.add(new_file_name)
            
            # Move the file
            dst_file = os.path.join(new_folder, new_file_name)
            shutil.move(src_file, dst_file)
            
            # Track path change for metadata update
            old_to_new_paths[src_file] = dst_file

        # Remove old directory if empty
        if os.path.exists(old_folder) and not os.listdir(old_folder):
            os.rmdir(old_folder)

        # Update metadata
        if old_face_id in metadata:
            old_entry = metadata[old_face_id]
            
            # Update paths in old entry
            updated_paths = []
            for old_path in old_entry["images"]:
                if old_path in old_to_new_paths:
                    updated_paths.append(old_to_new_paths[old_path])
                else:
                    updated_paths.append(old_path)
            
            # If merging with existing entry
            if new_face_name in metadata:
                # Average the encodings for better recognition
                if "encoding" in old_entry and "encoding" in metadata[new_face_name]:
                    old_encoding = np.array(old_entry["encoding"])
                    new_encoding = np.array(metadata[new_face_name]["encoding"])
                    avg_encoding = ((old_encoding + new_encoding) / 2).tolist()
                    metadata[new_face_name]["encoding"] = avg_encoding
                    
                # Merge images lists
                metadata[new_face_name]["images"].extend(updated_paths)
                
                # Remove duplicates
                metadata[new_face_name]["images"] = list(set(metadata[new_face_name]["images"]))
            else:
                # Create new entry with updated paths
                metadata[new_face_name] = {
                    "encoding": old_entry.get("encoding"),
                    "images": updated_paths
                }
                
            # Remove old entry
            metadata.pop(old_face_id)
            
            # Save updated metadata
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=4)
                
            return True
        
        return False

    except Exception as e:
        print(f"Error during renaming: {e}")
        return False