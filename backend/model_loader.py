import torch
from ultralytics import YOLO
from transformers import DetrForObjectDetection, DetrImageProcessor

device = "cpu"  # Force CPU usage

def load_yolo_models():
    """Load YOLO models from Ultralytics hub"""
    try:
        # Load models directly from hub
        yolo8 = YOLO('yolov8x.pt')  # Load YOLOv8x
        yolo_oi = YOLO('yolov8x-oiv7.pt')  # Load YOLOv8x trained on Open Images
        
        return [yolo8, yolo_oi]
    except Exception as e:
        raise RuntimeError(f"Failed to load YOLO models: {e}")

def load_detr_model():
    """Load DETR model from Hugging Face hub"""
    try:
        # Load the DETR model and processor
        model = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-50", ignore_mismatched_sizes=True).to(device)
        processor = DetrImageProcessor.from_pretrained("facebook/detr-resnet-50")
        model.eval()
        return model, processor
    except Exception as e:
        raise RuntimeError(f"Failed to load DETR model: {e}")