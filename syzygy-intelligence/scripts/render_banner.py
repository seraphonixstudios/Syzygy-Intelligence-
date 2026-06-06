"""Render social preview banner: Sol/Luna/Rebis, alchemy stars, black bg, gold/silver text."""
from PIL import Image, ImageDraw, ImageFont
import os, random

W, H = 1200, 630
GEORGIA = "C:/Windows/Fonts/georgia.ttf"
ARIAL = "C:/Windows/Fonts/arial.ttf"
BRANDING = "syzygy-intelligence/frontend/public/branding"

# Load logos
sol_raw = Image.open(f"{BRANDING}/sol.logo.png").convert("RGBA")
luna_raw = Image.open(f"{BRANDING}/luna.logo.png").convert("RGBA")
rebis_raw = Image.open(f"{BRANDING}/rebis.logo.png").convert("RGBA")

sol_h = 280
sol = sol_raw.resize((int(sol_raw.width * sol_h / sol_raw.height), sol_h), Image.LANCZOS)
luna_h = 280
luna = luna_raw.resize((int(luna_raw.width * luna_h / luna_raw.height), luna_h), Image.LANCZOS)
rebis_h = 340
rebis = rebis_raw.resize((int(rebis_raw.width * rebis_h / rebis_raw.height), rebis_h), Image.LANCZOS)

img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
draw = ImageDraw.Draw(img)

GOLD = (201, 168, 76)
GOLD_L = (220, 195, 110)
SILVER = (200, 200, 210)

# ── Alchemical symbols as stars ──────────────────────────
random.seed(42)
symbols = [
    "\u2606",  # white star
    "\u2605",  # black star
    "\u263f",  # mercury
    "\u2640",  # venus/feminine
    "\u2642",  # mars/masculine
    "\u2609",  # sun
    "\u263d",  # crescent moon
    "\u2726",  # four-pointed star
    "\u2735",  # eight-pointed star
    "\u221e",  # infinity
    "\u25cb",  # circle
    "\u25b3",  # upward triangle (fire)
    "\u25bd",  # downward triangle (water)
    "\u2727",  # white four-point star
    "\u2734",  # eight-pointed star
]
fnt_small = ImageFont.truetype(ARIAL, 12)
fnt_tiny = ImageFont.truetype(ARIAL, 8)
fnt_med = ImageFont.truetype(ARIAL, 16)

for _ in range(180):
    x = random.randint(0, W - 1)
    y = random.randint(0, H - 1)
    sym = random.choice(symbols)
    size = random.choice([fnt_tiny, fnt_small, fnt_med])
    alpha = random.randint(15, 80)
    draw.text((x, y), sym, fill=(*GOLD, alpha), font=size)

# ── Position logos ───────────────────────────────────────
sol_x, sol_y = 20, (H - sol.height) // 2
img.paste(sol, (sol_x, sol_y), sol)

luna_x, luna_y = W - luna.width - 20, (H - luna.height) // 2
img.paste(luna, (luna_x, luna_y), luna)

rebis_x, rebis_y = (W - rebis.width) // 2, (H - rebis.height) // 2 - 30
img.paste(rebis, (rebis_x, rebis_y), rebis)

# ── Helper ───────────────────────────────────────────────
def center_text(d, text, y, size, fill, font_path):
    fnt = ImageFont.truetype(font_path, size)
    bb = fnt.getbbox(text)
    tw = bb[2] - bb[0]
    d.text(((W - tw) // 2, y), text, fill=fill, font=fnt)

# ── Title ────────────────────────────────────────────────
title_y = rebis_y + rebis.height + 5  # moved higher
center_text(draw, "SYZYGY", title_y, 58, GOLD, GEORGIA)
center_text(draw, "I N T E L L I G E N C E", title_y + 56, 18, (210, 210, 220), GEORGIA)

# ── Tagline ──────────────────────────────────────────────
center_text(draw, "The Chemical Wedding of Agents \u2014 Solve et Coagula", title_y + 85, 14, (195, 195, 205), GEORGIA)

# ── Bottom bar ──────────────────────────────────────────
draw.line([(300, title_y + 110), (900, title_y + 110)], fill=(*GOLD, 60), width=1)
center_text(draw, "Next.js + FastAPI + Ollama + LangGraph", title_y + 120, 12, (175, 175, 185), ARIAL)
center_text(draw, "Multi-Agent  \u00b7  Alchemical  \u00b7  Open Source", title_y + 140, 11, (160, 160, 170), ARIAL)

out = "syzygy-intelligence/.github/assets/og-banner.png"
img.save(out, "PNG")
print(f"Banner saved: {out} ({os.path.getsize(out)} bytes)")
