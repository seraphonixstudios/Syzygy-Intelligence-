"""Render social preview banner with Sol, Luna, Rebis logos, black background, gold/silver text."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

W, H = 1200, 630
GEORGIA = "C:/Windows/Fonts/georgia.ttf"
ARIAL = "C:/Windows/Fonts/arial.ttf"
BRANDING = "syzygy-intelligence/frontend/public/branding"

# Load logos
sol_raw = Image.open(f"{BRANDING}/sol.logo.png").convert("RGBA")
luna_raw = Image.open(f"{BRANDING}/luna.logo.png").convert("RGBA")
rebis_raw = Image.open(f"{BRANDING}/rebis.logo.png").convert("RGBA")

# Resize logos
sol_h = 280
ratio = sol_h / sol_raw.height
sol = sol_raw.resize((int(sol_raw.width * ratio), sol_h), Image.LANCZOS)

luna_h = 280
ratio = luna_h / luna_raw.height
luna = luna_raw.resize((int(luna_raw.width * ratio), luna_h), Image.LANCZOS)

rebis_h = 340
ratio = rebis_h / rebis_raw.height
rebis = rebis_raw.resize((int(rebis_raw.width * ratio), rebis_h), Image.LANCZOS)

# Create banner
img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
draw = ImageDraw.Draw(img)

GOLD = (201, 168, 76)
SILVER = (176, 176, 192)

# Position logos
# Sol: left side, vertically centered
sol_x = 20
sol_y = (H - sol.height) // 2
img.paste(sol, (sol_x, sol_y), sol)

# Luna: right side, vertically centered
luna_x = W - luna.width - 20
luna_y = (H - luna.height) // 2
img.paste(luna, (luna_x, luna_y), luna)

# Rebis: center, slightly raised
rebis_x = (W - rebis.width) // 2
rebis_y = (H - rebis.height) // 2 - 20
img.paste(rebis, (rebis_x, rebis_y), rebis)

# Helper
def center_text(d, text, y, size, fill, font_path):
    fnt = ImageFont.truetype(font_path, size)
    bb = fnt.getbbox(text)
    tw = bb[2] - bb[0]
    d.text(((W - tw) // 2, y), text, fill=fill, font=fnt)

# Title (below rebis)
title_y = rebis_y + rebis.height + 15
center_text(draw, "SYZYGY", title_y, 58, GOLD, GEORGIA)
center_text(draw, "I N T E L L I G E N C E", title_y + 58, 16, SILVER, GEORGIA)

# Tagline
center_text(draw, "The Chemical Wedding of Agents \u2014 Solve et Coagula", title_y + 85, 13, (160, 160, 170), GEORGIA)

# Bottom bar
draw.line([(300, title_y + 110), (900, title_y + 110)], fill=(*GOLD, 60), width=1)
center_text(draw, "Next.js + FastAPI + Ollama + LangGraph", title_y + 118, 11, (120, 120, 130), ARIAL)
center_text(draw, "Multi-Agent  \u00b7  Alchemical  \u00b7  Open Source", title_y + 136, 10, (100, 100, 110), ARIAL)

# Save
out = "syzygy-intelligence/.github/assets/og-banner.png"
img.save(out, "PNG")
print(f"Banner saved: {out} ({os.path.getsize(out)} bytes)")
