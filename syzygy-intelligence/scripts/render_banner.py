"""Social preview: triangle logo layout, big readable text, alchemy stars."""
from PIL import Image, ImageDraw, ImageFont
import os, random

W, H = 1200, 630
GEORGIA = "C:/Windows/Fonts/georgia.ttf"
ARIAL   = "C:/Windows/Fonts/arial.ttf"
BRANDING = "syzygy-intelligence/frontend/public/branding"

# ── Load + resize ───────────────────────────────────────
def load(n, h):
    return Image.open(f"{BRANDING}/{n}").convert("RGBA").resize(
        (int(1024 * h / 1536), h), Image.LANCZOS)

sol   = load("sol.logo.png",   190)
luna  = load("luna.logo.png",  190)
rebis = load("rebis.logo.png", 270)

img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
draw = ImageDraw.Draw(img)

G = (220, 188, 95)     # gold
S = (225, 225, 235)    # silver bright

# ── Alchemical stars ─────────────────────────────────────
random.seed(42)
stars = ["\u2606","\u263f","\u2640","\u2642","\u2609","\u263d","\u2726","\u2735","\u221e","\u25b3","\u25bd"]
fs = [ImageFont.truetype(ARIAL, s) for s in (24, 18, 12)]
for _ in range(120):
    x, y, a = random.randint(0,W-1), random.randint(0,H-1), random.randint(20,100)
    draw.text((x, y), random.choice(stars), fill=(*G, a), font=random.choice(fs))

# ── Triangle layout ─────────────────────────────────────
# Sol: top-left, Luna: top-right, Rebis: center-below
sol_x,   sol_y   = 50,  20
luna_x,  luna_y  = W - luna.width - 50, 20
rebis_x, rebis_y = (W - rebis.width)//2, sol_y + max(sol.height, luna.height) - 40

img.paste(sol,   (sol_x,   sol_y),   sol)
img.paste(luna,  (luna_x,  luna_y),  luna)
img.paste(rebis, (rebis_x, rebis_y), rebis)

# ── Text backdrop ────────────────────────────────────────
ty = rebis_y + rebis.height + 8
draw.rectangle([(0, ty-8), (W, ty+145)], fill=(0, 0, 0, 180))

def ct(d, t, y, s, c, f):
    fnt = ImageFont.truetype(f, s)
    bb = fnt.getbbox(t)
    d.text(((W-(bb[2]-bb[0]))//2, y), t, fill=c, font=fnt)

ct(draw, "SYZYGY",                  ty,     52, G,     GEORGIA)
ct(draw, "I N T E L L I G E N C E", ty+50,  16, S,     GEORGIA)
ct(draw, "The Chemical Wedding of Agents \u2014 Solve et Coagula", ty+74, 14, (210,210,220), GEORGIA)

draw.line([(300, ty+92), (900, ty+92)], fill=(*G, 80), width=1)
ct(draw, "Next.js + FastAPI + Ollama + LangGraph",  ty+100, 11, (200,200,210), ARIAL)
ct(draw, "Multi-Agent  \u00b7  Alchemical  \u00b7  Open Source", ty+118, 10, (185,185,195), ARIAL)

out = "syzygy-intelligence/.github/assets/og-banner.png"
img.save(out, "PNG")
print(f"Saved: {out} ({os.path.getsize(out)} bytes)")
