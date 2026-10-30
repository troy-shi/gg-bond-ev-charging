"""Generate editable Excalidraw sketches (intro, Q7, storyboard) for the M2 report.

AI-generated (Claude) at the team's request; disclose in the report's AI-use statement.
Run from the repo root after 01_build_tables.py:
  .venv/bin/python scripts/03_make_sketch_layouts.py
Outputs (git-ignored): sketches/layouts/{intro,q7,storyboard}.excalidraw
Open them at excalidraw.com (Menu → Open) to edit; export PNGs with scripts/sketch_render/.
"""
import json
import random
from pathlib import Path

import geopandas as gpd
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
HERE = REPO / "sketches" / "layouts"
HERE.mkdir(parents=True, exist_ok=True)
random.seed(7)

INK, RED, GRAY, BLUE = "#1e1e1e", "#e03131", "#868e96", "#1971c2"
DARK, MED, LIGHT = "#364fc7", "#91a7ff", "#edf2ff"


class Sketch:
    def __init__(self):
        self.els = []

    def _base(self, kind, x, y, w, h, **kw):
        el = {
            "id": f"{kind}{len(self.els)}_{random.randint(0, 10**6)}", "type": kind,
            "x": x, "y": y, "width": w, "height": h, "angle": 0,
            "strokeColor": kw.get("stroke", INK), "backgroundColor": kw.get("fill", "transparent"),
            "fillStyle": kw.get("fill_style", "hachure"), "strokeWidth": kw.get("sw", 1),
            "strokeStyle": kw.get("style", "solid"), "roughness": kw.get("rough", 1), "opacity": 100,
            "groupIds": [], "frameId": None, "roundness": kw.get("roundness"),
            "seed": random.randint(1, 2**31), "version": 1, "versionNonce": random.randint(1, 2**31),
            "isDeleted": False, "boundElements": None, "updated": 1, "link": None, "locked": False,
        }
        return el

    def rect(self, x, y, w, h, **kw):
        self.els.append(self._base("rectangle", x, y, w, h, **kw))

    def ellipse(self, x, y, w, h, **kw):
        self.els.append(self._base("ellipse", x, y, w, h, **kw))

    def line(self, pts, arrow=False, both=False, **kw):
        x0, y0 = pts[0]
        rel = [[px - x0, py - y0] for px, py in pts]
        xs, ys = [p[0] for p in rel], [p[1] for p in rel]
        el = self._base("arrow" if arrow else "line", x0, y0, max(xs) - min(xs), max(ys) - min(ys), **kw)
        el.update({"points": rel, "lastCommittedPoint": None, "startBinding": None, "endBinding": None,
                   "startArrowhead": "arrow" if both else None, "endArrowhead": "arrow" if arrow else None})
        self.els.append(el)

    def text(self, x, y, s, size=16, color=INK, align="left"):
        # one element per line: multi-line text elements render shifted in the export library
        for i, ln in enumerate(s.split("\n")):
            w, h = len(ln) * size * 0.56, size * 1.25
            el = self._base("text", x - w / 2 if align == "center" else x, y + i * h, w, h, stroke=color)
            el.update({"text": ln, "originalText": ln, "fontSize": size, "fontFamily": 1, "textAlign": align,
                       "verticalAlign": "top", "containerId": None, "lineHeight": 1.25, "baseline": int(size),
                       "autoResize": True})
            self.els.append(el)

    def save(self, name):
        doc = {"type": "excalidraw", "version": 2, "source": "https://excalidraw.com", "elements": self.els,
               "appState": {"viewBackgroundColor": "#ffffff", "gridSize": None}, "files": {}}
        (HERE / name).write_text(json.dumps(doc, indent=1))
        print("wrote", name, len(self.els), "elements")


def source_line(s, x, y):
    s.text(x, y, "Source: AFDC station snapshot 2026-10-30 · ACS 2020-2024 5-yr · USDA RUCC 2023", 13, GRAY)


def legend_note(s, x, y, w):
    s.text(x, y, "red = interaction", 13, RED)


# ------------------------------------------------------------------ data for Q7 map
states = gpd.read_file(f"zip://{REPO / 'data/raw/cb_2024_us_state_20m.zip'}")
states = states[~states.STUSPS.isin(["AK", "HI", "PR"])].to_crs(5070)
outline = max(states.union_all().simplify(25000).geoms, key=lambda g: g.area)
counties = gpd.read_file(f"zip://{REPO / 'data/raw/cb_2024_us_county_20m.zip'}").to_crs(5070)
cs = pd.read_csv(REPO / "data/processed/county_summary.csv", dtype={"county_fips": str})
counties = counties.merge(cs[["county_fips", "q7_selected_default", "stations"]], left_on="GEOID", right_on="county_fips")
counties = counties[~counties.STATEFP.isin(["02", "15", "72"])]
minx, miny, maxx, maxy = outline.bounds


def project(px, py, ox, oy, w, h):
    k = min(w / (maxx - minx), h / (maxy - miny))
    return ox + (px - minx) * k, oy + (maxy - py) * k


# ================================================================== INTRO
s = Sketch()
s.text(40, 20, "Before we start: four words you'll see in every chart", 28)
s.text(40, 62, "Intro explainer (top of the article, before Q1)", 15, GRAY)
cards = [
    ("STATION", "a location\n(one pin on the map)", "83,666 public stations"),
    ("PORT", "one vehicle can\ncharge at a time", "263,062 ports\n(~3.1 per station)"),
    ("CHARGING LEVEL", "how fast", "L1 0.3% · L2 69.5%\nDC fast 30.2% of ports"),
    ("CONNECTOR", "the plug shape", "J1772 · CCS1 ·\nCHAdeMO · NACS"),
]
for i, (title, sub, stat) in enumerate(cards):
    x = 40 + i * 330
    s.rect(x, 110, 300, 400, roundness={"type": 3})
    s.text(x + 150, 125, title, 22, align="center")
    s.text(x + 150, 160, sub, 16, GRAY, align="center")
    s.text(x + 150, 430, stat, 15, BLUE, align="center")
# station: map pin + building
x = 40
s.ellipse(x + 120, 230, 60, 60, fill=MED, fill_style="solid")
s.line([(x + 130, 280), (x + 150, 330), (x + 170, 280)])
s.ellipse(x + 140, 250, 20, 20, fill="#ffffff", fill_style="solid")
s.line([(x + 60, 360), (x + 240, 360)])
s.text(x + 150, 372, "1 station = 1 dot", 14, align="center")
# port: one station box with 3 posts, one car each
x = 370
s.rect(x + 40, 230, 220, 40, fill=LIGHT, fill_style="solid")
s.text(x + 150, 240, "1 station", 14, align="center")
for j in range(3):
    px = x + 70 + j * 70
    s.rect(px, 285, 20, 45, fill=MED, fill_style="solid")
    s.rect(px - 15, 345, 50, 25, roundness={"type": 3})
    s.ellipse(px - 10, 365, 12, 12, fill=INK, fill_style="solid")
    s.ellipse(px + 18, 365, 12, 12, fill=INK, fill_style="solid")
s.text(x + 150, 395, "3 ports = 3 cars at once", 14, align="center")
# level: speed bars
x = 700
for j, (lab, ln, t) in enumerate([("Level 1", 30, "~40+ hours"), ("Level 2", 90, "4-10 hours"), ("DC fast", 220, "20-60 min")]):
    yy = 225 + j * 60
    s.text(x + 20, yy, lab, 15)
    s.rect(x + 95, yy, ln * 0.85, 22, fill=[LIGHT, MED, DARK][j], fill_style="solid")
    s.text(x + 95, yy + 26, t, 13, GRAY)
s.text(x + 150, 400, "time to add ~200 miles", 14, GRAY, align="center")
# connector: four plug faces
x = 1030
for j, lab in enumerate(["J1772", "CCS1", "CHAdeMO", "NACS"]):
    cx, cy = x + 40 + (j % 2) * 130, 220 + (j // 2) * 105
    s.ellipse(cx, cy, 70, 70)
    for k in range([5, 6, 2, 4][j]):
        s.ellipse(cx + 15 + (k % 3) * 16, cy + 18 + (k // 3) * 20, 9, 9, fill=INK, fill_style="solid")
    s.text(cx + 35, cy + 74, lab, 13, align="center")
s.text(40, 540, "Note: ports describe physical supply only, not use, reliability, or waiting time.", 15)
s.text(40, 565, "Each card hover: one-sentence definition + national total from the snapshot.", 15, RED)
source_line(s, 40, 595)
s.save("intro.excalidraw")

# ================================================================== Q7
s = Sketch()
s.text(30, 15, "Counties that may merit a closer look", 30)
s.text(30, 58, "Q7 · screening view (not a verdict)", 15, GRAY)
# control panel
s.rect(30, 90, 1340, 170, roundness={"type": 3})
sliders = [("Total ports per 100k residents", "<= 30th pct = 9.4", 0.30, (0.25, 0.60)),
           ("DC fast ports per 100k residents", "<= 40th pct = 2.4", 0.40, (0.25, 0.60)),
           ("Median household income", "<= 50th pct = $65,671", 0.50, (0.25, 0.75))]
for i, (lab, val, p, (lo, hi)) in enumerate(sliders):
    y = 110 + i * 48
    s.text(50, y, lab, 15)
    s.line([(330, y + 12), (630, y + 12)], sw=2)
    knob = 330 + (p - lo) / (hi - lo) * 300
    s.ellipse(knob - 9, y + 3, 18, 18, fill=RED, fill_style="solid", stroke=RED)
    s.text(322, y + 20, f"{int(lo*100)}th", 11, GRAY)
    s.text(612, y + 20, f"{int(hi*100)}th", 11, GRAY)
    s.text(650, y, val, 15, BLUE)
s.text(860, 105, "Rule (always shown):", 15)
s.text(860, 128, "selected = total_rate <= cutoff\n  AND dc_fast_rate <= cutoff\n  AND income <= cutoff", 14)
s.rect(860, 200, 330, 46, stroke=BLUE)
s.text(872, 205, "575 counties selected\n(526 with no stations) · +0 / -0 vs default", 13, BLUE)
s.rect(1220, 200, 120, 46, roundness={"type": 3}, stroke=RED)
s.text(1280, 212, "Reset", 18, RED, align="center")
s.text(330, 245, "drag -> map, table, counter update", 13, RED)
# map
mx, my, mw, mh = 30, 290, 760, 470
s.rect(mx, my, mw, mh)
pts = [project(px, py, mx + 20, my + 30, mw - 40, mh - 120) for px, py in outline.exterior.coords]
s.line(pts, stroke=GRAY)
sel = counties[counties.q7_selected_default == "selected"].copy()
sel["pt"] = sel.geometry.representative_point()
for _, r in sel.sample(90, random_state=3).iterrows():
    cx, cy = project(r.pt.x, r.pt.y, mx + 20, my + 30, mw - 40, mh - 120)
    zero = r.stations == 0
    s.rect(cx - 5, cy - 5, 10, 10, fill=DARK if zero else MED, fill_style="solid" if zero else "cross-hatch",
           stroke=DARK if zero else BLUE, rough=0)
lx, ly = mx + 20, my + mh - 82
for i, (lab, fill, fs, st) in enumerate([("selected · no stations recorded", DARK, "solid", "solid"),
                                          ("selected · some stations", MED, "cross-hatch", "solid"),
                                          ("not selected", LIGHT, "solid", "solid"),
                                          ("not evaluated (missing data)", "transparent", "solid", "dashed")]):
    xx, yy = lx + (i % 2) * 360, ly + (i // 2) * 30
    s.rect(xx, yy, 18, 18, fill=fill, fill_style=fs, style=st)
    s.text(xx + 26, yy, lab, 14)
s.text(mx + 10, my + 8, "County map (fill + pattern, not color alone) · hover = tooltip", 14, GRAY)
# table
tx, ty, tw = 820, 290, 550
s.rect(tx, ty, tw, 470)
s.text(tx + 12, ty + 8, "Sortable table   [x] show 'not evaluated'", 14, GRAY)
cols = ["County", "St", "Ports", "Ports/100k", "DC/100k", "Income", "Status"]
cx = [0, 135, 170, 225, 315, 395, 470]
s.line([(tx, ty + 60), (tx + tw, ty + 60)])
for c, off in zip(cols, cx):
    s.text(tx + 10 + off, ty + 36, c + (" v" if c == "Ports/100k" else ""), 13)
rows = [("Madison Co.", "IN", "7", "5.3", "0.8", "63,037", "sel."),
        ("Lafourche Par.", "LA", "2", "2.1", "2.1", "63,135", "sel."),
        ("White Co.", "AR", "7", "9.0", "0.0", "55,249", "sel."),
        ("Iberia Par.", "LA", "0", "0.0", "0.0", "56,961", "sel. (0)"),
        ("Autauga Co.", "AL", "13", "21.7", "16.7", "72,481", "not sel."),
        ("Solano Co.", "CA", "-", "-", "-", "100,401", "not eval.")]
for i, row in enumerate(rows):
    y = ty + 72 + i * 40
    if i == 1:
        s.rect(tx + 4, y - 6, tw - 8, 32, stroke=RED, style="dashed")
    for v, off in zip(row, cx):
        s.text(tx + 10 + off, y, v, 13)
s.text(tx + 12, ty + 330, "...  scrolls; header stays fixed", 13, GRAY)
s.line([(790, 470), (820, 470)], arrow=True, both=True, stroke=RED, sw=2)
s.text(640, 425, "click county <-> row", 13, RED)
s.text(640, 442, "highlight + scroll", 13, RED)
s.line([(480, 260), (420, 300)], arrow=True, stroke=RED, sw=2)
s.line([(1000, 250), (1060, 290)], arrow=True, stroke=RED, sw=2)
# caption
s.rect(30, 780, 1340, 70, stroke=GRAY)
s.text(45, 790, "These counties meet the selected screening criteria and may merit closer review. This does not prove a charging shortage.\n"
                "Travel demand, EV ownership, neighboring chargers, operating conditions, and uncertainty in the estimates are not fully represented.", 14)
source_line(s, 30, 862)
s.save("q7.excalidraw")

# ================================================================== STORYBOARD
s = Sketch()
s.text(30, 15, "Storyboard: one scroll, one question per step", 30)
s.text(30, 58, "* = one of the three coordinated interactions; arrows = transition sentence", 15, GRAY)
frames = [
    ("Intro", "4 icons: station, port,\nlevel, connector", "vocabulary", "icons"),
    ("Q1 Where", "county port circles\n+ state bars", "coasts & metros lead", "map"),
    ("Q2 Per resident *", "choropleth <-> dot plot\ncount / rate toggle", "ranks reshuffle", "map"),
    ("Q3 When", "opening-year bars\n+ bulk-date note", "mostly recent (caveats)", "bars"),
    ("Q4 How fast", "L1/L2/DC share bars\n+ DC fast rate dots", "fast supply varies >5x", "stack"),
    ("Q5 Who & which plug *", "state dropdown ->\nnetwork bars + heatmap", "few networks dominate", "heat"),
    ("Q6 Context", "2 scatterplots, income\nvs rate, metro shape", "weak positive association", "scatter"),
    ("Q7 Closer look *", "sliders -> map + table", "adjustable shortlist", "map"),
]
transitions = ["Let's start with\nwhere chargers are", "Big places have more\npeople: divide by residents",
               "When did these\nstations appear?", "Not all chargers are\nequal: how fast?",
               "Who runs them, which\ncars can plug in?", "Does supply follow\nincome or rurality?",
               "Which counties combine\nall three conditions?"]
W, H = 300, 250
for i, (title, body, take, icon) in enumerate(frames):
    col, row = i % 4, i // 4
    x, y = 30 + col * (W + 50), 100 + row * (H + 110)
    s.rect(x, y, W, H, roundness={"type": 3}, stroke=RED if "*" in title else INK, sw=2 if "*" in title else 1)
    s.text(x + 12, y + 10, f"{i}. {title}" if i else title, 18)
    ix, iy = x + 20, y + 50
    if icon == "map":
        pts = [project(px, py, ix, iy, 140, 80) for px, py in outline.exterior.coords][::3]
        s.line(pts, stroke=GRAY)
        for _ in range(6):
            s.ellipse(ix + random.randint(20, 120), iy + random.randint(15, 60), 10, 10, fill=MED, fill_style="solid")
    elif icon == "bars":
        for k, hgt in enumerate([10, 12, 14, 18, 25, 45, 80, 60, 70, 72, 76, 62]):
            s.rect(ix + k * 13, iy + 90 - hgt, 10, hgt, fill=MED if k != 7 else DARK, fill_style="solid")
    elif icon == "stack":
        for k in range(4):
            a = random.randint(80, 140)
            s.rect(ix, iy + k * 22, a, 16, fill=MED, fill_style="solid")
            s.rect(ix + a, iy + k * 22, 160 - a, 16, fill=DARK, fill_style="solid")
            s.ellipse(ix + 185 + random.randint(0, 50), iy + k * 22 + 3, 10, 10, fill=INK, fill_style="solid")
    elif icon == "heat":
        for k in range(4):
            s.rect(ix, iy + k * 20, 40 + (4 - k) * 18, 14, fill=MED, fill_style="solid")
            for c in range(4):
                s.rect(ix + 140 + c * 22, iy + k * 20, 18, 14, fill=[LIGHT, MED, DARK][random.randint(0, 2)], fill_style="solid")
    elif icon == "scatter":
        for p in range(2):
            s.rect(ix + p * 125, iy, 110, 85)
            for _ in range(10):
                s.ellipse(ix + p * 125 + random.randint(5, 95), iy + random.randint(10, 75), 7, 7)
    else:
        for k in range(4):
            s.ellipse(ix + k * 62, iy + 15, 44, 44)
    s.text(x + 12, y + 150, body, 14)
    s.text(x + 12, y + 205, "-> " + take, 14, BLUE)
for i, t in enumerate(transitions):
    col, row = i % 4, i // 4
    x, y = 30 + col * (W + 50), 100 + row * (H + 110)
    if col < 3:
        s.line([(x + W + 5, y + H / 2), (x + W + 45, y + H / 2)], arrow=True)
        s.text(x + W + 25, y + H + 10, t, 12, GRAY, align="center")
    else:
        s.line([(x + W / 2, y + H + 5), (30 + W / 2, y + H + 105)], arrow=True)
        s.text(900, y + H + 62, t, 12, GRAY, align="center")
s.text(30, 840, "Each step: short heading + 2-3 sentences of text, then the view. Shared colors, units, and legends throughout.", 15)
source_line(s, 30, 868)
s.save("storyboard.excalidraw")
