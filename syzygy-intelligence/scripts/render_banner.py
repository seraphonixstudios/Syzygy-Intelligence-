"""Social preview banner: Sol/Luna/Rebis, alchemy stars, big bright text."""
from PIL import Image, ImageDraw, ImageFont
import os, random

W, H = 1200, 630
GEORGIA = "C:/Windows/Fonts/georgia.ttf"
ARIAL = "C:/Windows/Fonts/arial.ttf"
BRANDING = "syzygy-intelligence/frontend/public/branding"

sol  = Image.open(f"{BRANDING}/sol.logo.png").convert("RGBA").resize((187, 280), Image.LANCZOS)
luna = Image.open(f"{BRANDING}/luna.logo.png").convert("RGBA").resize((187, 280), Image.LANCZOS)
rebis= Image.open(f"{BRANDING}/rebis.logo.png").convert("RGBA").resize((227, 340), Image.LANCZOS)

img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
draw = ImageDraw.Draw(img)

G = (220, 188, 95)
S = (225, 225, 235)

# ── Alchemical stars ─────────────────────────────────────
random.seed(42)
stars = ["\u2606","\u263f","\u2640","\u2642","\u2609","\u263d","\u2726","\u2735","\u221e","\u25cb","\u25b3","\u25bd","\u2727"]
f = [ImageFont.truetype(ARIAL, s) for s in (26, 20, 14)]
for _ in range(120):
    x, y = random.randint(0, W-1), random.randint(0, H-1)
    a = random.randint(20, 100)
    draw.text((x, y), random.choice(stars), fill=(*G, a), font=random.choice(f))

# ── Logos ────────────────────────────────────────────────
img.paste(sol,  (20, (H-280)//2), sol)
img.paste(luna, (W-207, (H-280)//2), luna)
img.paste(rebis, ((W-227)//2, (H-340)//2-30), rebis)

# ── Dark backdrop for text ──────────────────────────────
ty = (H-340)//2 - 30 + 340 + 5            # title_y
draw.rectangle([(0, ty-10), (W, ty+170)], fill=(0,0,0,180))

# ── Text ────────────────────────────────────────────────
def ct(d, t, y, s, c, f):
    fnt = ImageFont.truetype(f, s)
    bb = fnt.getbbox(t)
    d.text(((W-(bb[2]-bb[0]))//2, y), t, fill=c, font=fnt)

ct(draw, "SYZYGY", ty, 72, G, GEORGIA)
ct(draw, "I N T E L L I G E N C E", ty+72, 22, S, GEORGIA)
ct(draw, "The Chemical Wedding of Agents \u2014 Solve et Coagula", ty+106, 18, (210,210,220), GEORGIA)

draw.line([(250, ty+136), (950, ty+136)], fill=(*G, 90), width=2)
ct(draw, "Next.js + FastAPI + Ollama + LangGraph", ty+148, 15, (200,200,210), ARIAL)
ct(draw, "Multi-Agent  \u00b7  Alchemical  \u00b7  Open Source", ty+170, 14, (185,185,195), ARIAL)

out = "syzygy-intelligence/.github/assets/og-banner.png"
img.save(out, "PNG")
print(f"Saved: {out} ({os.path.getsize(out)} bytes)")
