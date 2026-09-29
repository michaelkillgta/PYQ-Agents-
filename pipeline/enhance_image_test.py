import os
from PIL import Image, ImageFilter, ImageOps, ImageEnhance
import numpy as np

src_path = r'C:\Users\tempo\.gemini\antigravity\brain\8b69d5f5-ea94-4d38-820e-cd18bdff3395\.user_uploaded\media_1789717620050.png'
raw_x18 = r'c:\Users\tempo\Downloads\files\x18_raw.png'
artifact_dir = r'C:\Users\tempo\.gemini\antigravity\brain\8b69d5f5-ea94-4d38-820e-cd18bdff3395'

# Load the uploaded image
img = Image.open(src_path).convert('RGB')
w, h = img.size
print(f"Original uploaded size: {w}x{h}")

# Technique 1: Advanced Unsharp Mask + Contrast Stretching
# Crop inner white card if needed or process entire card
gray = img.convert('L')

# Contrast stretching
arr = np.array(gray, dtype=np.float32)
# Map near-white (> 210) to pure white 255
# Map dark line pixels (< 120) to deep dark
# Smooth transition
enhanced_arr = np.clip((arr - 100) / (230 - 100) * 255, 0, 255).astype(np.uint8)
t1_img = Image.fromarray(enhanced_arr)

# Unsharp mask
t1_sharp = t1_img.filter(ImageFilter.UnsharpMask(radius=2, percent=200, threshold=3))
t1_out = os.path.join(artifact_dir, 'enhanced_v1_sharp.png')
t1_sharp.save(t1_out)
print(f"Saved {t1_out}")

# Technique 2: High-Resolution Upscale (2x) with Lanczos + Edge Refinement + Binarized Clean lines
up_w, up_h = w * 2, h * 2
img_up = img.resize((up_w, up_h), Image.Resampling.LANCZOS)
gray_up = img_up.convert('L')
arr_up = np.array(gray_up, dtype=np.float32)

# Intelligent sigmoidal contrast curve to eliminate blur halo around edges
# Midpoint around 180, steep slope
norm = (arr_up - 170.0) / 45.0
sig = 1.0 / (1.0 + np.exp(-norm))
clean_arr = (sig * 255.0).astype(np.uint8)
t2_img = Image.fromarray(clean_arr)

# Gentle unsharp mask to crisp up letter edges
t2_sharp = t2_img.filter(ImageFilter.UnsharpMask(radius=1.5, percent=150, threshold=2))
t2_out = os.path.join(artifact_dir, 'enhanced_v2_clean_crisp.png')
t2_sharp.save(t2_out)
print(f"Saved {t2_out}")

# Technique 3: From raw vector-embedded PDF image (x18_raw.png)
if os.path.exists(raw_x18):
    raw = Image.open(raw_x18).convert('RGB')
    rw, rh = raw.size
    # Upscale 4x with Lanczos
    raw_4x = raw.resize((rw * 4, rh * 4), Image.Resampling.LANCZOS)
    raw_gray = raw_4x.convert('L')
    r_arr = np.array(raw_gray, dtype=np.float32)
    # Background flattening
    r_norm = (r_arr - 165.0) / 40.0
    r_sig = 1.0 / (1.0 + np.exp(-r_norm))
    r_clean = (r_sig * 255.0).astype(np.uint8)
    t3_img = Image.fromarray(r_clean)
    t3_sharp = t3_img.filter(ImageFilter.UnsharpMask(radius=2.0, percent=180, threshold=2))
    t3_out = os.path.join(artifact_dir, 'enhanced_v3_raw_4x.png')
    t3_sharp.save(t3_out)
    print(f"Saved {t3_out}")
