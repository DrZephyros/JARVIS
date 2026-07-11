import os
import io
import base64
import logging
import mss
import pyautogui
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger("jarvis.vision")

class HybridVisionAnnotator:
    def __init__(self):
        logger.info("Initializing Pure OpenCV Vision Annotator.")
            
    def capture_and_annotate(self):
        """
        Captures the screen and generates a Set-of-Mark annotated image and an ID mapping.
        Returns: (annotated_base64_img, id_to_coord_map, clean_base64_img)
        """
        with mss.mss() as sct:
            monitor = sct.monitors[1] # Primary monitor
            screenshot = sct.grab(monitor)
            # convert to standard formats
            img_pil = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            img_cv = np.array(img_pil)
            img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2BGR)
            
        boxes = []
        
        # Apply a bilateral filter to the BGR image. This smooths out background gradients 
        # and album art noise while preserving sharp UI edges, preventing the morphology 
        # step from merging everything into a giant blob.
        img_filtered = cv2.bilateralFilter(img_cv, 9, 75, 75)
        
        # Use stricter thresholds on the color image to only catch definitive UI elements
        # Adjusted to 50, 150 to detect modern flat UI elements like gradient buttons
        edges = cv2.Canny(img_filtered, 50, 150)
        
        # Adjust morphology kernel to catch text blocks and icons
        # Wider horizontally to link text characters into lines
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 5))
        closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            # Filter out very large/small contours
            if 10 < w < int(img_cv.shape[1] * 0.8) and 10 < h < int(img_cv.shape[0] * 0.8):
                boxes.append((x, y, w, h))
                
        # Non-Maximum Suppression (NMS) to merge/suppress overlapping boxes
        if boxes:
            # Sort by area (smallest first) to prioritize keeping the tightest boxes
            boxes.sort(key=lambda b: b[2] * b[3])
            
            kept = []
            suppressed = set()
            
            for i, (x1, y1, w1, h1) in enumerate(boxes):
                if i in suppressed:
                    continue
                kept.append((x1, y1, w1, h1))
                
                for j in range(i + 1, len(boxes)):
                    if j in suppressed:
                        continue
                    x2, y2, w2, h2 = boxes[j]
                    
                    # Compute Intersection over Union (IoU) / coverage
                    ix1 = max(x1, x2)
                    iy1 = max(y1, y2)
                    ix2 = min(x1 + w1, x2 + w2)
                    iy2 = min(y1 + h1, y2 + h2)
                    
                    if ix2 > ix1 and iy2 > iy1:
                        intersection = (ix2 - ix1) * (iy2 - iy1)
                        a1 = w1 * h1
                        a2 = w2 * h2
                        smaller_area = min(a1, a2)
                        
                        # If the smaller box is mostly inside the larger one, suppress the larger one
                        if smaller_area > 0 and intersection / smaller_area > 0.4:
                            suppressed.add(j)
                            
            # Also cap at top 150 elements to avoid overloading the LLM
            boxes = kept[:150]
            
            # Sort final boxes top-to-bottom, left-to-right for logical reading order
            boxes.sort(key=lambda b: (b[1] // 20, b[0]))
                    
        # 3. Layout Overlay
        draw = ImageDraw.Draw(img_pil, "RGBA")
        try:
            # Try to load a generic font
            font = ImageFont.truetype("arial.ttf", 16)
        except IOError:
            font = ImageFont.load_default()
            
        id_to_coord = {}
        for i, (x, y, w, h) in enumerate(boxes):
            tag_id = str(i + 1)
            cx = x + w // 2 + monitor["left"]
            cy = y + h // 2 + monitor["top"]
            id_to_coord[tag_id] = (cx, cy)
            
            # Draw semi-transparent rectangle
            draw.rectangle([x, y, x+w, y+h], outline=(255, 0, 0, 255), width=2)
            # Draw tag background
            # Calculate text size to adjust background
            text_bbox = font.getbbox(tag_id)
            tw = text_bbox[2] - text_bbox[0]
            th = text_bbox[3] - text_bbox[1]
            draw.rectangle([x, y, x + tw + 4, y + th + 4], fill=(255, 0, 0, 255))
            draw.text((x + 2, y + 2), tag_id, fill=(255, 255, 255, 255), font=font)
            
        # Convert annotated to base64
        buffered_annot = io.BytesIO()
        img_pil.save(buffered_annot, format="JPEG", quality=85)
        annot_str = base64.b64encode(buffered_annot.getvalue()).decode("utf-8")
        
        # Convert clean to base64
        clean_pil = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        buffered_clean = io.BytesIO()
        clean_pil.save(buffered_clean, format="JPEG", quality=85)
        clean_str = base64.b64encode(buffered_clean.getvalue()).decode("utf-8")
        
        return annot_str, id_to_coord, clean_str, clean_pil
