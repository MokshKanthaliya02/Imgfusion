import os
import torch
from PyQt6.QtCore import QThread, pyqtSignal
from PIL import Image
from backend.model_loader import load_yolo_models, load_detr_model

class ObjectDetectionThread(QThread):
    detection_complete = pyqtSignal(dict)
    progress_update = pyqtSignal(int, int)

    def __init__(self, image_folder, existing_index):
        super().__init__()
        self.image_folder = image_folder
        self.existing_index = existing_index

    def run(self):
        index_data = self.existing_index.copy()
        image_files = [f for f in os.listdir(self.image_folder) if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))]

        new_images = [f for f in image_files if f not in index_data]
        total_new = len(new_images)

        if not total_new:
            self.detection_complete.emit(index_data)
            return

        # Load YOLO models
        yolo_models = load_yolo_models()
        # Load DETR model
        detr_model, detr_processor = load_detr_model()

        for i, filename in enumerate(new_images, start=1):
            image_path = os.path.join(self.image_folder, filename)
            detected_objects = {}

            # YOLO detection
            for model in yolo_models:
                try:
                    # Run inference with YOLO models
                    results = model(image_path)
                    for result in results:
                        for box, cls_idx, conf in zip(result.boxes.xyxy, result.boxes.cls, result.boxes.conf):
                            label = result.names[int(cls_idx)]
                            if conf >= 0.7:  # Confidence threshold for YOLO
                                detected_objects[label] = max(detected_objects.get(label, 0), float(conf))
                except Exception as e:
                    print(f"YOLO error on {filename}: {e}")

            # DETR detection
            try:
                image = Image.open(image_path).convert("RGB")
                encoding = detr_processor(images=image, return_tensors="pt").to("cpu")
                with torch.no_grad():
                    # Run inference with DETR
                    outputs = detr_model(**encoding)
                logits = outputs.logits.softmax(-1)[0]
                for logit, box in zip(logits, outputs.pred_boxes):
                    max_score, label = logit[:-1].max(0)
                    if max_score > 0.7:  # Confidence threshold for DETR
                        obj_name = detr_model.config.id2label[label.item()]
                        detected_objects[obj_name] = max(detected_objects.get(obj_name, 0), float(max_score))
            except Exception as e:
                print(f"DETR error on {filename}: {e}")

            # Update index data with detected objects for the current image
            index_data[filename] = detected_objects
            # Update progress (emit signal)
            self.progress_update.emit(i, total_new)

        # Emitting the final detection results
        self.detection_complete.emit(index_data)

