import os
from PIL import Image, ImageFilter
import numpy as np

src_path = r'c:\Users\tempo\Downloads\files\x18_raw.png'
artifact_dir = r'C:\Users\tempo\.gemini\antigravity\brain\8b69d5f5-ea94-4d38-820e-cd18bdff3395'

raw = Image.open(src_path).convert('L')
rw, rh = raw.size

# Upscale 4x with Lanczos resampling
scale = 4
up = raw.resize((rw * scale, rh * scale), Image.Resampling.LANCZOS)
arr = np.array(up, dtype=np.float32)

# Smoothstep function: x in [0, 1] -> 3x^2 - 2x^3
# We map low_thresh (dark text/lines) to 0, and high_thresh (white background) to 255
low_thresh = 95.0
high_thresh = 215.0

t = np.clip((arr - low_thresh) / (high_thresh - low_thresh), 0.0, 1.0)
# Smoothstep curve sharpens transitions while retaining sub-pixel anti-aliasing
smoothed = t * t * (3.0 - 2.0 * t)
res = (smoothed * 255.0).astype(np.uint8)

enhanced_img = Image.fromarray(res, mode='L').convert('RGB')

# Apply a gentle unsharp mask to ensure pin-sharp edges
sharp_img = enhanced_img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=140, threshold=1))

out_path = os.path.join(artifact_dir, 'wavy_curve_enhanced_clean.png')
sharp_img.save(out_path, format='PNG')
print(f"Saved {out_path}, size: {sharp_img.size}")
