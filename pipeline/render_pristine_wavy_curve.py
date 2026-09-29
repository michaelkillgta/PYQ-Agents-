import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

artifact_dir = r'C:\Users\tempo\.gemini\antigravity\brain\8b69d5f5-ea94-4d38-820e-cd18bdff3395'
out_png = os.path.join(artifact_dir, 'wavy_curve_pristine_2k.png')

# Create figure with 3:1 aspect ratio, high resolution (300 DPI)
fig, ax = plt.subplots(figsize=(10, 3.2), dpi=300)
fig.patch.set_facecolor('white')
ax.set_facecolor('white')

# Critical x positions
sq5 = np.sqrt(5)
sq3 = np.sqrt(3)
x_crit = [-sq5, -sq3, 0.0, sq3, sq5]

# Axis range
x_min, x_max = -3.2, 3.5
y_axis = 0.0

# 1. Draw horizontal number line
ax.plot([x_min, x_max], [y_axis, y_axis], color='black', lw=2.2, solid_capstyle='round')

# 2. Draw tick marks and math labels
tick_len = 0.22
labels = [r'$-\sqrt{5}$', r'$-\sqrt{3}$', r'$0$', r'$\sqrt{3}$', r'$\sqrt{5}$']
for x, lab in zip(x_crit, labels):
    ax.plot([x, x], [y_axis, y_axis - tick_len], color='black', lw=2.0)
    ax.text(x, y_axis - tick_len - 0.15, lab, ha='center', va='top', fontsize=16, fontweight='bold', color='black')

# 3. Define smooth wavy curve passing through:
# (-3.0, 1.8), (-sq5, 0.8)[min], (-sq3, 1.8)[max], (0, 0.8)[min], (sq3, 1.8)[max], (sq5, 0.8)[min], (3.1, 1.9)
# Use piecewise cubic splines / cosine arcs for that classic crisp textbook curve
x_pts = []
y_pts = []

# Section 1: left tail to -sq5
t1 = np.linspace(-3.0, -sq5, 60)
# starts high at 1.8, reaches min at -sq5 (y=0.8) with zero derivative
y1 = 0.8 + 1.0 * ((t1 - (-sq5)) / (-3.0 - (-sq5)))**2
x_pts.extend(t1[:-1])
y_pts.extend(y1[:-1])

# Arc -sq5 to -sq3 (min 0.8 to max 1.8)
t2 = np.linspace(-sq5, -sq3, 60)
y2 = 1.3 - 0.5 * np.cos(np.pi * (t2 - (-sq5)) / (-sq3 - (-sq5)))
x_pts.extend(t2[:-1])
y_pts.extend(y2[:-1])

# Arc -sq3 to 0 (max 1.8 to min 0.8)
t3 = np.linspace(-sq3, 0.0, 60)
y3 = 1.3 + 0.5 * np.cos(np.pi * (t3 - (-sq3)) / (0.0 - (-sq3)))
x_pts.extend(t3[:-1])
y_pts.extend(y3[:-1])

# Arc 0 to sq3 (min 0.8 to max 1.8)
t4 = np.linspace(0.0, sq3, 60)
y4 = 1.3 - 0.5 * np.cos(np.pi * (t4 - 0.0) / (sq3 - 0.0))
x_pts.extend(t4[:-1])
y_pts.extend(y4[:-1])

# Arc sq3 to sq5 (max 1.8 to min 0.8)
t5 = np.linspace(sq3, sq5, 60)
y5 = 1.3 + 0.5 * np.cos(np.pi * (t5 - sq3) / (sq5 - sq3))
x_pts.extend(t5[:-1])
y_pts.extend(y5[:-1])

# Right tail from sq5 to 3.1
t6 = np.linspace(sq5, 3.1, 60)
y6 = 0.8 + 1.1 * ((t6 - sq5) / (3.1 - sq5))**2
x_pts.extend(t6)
y_pts.extend(y6)

ax.plot(x_pts, y_pts, color='black', lw=2.4)

# 4. Critical point dots on the curve
# Troughs at y=0.8, Peaks at y=1.8
troughs = [-sq5, 0.0, sq5]
peaks = [-sq3, sq3]
for xt in troughs:
    ax.plot(xt, 0.8, 'o', color='black', markersize=6.5)
for xp in peaks:
    ax.plot(xp, 1.8, 'o', color='black', markersize=6.5)

# 5. Circled + and - signs
# Intervals:
# (-inf, -sq5): mid = -2.7 -> (-)
# (-sq5, -sq3): mid = (-sq5 + -sq3)/2 = -1.984 -> (+)
# (-sq3, 0): mid = -sq3/2 = -0.866 -> (-)
# (0, sq3): mid = sq3/2 = 0.866 -> (+)
# (sq3, sq5): mid = (sq3 + sq5)/2 = 1.984 -> (-)
# (sq5, inf): mid = 2.75 -> (+)

sign_info = [
    (-2.70, r'$-$'),
    (-1.98, r'$+$'),
    (-0.866, r'$-$'),
    (0.866, r'$+$'),
    (1.98, r'$-$'),
    (2.75, r'$+$'),
]

y_sign = 0.35
r_circle = 0.16

for x_s, s_text in sign_info:
    # Draw circle
    circ = patches.Circle((x_s, y_sign), r_circle, edgecolor='black', facecolor='white', lw=1.8)
    ax.add_patch(circ)
    # Draw sign inside circle
    ax.text(x_s, y_sign, s_text, ha='center', va='center', fontsize=14, fontweight='bold', color='black')

ax.set_xlim(x_min, x_max + 0.1)
ax.set_ylim(-0.9, 2.2)
ax.axis('off')

plt.tight_layout()
plt.savefig(out_png, dpi=300, facecolor='white', bbox_inches='tight')
plt.close()
print(f"Saved pristine 2K vector-rendered PNG: {out_png}")
