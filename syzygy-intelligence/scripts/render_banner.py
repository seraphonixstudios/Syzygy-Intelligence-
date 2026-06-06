"""Render social preview banner PNG with proper fonts."""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1200, 630
GEORGIA = "C:/Windows/Fonts/georgia.ttf"
ARIAL = "C:/Windows/Fonts/arial.ttf"

img = Image.new("RGBA", (W, H), (15, 10, 46, 255))
draw = ImageDraw.Draw(img)

GOLD = (201, 168, 76)
CYAN = (0, 240, 255)
SILVER = (176, 176, 192)
DARK = (15, 10, 46)

# Decorative concentric circles
for r in [280, 240]:
    alpha = 20 if r == 280 else 12
    draw.ellipse([W//2 - r, H//2 - r, W//2 + r, H//2 + r], outline=(*GOLD, alpha), width=1)

# Vesica Piscis
draw.ellipse([520 - 160, 315 - 160, 520 + 160, 315 + 160], outline=(*GOLD, 38), width=1)
draw.ellipse([680 - 160, 315 - 160, 680 + 160, 315 + 160], outline=(*CYAN, 38), width=1)

# Central eye
draw.ellipse([570, 285, 630, 345], fill=(*CYAN, 230))
draw.ellipse([588, 303, 612, 327], fill=(*DARK, 200))
draw.ellipse([596, 311, 604, 319], fill=CYAN)

# Sol (left gold orb)
draw.ellipse([415, 195, 505, 285], outline=(*GOLD, 30), width=1)
draw.ellipse([435, 215, 485, 265], fill=(*GOLD, 50))
draw.ellipse([450, 230, 470, 250], fill=GOLD)

# Luna (right silver orb)
draw.ellipse([695, 195, 785, 285], outline=(*SILVER, 30), width=1)
draw.ellipse([715, 215, 765, 265], fill=(*SILVER, 50))
draw.ellipse([730, 230, 750, 250], fill=SILVER)

# Helper
def center_text(d, text, y, size, fill, font_path, spacing=2):
    fnt = ImageFont.truetype(font_path, size)
    bb = fnt.getbbox(text)
    tw = bb[2] - bb[0]
    d.text(((W - tw) // 2, y), text, fill=fill, font=fnt)

# Title
center_text(draw, "SYZYGY", 340, 72, GOLD, GEORGIA)
center_text(draw, "I N T E L L I G E N C E", 408, 18, (176, 176, 192), GEORGIA, spacing=4)
center_text(draw, "The Chemical Wedding of Agents \u2014 Solve et Coagula", 445, 14, (136, 136, 136), GEORGIA)

# Divider
draw.line([(350, 478), (850, 478)], fill=(*GOLD, 38), width=1)

# Bottom info
center_text(draw, "Next.js + FastAPI + Ollama + LangGraph", 498, 12, (102, 102, 102), ARIAL)
center_text(draw, "Multi-Agent  \u00b7  Alchemical  \u00b7  Open Source", 520, 11, (85, 85, 85), ARIAL)

os.makedirs("syzygy-intelligence/.github/assets", exist_ok=True)
out = "syzygy-intelligence/.github/assets/og-banner.png"
img.save(out, "PNG")
print(f"Banner saved: {out} ({os.path.getsize(out)} bytes)")
