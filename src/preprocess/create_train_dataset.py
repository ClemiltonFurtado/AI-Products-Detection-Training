"""
Script for preparing and re-indexing the YOLO training dataset.

This module extracts specific classes (oil and rice) from raw dataset annotations,
re-indexes them to meet YOLO standards (starting at 0), and builds the final 
folder structure required for model training.
"""

import os
import shutil

class CreateTrainDataset:
    """
    Utility class to process raw dataset annotations and images,
    creating a clean, YOLO-compliant dataset structure.
    """

    @staticmethod
    def create_path(final_dataset):
        """
        Creates the necessary 'images' and 'labels' subdirectories.

        Args:
            final_dataset (str): The base directory for the new dataset.
        """
        os.makedirs(os.path.join(final_dataset, "images"), exist_ok=True)
        os.makedirs(os.path.join(final_dataset, "labels"), exist_ok=True)

    @staticmethod
    def create_dataset():
        """
        Processes labels and images to generate the final dataset.
        
        Reads filtered label files, remaps class ID '1' (oil) to '0' and 
        class '2' (rice) to '1'. It ignores images without relevant detections, 
        copies valid image-label pairs to the destination folder, and generates 
        the necessary data.yaml configuration file.
        """
        CreateTrainDataset.create_path(FINAL_DATASET)
        
        filtered_labels = [f for f in os.listdir(LABELS_FILTERED) if f.lower().endswith('.txt')]
        copied_count = 0

        for label_file in filtered_labels:
            source_lbl_path = os.path.join(LABELS_FILTERED, label_file)
            
            mapped_lines = []
            with open(source_lbl_path, 'r') as f:
                for line in f.readlines():
                    parts = line.strip().split()
                    if len(parts) == 5:
                        class_id = parts[0]
                        
                        if class_id == '1':
                            parts[0] = '0'
                            mapped_lines.append(" ".join(parts) + "\n")
                        elif class_id == '2':
                            parts[0] = '1'
                            mapped_lines.append(" ".join(parts) + "\n")
            
            if not mapped_lines:
                continue

            base_name = os.path.splitext(label_file)[0]
            image_found = None
            for ext in ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']:
                test_img_path = os.path.join(INPUT_FOLDER, base_name + ext)
                if os.path.exists(test_img_path):
                    image_found = test_img_path
                    break
                    
            if image_found:
                dest_img = os.path.join(FINAL_DATASET, "images", os.path.basename(image_found))
                dest_lbl = os.path.join(FINAL_DATASET, "labels", label_file)
                
                shutil.copy(image_found, dest_img)
                
                with open(dest_lbl, 'w') as f:
                    f.writelines(mapped_lines)
                    
                copied_count += 1
            else:
                print(f"⚠️ Alert: Image not found for label file: {label_file}")

        print(f"✅ Success! {copied_count} pairs optimized and reindexed for YOLO (0: oil, 1: rice).")

        yaml_path = os.path.join(FINAL_DATASET, "data.yaml")

        yaml_content = f"""# Dataset re-indexed for YOLO (Sequential classes starting from 0)
path: {FINAL_DATASET}
train: images 
val: images   

nc: 2 

names:
  0: oil
  1: rice
"""

        with open(yaml_path, 'w') as f:
            f.write(yaml_content.strip())

        print(f"Configured File in: `{yaml_path}`")
        print("-" * 60)


# Global paths configuration
LABELS_FILTERED = "../../runs/detect/predict/labels_filtrados"
FINAL_DATASET = "../../data/Dataset/dataset_oil_and_rice"
INPUT_FOLDER = "../../data/Dataset"

# Script execution entry point
if __name__ == '__main__':
    CreateTrainDataset.create_dataset()