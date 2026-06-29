import cv2
import numpy as np
from PIL import Image

def is_mostly_white_background(img_np, threshold=245):
    h, w = img_np.shape[:2]
    corners = [
        img_np[0:20, 0:20],
        img_np[0:20, w-20:w],
        img_np[h-20:h, 0:20],
        img_np[h-20:h, w-20:w],
    ]
    for corner in corners:
        if corner.mean(axis=(0, 1)).min() < threshold:
            return False
    return True

def remove_background_opencv(img_pil, lo_diff=10, up_diff=10, debug_dir=None):
    """
    Remove white background using floodFill + soft alpha unblend.
    If the image doesn't have a white background, it raises an exception to fallback to rembg.
    """
    if img_pil.mode != 'RGB':
        img_pil = img_pil.convert('RGB')
    
    img = np.array(img_pil)
    h, w = img.shape[:2]

    if not is_mostly_white_background(img):
        raise ValueError("Background is not white, fallback to rembg")

    mask = np.zeros((h + 2, w + 2), np.uint8)
    
    seeds = [
        (0, 0), (w//2, 0), (w-1, 0),
        (0, h//2),         (w-1, h//2),
        (0, h-1), (w//2, h-1), (w-1, h-1)
    ]
    
    flags = cv2.FLOODFILL_MASK_ONLY | (255 << 8) | cv2.FLOODFILL_FIXED_RANGE
    
    for seed in seeds:
        cv2.floodFill(
            img, mask, seed, (255, 255, 255), 
            (lo_diff, lo_diff, lo_diff), 
            (up_diff, up_diff, up_diff), 
            flags
        )
        
    bg_mask = mask[1:-1, 1:-1]
    
    if debug_dir:
        import os
        cv2.imwrite(os.path.join(debug_dir, "debug_bg_mask.png"), bg_mask)

    img_norm = img.astype(np.float32) / 255.0
    
    dist_from_white = 1.0 - img_norm.min(axis=2)
    
    alpha = np.ones((h, w), dtype=np.float32)
    
    bg_bool_mask = bg_mask > 0
    alpha[bg_bool_mask] = dist_from_white[bg_bool_mask]
    
    # Threshold alpha to remove very low alpha noise (prevents yellow artifacts)
    alpha[alpha < (10.0 / 255.0)] = 0.0
    
    alpha_safe = np.clip(alpha, 1e-6, 1.0)
    alpha_expanded = np.expand_dims(alpha_safe, axis=2)
    
    fg_norm = (img_norm - (1.0 - alpha_expanded)) / alpha_expanded
    fg_norm = np.clip(fg_norm, 0.0, 1.0)
    
    fg_8bit = (fg_norm * 255).astype(np.uint8)
    alpha_8bit = (alpha * 255).astype(np.uint8)
    
    rgba = np.dstack((fg_8bit, alpha_8bit))
    
    return Image.fromarray(rgba, 'RGBA')

