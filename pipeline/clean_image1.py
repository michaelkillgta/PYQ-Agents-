import os
from PIL import Image, ImageFilter
import numpy as np

src_path = r'C:\Users\tempo\.gemini\antigravity\brain\8b69d5f5-ea94-4d38-820e-cd18bdff3395\.user_uploaded\media_1789718616395.png'
artifact_dir = r'C:\Users\tempo\.gemini\antigravity\brain\8b69d5f5-ea94-4d38-820e-cd18bdff3395'

img = Image.open(src_path).convert('RGB')
w, h = img.size

# Upscale 4x with high quality Lanczos
scale = 4
up = img.resize((w * scale, h * scale), Image.Resampling.LANCZOS)
arr = np.array(up, dtype=np.float32)

r = arr[:, :, 0]
g = arr[:, :, 1]
b = arr[:, :, 2]

# In black ink, R, G, and B are all low.
# In blue watermark, R is high (>180) and B is very high (>210).
# In white paper, R, G, B are all > 240.
# The minimum of R, G, B captures any ink.
# But using Red channel specifically eliminates the blue watermark completely because blue has high red compared to black!
ink = r  # black is < 110, blue watermark is > 190, paper is 255

# Apply smoothstep threshold to lock background to pure white and black ink to 0
low_thresh = 90.0
high_thresh = 185.0

t = np.clip((ink - low_thresh) / (high_thresh - low_thresh), 0.0, 1.0)
smooth = t * t * (3.0 - 2.0 * t)
res = (smooth * 255.0).astype(np.uint8)

clean_img = Image.fromarray(res, mode='L').convert('RGB')
# Gentle unsharp mask for razor-sharp edge definition
sharp_img = clean_img.filter(ImageFilter.UnsharpMask(radius=1.3, percent=150, threshold=1))

out_path = os.path.join(artifact_dir, 'image1_cleaned_deblurred.png')
sharp_img.save(out_path, format='PNG')
print(f"Saved {out_path}, size: {sharp_img.size}")
