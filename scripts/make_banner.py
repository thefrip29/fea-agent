"""Compose docs/banner.png: gradient + title + FEA part render (white removed)."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from matplotlib.font_manager import FontProperties, findfont

W, H = 1280, 320

xs = np.linspace(0, 1, W)[None, :]
ys = np.linspace(0, 1, H)[:, None]
t = np.clip(0.5 * xs + 0.5 * ys, 0, 1)[..., None]
c0, c1 = np.array([11, 18, 32]), np.array([22, 33, 62])
img = Image.fromarray(((1 - t) * c0 + t * c1).astype(np.uint8), "RGB")
d = ImageDraw.Draw(img, "RGBA")

for gx in range(0, W, 52):                      # subtle FE-mesh grid
    d.line([(gx, 0), (gx, H)], fill=(148, 163, 184, 18))
for gy in range(0, H, 34):
    d.line([(0, gy), (W, gy)], fill=(148, 163, 184, 18))

def F(size):
    return ImageFont.truetype(findfont(FontProperties(family="DejaVu Sans", weight="bold")), size)

def Fr(size):
    return ImageFont.truetype(findfont(FontProperties(family="DejaVu Sans")), size)

rod = Image.open("docs/rod.png").convert("RGBA")
a = np.array(rod)
a[..., 3] = np.where((a[..., :3] >= 244).all(-1), 0, a[..., 3])   # white -> transparent
rod = Image.fromarray(a)

s = min(250 / rod.height, 470 / rod.width)
rod = rod.resize((max(1, int(rod.width * s)), max(1, int(rod.height * s))), Image.LANCZOS)
img.paste(rod, (W - rod.width - 50, (H - rod.height) // 2), rod)

d.text((70, 96), "FEA", font=F(58), fill=(241, 245, 249))
w = d.textlength("FEA", font=F(58))
d.text((70 + w, 92), "-Agent", font=F(58), fill=(56, 189, 248))
d.text((70, 176), "LLM-driven CAE: generate · solve · parse · verify",
       font=Fr(21), fill=(148, 163, 184))

logo = Image.open("docs/mistral_logo.png").convert("RGBA")
s = 34 / logo.width
logo = logo.resize((34, int(logo.height * s)), Image.LANCZOS)
img.paste(logo, (70, 240), logo)
d.text((116, 246), "Powered by Mistral AI", font=Fr(17), fill=(148, 163, 184))

img.save("docs/banner.png")
print("saved docs/banner.png")
