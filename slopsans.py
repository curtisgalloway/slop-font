#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Curtis Galloway
# SPDX-License-Identifier: Apache-2.0
"""Slop Sans generator.

Humanist-sans stroke skeletons -> six 'AI-malformed' alternates per glyph -> TTF with
OpenType features:
  calt : stem-merge (H M N h m n lose their right stem into a following left-stem letter)
         + pseudo-random cycling through the 6 alternates
  ss01-ss06 : pin alternate N
  ss07 : 'sober' - the unmutated humanist skeleton
  kern : over-kerning that fuses stems, bowls, bars, diagonals, and the rn->m / cl->d / vv->w misreads

usage: slopsans.py <intensity> <style-name> <out.ttf>
"""
import math, random, sys
from shapely.geometry import LineString, Point, Polygon, MultiPolygon
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

CAP, XH, ASC, DESC = 700, 500, 720, -210
W = 105
PEN = math.radians(30)  # broad-nib angle for humanist contrast


def arc(cx, cy, rx, ry, a0, a1, n=None):
    if n is None:
        n = max(6, int(abs(a1 - a0) / 9))
    return [(cx + rx * math.cos(math.radians(a)), cy + ry * math.sin(math.radians(a)))
            for a in [a0 + (a1 - a0) * i / n for i in range(n + 1)]]


def ell(cx, cy, rx, ry):
    return arc(cx, cy, rx, ry, 90, 450)


def dot(x, y):
    return [(x, y - 12), (x, y + 12)]

# ---------------------------------------------------------------- skeletons
# name -> (strokes, advance). Coordinates: baseline 0, y up.
G = {}
def g(name, adv, *strokes): G[name] = ([list(s) for s in strokes], adv)

g('A', 600, [(40,0),(300,CAP)], [(300,CAP),(560,0)], [(150,230),(450,230)])
g('B', 580, [(80,0),(80,CAP)], [(80,CAP),(300,CAP)]+arc(300,540,160,160,90,-90)+[(80,380)],
  [(80,380),(320,380)]+arc(320,190,190,190,90,-90)+[(80,0)])
g('C', 620, arc(330,350,270,350,45,315))
g('D', 620, [(80,0),(80,CAP)], [(80,CAP),(260,CAP)]+arc(260,350,300,350,90,-90)+[(80,0)])
g('E', 560, [(80,0),(80,CAP)], [(80,CAP),(500,CAP)], [(80,370),(440,370)], [(80,0),(500,0)])
g('F', 530, [(80,0),(80,CAP)], [(80,CAP),(500,CAP)], [(80,370),(420,370)])
g('G', 660, arc(330,350,270,350,45,360), [(380,350),(600,350)])
g('H', 600, [(80,0),(80,CAP)], [(520,0),(520,CAP)], [(80,360),(520,360)])
g('I', 220, [(80,0),(80,CAP)])
g('J', 420, [(330,CAP),(330,150)]+arc(180,150,150,150,0,-180))
g('K', 580, [(80,0),(80,CAP)], [(80,290),(500,CAP)], [(230,400),(540,0)])
g('L', 520, [(80,0),(80,CAP)], [(80,0),(480,0)])
g('M', 680, [(80,0),(80,CAP)], [(80,CAP),(340,120)], [(340,120),(600,CAP)], [(600,CAP),(600,0)])
g('N', 600, [(80,0),(80,CAP)], [(80,CAP),(520,0)], [(520,0),(520,CAP)])
g('O', 680, ell(340,350,280,350))
g('P', 580, [(80,0),(80,CAP)], [(80,CAP),(310,CAP)]+arc(310,520,180,180,90,-90)+[(80,340)])
g('Q', 680, ell(340,350,280,350), [(380,120),(560,-60)])
g('R', 600, [(80,0),(80,CAP)], [(80,CAP),(310,CAP)]+arc(310,520,180,180,90,-90)+[(80,340)], [(300,340),(540,0)])
g('S', 620, arc(320,525,195,165,30,270)+arc(315,190,215,170,90,-150)[1:])
g('T', 620, [(60,CAP),(560,CAP)], [(310,CAP),(310,0)])
g('U', 600, [(80,CAP),(80,230)]+arc(300,230,220,230,180,360)+[(520,CAP)])
g('V', 600, [(40,CAP),(300,0)], [(300,0),(560,CAP)])
g('W', 800, [(30,CAP),(220,0)], [(220,0),(400,CAP)], [(400,CAP),(580,0)], [(580,0),(770,CAP)])
g('X', 600, [(60,0),(540,CAP)], [(60,CAP),(540,0)])
g('Y', 600, [(40,CAP),(300,330)], [(560,CAP),(300,330)], [(300,330),(300,0)])
g('Z', 600, [(70,CAP),(530,CAP)], [(530,CAP),(70,0)], [(70,0),(540,0)])

g('a', 580, arc(300,380,180,120,165,0)+[(480,380),(480,0)], arc(300,150,180,150,35,355))
g('b', 600, [(80,0),(80,ASC)], arc(300,250,220,250,180,540))
g('c', 540, arc(300,250,220,250,45,315))
g('d', 600, [(520,0),(520,ASC)], ell(300,250,220,250))
g('e', 600, [(85,270),(515,270)], arc(300,260,215,245,0,300))
g('f', 360, [(160,0),(160,560)]+arc(330,560,170,160,180,60), [(50,500),(330,500)])
g('g', 600, ell(300,250,220,250), [(520,XH),(520,-40)]+arc(290,-40,230,170,0,-180))
g('h', 600, [(80,0),(80,ASC)], [(80,320)]+arc(300,320,220,180,180,0)+[(520,0)])
g('i', 220, [(80,0),(80,XH)], dot(80,650))
g('j', 360, [(260,XH),(260,-40)]+arc(120,-40,140,150,0,-180), dot(260,650))
g('k', 520, [(80,0),(80,ASC)], [(80,200),(420,XH)], [(220,320),(470,0)])
g('l', 220, [(80,0),(80,ASC)])
g('m', 880, [(80,0),(80,XH)], [(80,330)]+arc(260,330,180,170,180,0)+[(440,0)], [(440,330)]+arc(620,330,180,170,180,0)+[(800,0)])
g('n', 600, [(80,0),(80,XH)], [(80,330)]+arc(300,330,220,170,180,0)+[(520,0)])
g('o', 600, ell(300,250,230,250))
g('p', 600, [(80,XH),(80,DESC)], arc(300,250,220,250,180,540))
g('q', 600, [(520,XH),(520,DESC)], ell(300,250,220,250))
g('r', 400, [(80,0),(80,XH)], [(80,320)]+arc(250,320,170,180,180,30))
g('s', 540, arc(290,375,165,125,30,270)+arc(300,125,185,125,90,-150)[1:])
g('t', 400, [(170,ASC),(170,160)]+arc(320,160,150,160,180,330), [(50,500),(360,500)])
g('u', 600, [(80,XH),(80,180)]+arc(300,180,220,180,180,360), [(520,XH),(520,0)])
g('v', 520, [(40,XH),(260,0)], [(260,0),(480,XH)])
g('w', 700, [(30,XH),(190,0)], [(190,0),(350,XH)], [(350,XH),(510,0)], [(510,0),(670,XH)])
g('x', 520, [(50,0),(470,XH)], [(50,XH),(470,0)])
g('y', 540, [(40,XH),(268,0)], [(500,XH),(170,DESC)])
g('z', 520, [(60,XH),(460,XH)], [(460,XH),(60,0)], [(60,0),(470,0)])

g('zero', 560, ell(280,350,230,350))
g('one', 560, [(100,560),(280,CAP)], [(280,CAP),(280,0)])
g('two', 560, arc(280,505,205,185,165,-60)+[(60,0),(500,0)])
g('three', 560, arc(270,525,190,170,150,-90), arc(270,180,215,180,90,-150))
g('four', 560, [(400,0),(400,CAP)], [(400,CAP),(50,200)], [(50,200),(520,200)])
g('five', 560, [(480,CAP),(110,CAP),(90,380),(240,430)]+arc(270,215,230,215,80,-150)[1:])
g('six', 560, arc(330,400,260,300,75,180)+[(70,220)], ell(290,220,220,220))
g('seven', 560, [(70,CAP),(510,CAP)], [(510,CAP),(220,0)])
g('eight', 560, ell(280,525,180,175), ell(280,175,210,175))
g('nine', 560, arc(230,300,260,300,255,360)+[(490,480)], ell(270,480,220,220))

g('period', 240, dot(100,40))
g('comma', 240, [(110,60),(60,-120)])
g('colon', 240, dot(100,40), dot(100,420))
g('semicolon', 240, [(110,60),(60,-120)], dot(100,420))
g('exclam', 260, [(100,CAP),(100,220)], dot(100,40))
g('question', 500, arc(250,520,180,180,180,-70)+[(250,250)], dot(250,40))
g('hyphen', 380, [(50,270),(330,270)])
g('quotesingle', 180, [(85,CAP),(75,560)])
g('quotedbl', 320, [(85,CAP),(75,560)], [(235,CAP),(225,560)])
g('parenleft', 360, arc(420,280,320,520,120,240))
g('parenright', 360, arc(-60,280,320,520,60,-60))
g('slash', 420, [(20,-60),(400,CAP)])
g('ampersand', 680, arc(300,520,150,150,-30,230)+[(80,160)]+arc(240,160,160,160,180,320)+[(560,-10)], [(620,270),(380,0)])
g('space', 250)

# right-stem letters that lose that stem into a following left-stem glyph.
# name -> (x of stem to drop, strokes with stem removed and crossbar/diagonal extended)
MERGE = {
  'H': (520, [[(80,0),(80,CAP)], [(80,360),(560,360)]]),
  'M': (600, [[(80,0),(80,CAP)], [(80,CAP),(340,120)], [(340,120),(620,CAP)]]),
  'N': (520, [[(80,0),(80,CAP)], [(80,CAP),(550,-10)]]),
  'h': (520, [[(80,0),(80,ASC)], [(80,320)]+arc(300,320,220,180,180,0)+[(540,240)]]),
  'm': (800, [[(80,0),(80,XH)], [(80,330)]+arc(260,330,180,170,180,0)+[(440,0)], [(440,330)]+arc(620,330,180,170,180,0)+[(820,240)]]),
  'n': (520, [[(80,0),(80,XH)], [(80,330)]+arc(300,330,220,170,180,0)+[(540,240)]]),
}
LEFT_STEM = list('BDEFHIKLMNPRbhiklmnpru')
for nm, (stem_x, strokes) in MERGE.items():
    G[nm + '.merge'] = (strokes, stem_x - 80)   # follower's stem (at its x=80) lands where ours was

UNI = {chr(c): chr(c) for c in range(0x41, 0x5b)}
UNI.update({chr(c): chr(c) for c in range(0x61, 0x7b)})
UNI.update({'0':'zero','1':'one','2':'two','3':'three','4':'four','5':'five','6':'six','7':'seven','8':'eight','9':'nine',
            '.':'period',',':'comma',':':'colon',';':'semicolon','!':'exclam','?':'question','-':'hyphen',
            "'":'quotesingle','"':'quotedbl','(':'parenleft',')':'parenright','/':'slash','&':'ampersand',' ':'space'})

# ---------------------------------------------------------------- stroke rendering
def resample(pts, step=20):
    ls = LineString(pts)
    n = max(2, int(ls.length / step))
    return [ls.interpolate(i / n, normalized=True).coords[0] for i in range(n + 1)]


def nib_width(p, q, k=1.0):
    d = math.atan2(q[1] - p[1], q[0] - p[0])
    return W * k * (0.62 + 0.38 * abs(math.sin(d - PEN)))


def ink(pts, wmul=1.0, widths=None, flat_ends=True):
    """Humanist stroke: flat segment buffers + round interior joins."""
    pts = [p for i, p in enumerate(pts) if i == 0 or p != pts[i - 1]]
    if len(pts) < 2:
        return Point(pts[0]).buffer(W * wmul / 2)
    polys = []
    for i in range(len(pts) - 1):
        w = (widths[i] if widths else nib_width(pts[i], pts[i + 1])) * wmul
        polys.append(LineString([pts[i], pts[i + 1]]).buffer(w / 2, cap_style=2 if flat_ends else 1))
        if 0 < i:
            polys.append(Point(pts[i]).buffer(w / 2))
    return unary_union(polys)


def render(strokes, wmul=1.0):
    if not strokes:
        return Polygon()
    return unary_union([ink(s, wmul) for s in strokes])


def jitter(pts, amp, rng, smooth=3):
    pts = resample(pts)
    noise = [rng.uniform(-amp, amp) for _ in pts]
    for _ in range(smooth):
        noise = [(noise[max(i-1,0)] + noise[i] + noise[min(i+1,len(noise)-1)]) / 3 for i in range(len(noise))]
    out = []
    for i, (x, y) in enumerate(pts):
        x0, y0 = pts[max(i-1,0)]; x1, y1 = pts[min(i+1,len(pts)-1)]
        dx, dy = x1-x0, y1-y0; L = math.hypot(dx, dy) or 1
        out.append((x - dy/L*noise[i], y + dx/L*noise[i]))
    return out

# ---------------------------------------------------------------- the six recipes (k = intensity)
def m1_wobble(strokes, rng, k):
    geoms = []
    for s in strokes:
        pts = jitter(s, 16*k, rng)
        ws = [nib_width(pts[i], pts[i+1]) * rng.uniform(1-0.45*k, 1+0.4*k) for i in range(len(pts)-1)]
        for _ in range(2):
            ws = [(ws[max(i-1,0)]+ws[i]+ws[min(i+1,len(ws)-1)])/3 for i in range(len(ws))]
        geoms.append(ink(pts, widths=ws))
    return unary_union(geoms)


def m2_drop_extra(strokes, rng, k):
    ss = list(strokes)
    if len(ss) >= 3 and rng.random() < min(1, 0.5 + 0.5*k):
        ss.pop(rng.randrange(len(ss)))
    y = rng.choice([XH*0.35, XH*0.62, CAP*0.55])
    x0 = rng.uniform(60, 250); x1 = x0 + rng.uniform(120, 200) * (0.6 + 0.6*k)
    ss.append([(x0, y), (x1, y + rng.uniform(-40, 40)*k)])
    return render([jitter(s, 5*k, rng) for s in ss])


def m3_melt(strokes, rng, k):
    geoms = []
    for s in strokes:
        pts = []; ws = []
        rs = resample(s)
        for x, y in rs:
            t = max(0.0, 1 - y/XH)
            pts.append((x + 80*k*t*t, y - 60*k*t*t))
        for i in range(len(pts)-1):
            t = max(0, 1 - pts[i][1]/XH)
            ws.append(nib_width(pts[i], pts[i+1]) * (1 + 0.55*k*t*t))
        geoms.append(ink(pts, widths=ws))
    gm = unary_union(geoms)
    for _ in range(rng.randint(1, 1 + int(k))):
        x = rng.uniform(100, 500)
        gm = gm.union(ink([(x, 10), (x, -rng.uniform(50, 140)*k)], 0.6, flat_ends=False))
    gm = gm.union(Point(rng.uniform(80, 500), rng.uniform(250, 450)).buffer(W*(0.5+0.4*k)))
    return gm


def m4_duplicate(strokes, rng, k):
    ss = [list(s) for s in strokes]
    i = rng.randrange(len(ss))
    dx, dy = rng.choice([(0,-110),(0,100),(130,0),(-120,0)])
    ss.append([(x+dx*k, y+dy*k) for x, y in ss[i]])
    y = rng.uniform(150, 560)
    ss.append([(70, y), (70 + 300*min(1, 0.4+0.6*k), y)])
    return render([jitter(s, 6*k, rng) for s in ss])


def m5_gaps(strokes, rng, k):
    geoms = []
    for s in strokes:
        pts = resample(s); ls = LineString(pts)
        if ls.length > 260:
            a = rng.uniform(-0.12, 0.10)*k; b = 1 + rng.uniform(-0.10, 0.14)*k
            p0 = ls.interpolate(max(0, a), normalized=True).coords[0]
            p1 = ls.interpolate(min(1, b), normalized=True).coords[0]
            if a < 0:
                (x0,y0),(x1,y1) = pts[0], pts[1]; d = math.hypot(x1-x0, y1-y0) or 1
                p0 = (x0 - (x1-x0)/d*(-a*ls.length), y0 - (y1-y0)/d*(-a*ls.length))
            if b > 1:
                (x0,y0),(x1,y1) = pts[-2], pts[-1]; d = math.hypot(x1-x0, y1-y0) or 1
                p1 = (x1 + (x1-x0)/d*((b-1)*ls.length), y1 + (y1-y0)/d*((b-1)*ls.length))
            inner = [c for c in pts if max(0,a)+0.02 < ls.project(Point(c), normalized=True) < min(1,b)-0.02]
            pts = [p0] + inner + [p1]
        geoms.append(ink(pts, rng.choice([1-0.5*k, 1-0.25*k, 1.0, 1+0.5*k])))
    return unary_union(geoms)


def m6_hybrid(strokes, rng, k):
    ss = [jitter(s, 7*k, rng) for s in strokes]
    donors = [n for n in G if G[n][0] and '.' not in n and n not in ('space',)]
    part = rng.choice(G[rng.choice(donors)][0])
    sx = rng.uniform(0.6, 0.95); ox = rng.uniform(-40, 160)*k; oy = rng.uniform(-120, 80)*k
    ss.append([(x*sx+ox, y*sx+oy) for x, y in part])
    x, y = ss[0][0]
    ss.append([(x-60*k, y), (x+60*k, y)])
    return render(ss)


RECIPES = [m1_wobble, m2_drop_extra, m3_melt, m4_duplicate, m5_gaps, m6_hybrid]

# ---------------------------------------------------------------- outline -> glyf
def geom_to_glyph(geom, tol=1.2):
    pen = TTGlyphPen(None)
    if geom is None or geom.is_empty:
        return pen.glyph()
    geom = geom.buffer(0).simplify(tol, preserve_topology=True)
    polys = [geom] if geom.geom_type == 'Polygon' else [p for p in geom.geoms if p.geom_type == 'Polygon']
    for p in polys:
        p = orient(p, sign=-1.0)      # TrueType: outer clockwise (y-up), holes counter-clockwise
        rings = [p.exterior] + list(p.interiors)
        for ring in rings:
            coords = [(round(x), round(y)) for x, y in ring.coords[:-1]]
            if len(coords) < 3:
                continue
            pen.moveTo(coords[0])
            for c in coords[1:]:
                pen.lineTo(c)
            pen.closePath()
    return pen.glyph()

# ---------------------------------------------------------------- features
def build_features(bases):
    letters = [n for n in bases if n != 'space']
    alt = lambda n, i: n if i == 1 else f'{n}.s{i}'
    L = []
    for i in range(1, 7):
        L.append(f'@s{i} = [{" ".join(alt(n, i) for n in letters)}];')
    L.append(f'@clean = [{" ".join(n + ".clean" for n in letters)}];')
    L.append('@sep = [space period comma colon semicolon hyphen quotesingle quotedbl];')

    def allv(n):  # every variant of a base glyph
        return [alt(n, i) for i in range(1, 7)] + [n + '.clean']

    # stem merge
    lstem = [v for n in LEFT_STEM for v in allv(n)] + [v for n in MERGE for v in allv(n + '.merge')]
    L.append(f'@lstem = [{" ".join(lstem)}];')
    L.append('lookup merge {')
    for n in MERGE:
        for i in range(1, 7):
            L.append(f"  sub {alt(n, i)}' @lstem by {alt(n + '.merge', i)};")
        L.append(f"  sub {n}.clean' @lstem by {n}.merge.clean;")
    L.append('} merge;')

    # pseudo-random cycle: 1->4->2->6->3->5->1, keyed on previous letter (optionally across a separator)
    perm = {1: 4, 4: 2, 2: 6, 6: 3, 3: 5, 5: 1}
    L.append('lookup cycle {')
    for a, b in perm.items():
        L.append(f"  sub @s{a} @s1' by @s{b};")
        L.append(f"  sub @s{a} @sep @s1' by @s{b};")
    L.append('} cycle;')
    # second scramble keyed two back, so runs like 'aaaa' don't look periodic
    L.append('lookup scramble {')
    for a in (2, 5):
        for b in range(1, 7):
            c = b % 6 + 1
            L.append(f"  sub @s{a} @s{b} @s{b}' by @s{c};")
    L.append('} scramble;')

    L.append('feature calt { lookup merge; lookup cycle; lookup scramble; } calt;')
    for i in range(1, 7):
        L.append(f'feature ss{i:02d} {{')
        for n in letters:
            L.append(f'  sub [{" ".join(allv(n))}] by {alt(n, i)};')
        L.append(f'}} ss{i:02d};')
    L.append('feature ss07 {')
    for n in letters:
        L.append(f'  sub [{" ".join(allv(n))}] by {n}.clean;')
    L.append('} ss07;')

    # ---- over-kerning fusions
    def cls(name, names):
        L.append(f'@{name} = [{" ".join(v for n in names for v in allv(n))}];')
    # right-edge vertical stems (letters that keep their stem) -> left stems: overlap ~65%
    rstem = {'U': 520, 'I': 80, 'a': 480, 'd': 520, 'q': 520, 'u': 520, 'i': 80, 'l': 220 and 80}
    cls('lstemk', LEFT_STEM)
    L.append('feature kern {')
    for n, x in rstem.items():
        adv = G[n][1]
        L.append(f'  pos [{" ".join(allv(n))}] @lstemk {int(0.8*W - (adv - x) - 80)};')
    # bowls
    rbowl = {'o': 530, 'b': 520, 'p': 520, 'O': 620, 'D': 560, 'Q': 620, 'e': 515}
    lbowl = {'o': 70, 'c': 80, 'd': 80, 'e': 85, 'q': 80, 'g': 80, 'a': 120, 'O': 60, 'C': 60, 'G': 60, 'Q': 60}
    for a, ax in rbowl.items():
        for b, bx in lbowl.items():
            if a.isupper() != b.isupper():
                continue
            L.append(f'  pos [{" ".join(allv(a))}] [{" ".join(allv(b))}] {int(-(G[a][1]-ax+bx) - 0.9*W)};')
    # bars
    bars = {'T': (60, 560), 'F': (80, 500), 'E': (80, 500), 'Z': (70, 530), 'f': (50, 330), 't': (50, 360)}
    for a, (a0, a1) in bars.items():
        for b, (b0, b1) in bars.items():
            if a.isupper() != b.isupper():
                continue
            L.append(f'  pos [{" ".join(allv(a))}] [{" ".join(allv(b))}] {int(-(G[a][1]-a1+b0) + 0.3*W)};')
    # parallel diagonals superimpose
    for a, b, gap in [('A','V',80),('V','A',80),('A','W',70),('W','A',70),('A','Y',80),('Y','A',80),
                      ('v','v',80),('w','w',60),('v','w',70),('w','v',70)]:
        L.append(f'  pos [{" ".join(allv(a))}] [{" ".join(allv(b))}] {int(-gap - 0.2*W)};')
    # misreads: rn -> m, cl -> d, oo already fused
    L.append(f'  pos [{" ".join(allv("r"))}] [{" ".join(allv("n"))}] {int(-(400-397+80) - 0.6*W)};')
    L.append(f'  pos [{" ".join(allv("c"))}] [{" ".join(allv("l"))}] {int(-(540-455+80) - 0.6*W)};')
    L.append('} kern;')
    return '\n'.join(L)

# ---------------------------------------------------------------- build
def build(intensity, style, out):
    bases = list(G.keys())
    glyphs, metrics, order = {}, {}, ['.notdef']
    glyphs['.notdef'] = geom_to_glyph(Polygon([(60,0),(60,CAP),(440,CAP),(440,0)]).difference(
        Polygon([(130,70),(130,CAP-70),(370,CAP-70),(370,70)])))
    metrics['.notdef'] = (500, 60)
    for n in bases:
        strokes, adv = G[n]
        variants = {'clean': render(strokes)}
        for i, rec in enumerate(RECIPES, 1):
            rng = random.Random(f'{n}:{i}')
            variants[i] = rec(strokes, rng, intensity) if strokes else Polygon()
        for key, geom in variants.items():
            gname = n if key == 1 else (f'{n}.clean' if key == 'clean' else f'{n}.s{key}')
            if n == 'space':
                if key != 1:
                    continue
            order.append(gname)
            glyphs[gname] = geom_to_glyph(geom)
            lsb = int(geom.bounds[0]) if not geom.is_empty else 0
            metrics[gname] = (adv, lsb)
    cmap = {ord(ch): gn for ch, gn in UNI.items()}
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ASC + 80, descent=DESC - 40)
    fb.setupNameTable({'familyName': 'Slop Sans', 'styleName': style,
                       'fullName': f'Slop Sans {style}', 'psName': f'SlopSans-{style}',
                       'uniqueFontIdentifier': f'SlopSans-{style};2026', 'version': 'Version 1.000',
                       'description': 'Humanist sans as rendered by a model that almost learned the alphabet.'})
    fb.setupOS2(sTypoAscender=ASC + 80, sTypoDescender=DESC - 40, sTypoLineGap=0,
                usWinAscent=ASC + 200, usWinDescent=-DESC + 120, sxHeight=XH, sCapHeight=CAP)
    fb.setupPost()
    fb.addOpenTypeFeatures(build_features(bases))
    fb.save(out)
    print(f'wrote {out}: {len(order)} glyphs')


if __name__ == '__main__':
    build(float(sys.argv[1]), sys.argv[2], sys.argv[3])
