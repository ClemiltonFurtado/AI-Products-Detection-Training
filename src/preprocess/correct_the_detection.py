"""
Script for manual review and correction of YOLO format bounding boxes.

Provides an interactive OpenCV GUI to iterate over images and labels, 
allowing the user to draw new boxes, delete incorrect ones, or change 
the class ID of existing bounding boxes on the fly.
"""

import os
import cv2

class CorrectDetection:
    """
    Utility class that encapsulates the OpenCV visual editor logic.
    """

    @staticmethod
    def find_color(class_id, colors):
        """
        Retrieves the bounding box color associated with a specific class ID.
        
        Args:
            class_id (int): The integer identifier of the object class.
            colors (list): A list of RGB/BGR color tuples.
            
        Returns:
            tuple: The BGR color tuple for the specified class.
        """
        return colors[class_id] if class_id < len(colors) else colors[-1]
    
    @staticmethod
    def mouse_callback(event, x, y, flags, param):
        """
        Callback function to handle OpenCV mouse events.
        Updates the shared context dictionary to track dragging for drawing 
        new boxes or right-clicking to delete boxes.
        
        Args:
            event: The OpenCV mouse event type.
            x (int): The x-coordinate of the mouse pointer.
            y (int): The y-coordinate of the mouse pointer.
            flags: Specific condition flags (unused here).
            param (dict): Shared dictionary containing the interactive state.
        """
        param['mouse_x'] = x
        param['mouse_y'] = y

        if event == cv2.EVENT_LBUTTONDOWN:
            param['draw'] = True
            param['ix'], param['iy'] = x, y

        elif event == cv2.EVENT_LBUTTONUP:
            param['draw'] = False
            if abs(x - param['ix']) > 5 and abs(y - param['iy']) > 5:
                param['new_box'].append((param['ix'], param['iy'], x, y))

        elif event == cv2.EVENT_RBUTTONDOWN:
            param['right_click_detect'] = True
            param['point_right_click'] = (x, y)

    @staticmethod
    def correct_detection(image_dir, label_dir, max_screen_w, max_screen_h, color):
        """
        Initializes and runs the main loop for the interactive visual editor.
        
        Args:
            image_dir (str): Directory containing the original images.
            label_dir (str): Directory containing the YOLO format label texts.
            max_screen_w (int): Maximum window width for scaling.
            max_screen_h (int): Maximum window height for scaling.
            color (list): List of color tuples for plotting bounding boxes.
        """
        image_files = sorted([f for f in os.listdir(image_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])

        print("🚀 Super Editor OpenCV Activated!")
        print("-" * 60)
        print("👉 COMMANDS (With the window active and Caps Lock off):")
        print(" [Left Mouse Button + Drag] -> ADDS a new box to the image")
        print(" [Right Mouse Button] -> DELETES the box you clicked on")
        print(" Keys [0] to [9] -> Changes the CLASS of the focused box")
        print(" [Space] or [Enter] -> KEEP/ADVANCE to the next box or image")
        print(" Key [p] -> JUMPS to the next image without saving anything")
        print(" Key [q] -> CLOSES the program immediately")
        print("-" * 60)

        window_name = "Super Editor OpenCV"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

        for current_image in image_files:
            img_path = os.path.join(image_dir, current_image)
            txt_path = os.path.join(label_dir, os.path.splitext(current_image)[0] + ".txt")
            
            orig_img = cv2.imread(img_path)
            if orig_img is None: 
                continue
                
            img_h, img_w, _ = orig_img.shape
            
            scale = min(max_screen_w / img_w, max_screen_h / img_h, 1.0)
            resize_dim = (int(img_w * scale), int(img_h * scale))
            
            annotations = []
            if os.path.exists(txt_path):
                with open(txt_path, 'r') as f:
                    for line in f.readlines():
                        parts = line.strip().split()
                        if len(parts) == 5:
                            annotations.append([int(parts[0]), float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])])

            context_mouse = {
                'new_box': [],
                'draw': False,
                'ix': -1, 'iy': -1,
                'mouse_x': -1, 'mouse_y': -1,
                'right_click_detect': False,
                'point_right_click': (-1, -1)
            }
            cv2.setMouseCallback(window_name, CorrectDetection.mouse_callback, context_mouse)
            
            box_idx = 0
            file_modified = False
            skip_image = False

            while True:
                img_canvas = orig_img.copy()
                
                if len(context_mouse['new_box']) > 0:
                    for n_box in context_mouse['new_box']:
                        x1_real, y1_real = n_box[0] / scale, n_box[1] / scale
                        x2_real, y2_real = n_box[2] / scale, n_box[3] / scale
                        
                        xc = (x1_real + x2_real) / 2 / img_w
                        yc = (y1_real + y2_real) / 2 / img_h
                        w = abs(x2_real - x1_real) / img_w
                        h = abs(y2_real - y1_real) / img_h
                        
                        annotations.append([0, xc, yc, w, h])
                        file_modified = True
                    context_mouse['new_box'] = []
                
                if context_mouse['right_click_detect']:
                    cx, cy = context_mouse['point_right_click']
                    context_mouse['right_click_detect'] = False
                    box_to_remove = None
                    
                    for j in reversed(range(len(annotations))):
                        _, xc, yc, w, h = annotations[j]
                        x1 = int((xc - w/2) * img_w * scale)
                        y1 = int((yc - h/2) * img_h * scale)
                        x2 = int((xc + w/2) * img_w * scale)
                        y2 = int((yc + h/2) * img_h * scale)
                        
                        if x1 <= cx <= x2 and y1 <= cy <= y2:
                            box_to_remove = j
                            break
                    
                    if box_to_remove is not None:
                        del annotations[box_to_remove]
                        file_modified = True
                        print(f"Box {box_to_remove + 1} removed.")
                        if box_idx >= len(annotations) and box_idx > 0:
                            box_idx -= 1

                for j, ann in enumerate(annotations):
                    c_id, xc, yc, w, h = ann
                    x1 = int((xc - w/2) * img_w)
                    y1 = int((yc - h/2) * img_h)
                    x2 = int((xc + w/2) * img_w)
                    y2 = int((yc + h/2) * img_h)
                    
                    if j == box_idx and len(annotations) > 0:
                        cv2.rectangle(img_canvas, (x1, y1), (x2, y2), CorrectDetection.find_color(c_id, color), 4)
                        display_text = f"FOCUS: Box {j+1}/{len(annotations)} | Class: {c_id}"
                        cv2.putText(img_canvas, display_text, (x1, max(y1 - 12, 30)), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 5, cv2.LINE_AA)
                        cv2.putText(img_canvas, display_text, (x1, max(y1 - 12, 30)), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)
                    else:
                        cv2.rectangle(img_canvas, (x1, y1), (x2, y2), CorrectDetection.find_color(c_id, color), 1)

                if context_mouse['draw']:
                    x1_guide = int(context_mouse['ix'] / scale)
                    y1_guide = int(context_mouse['iy'] / scale)
                    x2_guide = int(context_mouse['mouse_x'] / scale)
                    y2_guide = int(context_mouse['mouse_y'] / scale)
                    cv2.rectangle(img_canvas, (x1_guide, y1_guide), (x2_guide, y2_guide), (255, 255, 255), 2)

                img_render = cv2.resize(img_canvas, resize_dim, interpolation=cv2.INTER_AREA)
                cv2.imshow(window_name, img_render)
                
                key = cv2.waitKey(15) & 0xFF
                
                if key == 255:
                    continue
                    
                if key == 32 or key == 13:
                    if box_idx < len(annotations) - 1:
                        box_idx += 1
                    else:
                        break 

                elif 48 <= key <= 57:
                    if len(annotations) > 0:
                        new_class_id = key - 48
                        annotations[box_idx][0] = new_class_id
                        file_modified = True
                        print(f"[{current_image}] Box {box_idx+1}: Class modify to -> {new_class_id}")

                elif key == ord('p'):
                    print(f"⏭ Image `{current_image}` jumped.")
                    skip_image = True
                    break

                elif key == ord('q'):
                    cv2.destroyAllWindows()
                    print("\nUser breaks.")
                    exit()

            if file_modified and not skip_image:
                os.makedirs(os.path.dirname(txt_path), exist_ok=True)
                with open(txt_path, 'w') as f:
                    for ann in annotations:
                        f.write(f"{ann[0]} {ann[1]:.6f} {ann[2]:.6f} {ann[3]:.6f} {ann[4]:.6f}\n")
                print(f"File `{os.path.basename(txt_path)}` updated.")

        cv2.destroyAllWindows()


if __name__ == '__main__':
    INPUT_FOLDER = "../../data/Dataset"
    LABEL_DIR = "../../runs/detect/predict/labels_filtrados"
    MAX_SCREEN_W = 1280
    MAX_SCREEN_H = 720
    COLOR = [(0, 255, 0), (0, 165, 255), (255, 0, 0), (0, 0, 255), (255, 0, 255)]

    CorrectDetection.correct_detection(
        image_dir=INPUT_FOLDER,      
        label_dir=LABEL_DIR, 
        max_screen_w=MAX_SCREEN_W, 
        max_screen_h=MAX_SCREEN_H, 
        color=COLOR
    )