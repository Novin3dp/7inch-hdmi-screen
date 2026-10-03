"""Autoroute the remaining nets with Freerouting and finish the board.

  python3.12 route.py export   -> lcd_dsi.dsn  (zones + temporary keepouts added)
  java -jar freerouting.jar -de lcd_dsi.dsn -do lcd_dsi.ses -mp 40
  python3.12 route.py import   -> imports .ses, removes temp keepouts, fills zones
"""
import os
import re
import sys

import pcbnew

import _shared  # noqa: F401  (sexpr, silk from hardware/gen)

sys.path.insert(0, os.path.dirname(__file__))

HW = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
BRD = os.path.join(HW, "lcd_dsi.kicad_pcb")
DSN = os.path.join(HW, "lcd_dsi.dsn")
SES = os.path.join(HW, "lcd_dsi.ses")

def export():
    b = pcbnew.LoadBoard(BRD)
    ok = pcbnew.ExportSpecctraDSN(b, DSN)
    print("DSN export", ok, DSN)
    fix_classes(b)


PWR_HI = ["+5V_IN", "+5V", "BOOST_IN", "AVDD_SW", "BL_SW"]
GND_CLS = ["GND"]
PWR = ["+3V3", "ICN_VCORE", "AVDD", "VLED_A", "VLED_K", "VGH", "VGL", "VCOM", "VGH_RAW", "VGL_RAW"]


def fix_classes(b):
    """KiCad 7 keeps net-class assignments in the project file; write them into the DSN."""
    txt = open(DSN).read()
    a = txt.index("    (class kicad_default")
    e = txt.index("  (wiring")
    names = sorted(str(n) for n in b.GetNetsByName().keys() if str(n))
    q = lambda n: '"%s"' % n if any(c in n for c in "+-()") else n
    sig = [n for n in names if n not in PWR_HI + PWR + GND_CLS]

    def cls(name, nets, w, cl, via):
        return ('    (class %s "" %s\n      (circuit (use_via %s))\n      (rule (width %d) (clearance %.1f))\n    )\n'
                % (name, " ".join(q(n) for n in nets), via, w, cl))
    block = (cls("kicad_default", sig, 150, 150.1, "Via[0-1]_600:300_um") +
             cls("PWR", PWR, 250, 150.1, "Via[0-1]_600:300_um") +
             cls("PWR_HI", PWR_HI, 500, 200.1, "Via[0-1]_800:400_um") +
             cls("GNDC", GND_CLS, 250, 150.1, "Via[0-1]_600:300_um") + "  )\n")
    txt = txt[:a] + block + txt[e:]
    # KiCad 7 drops fixed vias of some nets from the DSN: add every board via explicitly
    have = set(re.findall(r'\(via "[^"]+"\s+(-?[\d.]+) (-?[\d.]+)', txt))
    extra = ""
    for t in b.GetTracks():
        if t.GetClass() != "PCB_VIA":
            continue
        x, y = t.GetPosition().x / 1000.0, -t.GetPosition().y / 1000.0
        key = ("%g" % x, "%g" % y)
        if key in have:
            continue
        n = t.GetNetname()
        n = '"%s"' % n if any(c in n for c in "+-()") else n
        extra += '    (via "Via[0-1]_600:300_um"  %g %g (net %s)(type fix))\n' % (x, y, n)
    i = txt.index("  (wiring") + len("  (wiring\n")
    txt = txt[:i] + extra + txt[i:]
    open(DSN, "w").write(txt)


def do_import():
    """Read the Freerouting .ses directly (KiCad 7's python ImportSpecctraSES needs the GUI board)."""
    from sexpr import parse, find, find1
    import pcb
    stage2 = "--stage2" in sys.argv
    b = pcb.make(prep=stage2)
    ses_paths = [a for a in sys.argv[2:] if a.endswith(".ses")] or [SES]
    nets_out = []
    for sp in ses_paths:
        ses = parse(open(sp).read())
        routes = find1(ses, "routes")
        nets_out += find(find1(routes, "network_out"), "net")
    res = float(find1(routes, "resolution")[2])          # units per um
    k = 1000.0 / res                                      # -> KiCad nm
    pass
    nw = nv = 0
    for n in nets_out:
        ni = b.FindNet(str(n[1]))
        for w in find(n, "wire"):
            path = find1(w, "path")
            layer = b.GetLayerID(str(path[1]))
            width = float(path[2]) * k
            c = [float(v) for v in path[3:]]
            pts = [(c[i] * k, -c[i + 1] * k) for i in range(0, len(c), 2)]
            for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
                t = pcbnew.PCB_TRACK(b)
                t.SetStart(pcbnew.VECTOR2I(int(x1), int(y1)))
                t.SetEnd(pcbnew.VECTOR2I(int(x2), int(y2)))
                t.SetWidth(int(width))
                t.SetLayer(layer)
                t.SetNet(ni)
                t.SetLocked(stage2)
                b.Add(t)
                nw += 1
        for v in find(n, "via"):
            name = str(v[1])
            d, drill = [int(x) for x in name.split("_")[-2].split(":")]
            vi = pcbnew.PCB_VIA(b)
            vi.SetPosition(pcbnew.VECTOR2I(int(float(v[2]) * k), int(-float(v[3]) * k)))
            vi.SetWidth(pcbnew.FromMM(d / 1000.0))
            vi.SetDrill(pcbnew.FromMM(drill / 1000.0))
            vi.SetNet(ni)
            vi.SetLocked(stage2)
            b.Add(vi)
            nv += 1
    print("imported %d segments, %d vias" % (nw, nv))
    if stage2:
        b.Save(BRD)
        ok = pcbnew.ExportSpecctraDSN(b, DSN)
        fix_classes(b)
        print("stage-2 DSN written", ok)
        return
    prune_dangling(b)
    fanout_gnd(b)
    stitch(b)
    import silk
    from pcb import OX, OY, W, H
    silk.place_labels(b, OX, OY, W, H)
    b.Save(BRD)
    print("saved", BRD)


def prune_dangling(b):
    """Delete track segments with a free end (unused escape stubs the router bypassed)."""
    removed = 0
    while True:
        tracks = [t for t in b.GetTracks() if t.GetClass() != "PCB_VIA"]
        vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
        pads = [p for fp in b.GetFootprints() for p in fp.Pads()]
        dead = []
        for t in tracks:
            nc = t.GetNetCode()
            same = [o for o in tracks if o is not t and o.GetNetCode() == nc and o.GetLayer() == t.GetLayer()]
            for end in (t.GetStart(), t.GetEnd()):
                hit = any(p.GetNetCode() == nc and p.HitTest(end) for p in pads) or \
                    any(v.GetNetCode() == nc and v.HitTest(end) for v in vias) or \
                    any(o.HitTest(end, 0) for o in same)
                if hit:
                    continue
                # free end: keep the segment if another track joins it part-way (a T joint)
                other = t.GetEnd() if end == t.GetStart() else t.GetStart()
                joined = [q for o in same for q in (o.GetStart(), o.GetEnd())
                          if t.HitTest(q, 0) and (q - other).EuclideanNorm() > t.GetWidth()]
                if not joined:
                    dead.append(t)
                else:                         # trim the antenna back to the outermost joint
                    q = max(joined, key=lambda q: (q - other).EuclideanNorm())
                    if end == t.GetStart():
                        t.SetStart(q)
                    else:
                        t.SetEnd(q)
                break
        if not dead:
            # drop zero-length leftovers and segments lying entirely on a wider/equal same-net track
            dead = []
            for t in tracks:      # sequential, so one of two identical duplicates survives
                if (t.GetStart() - t.GetEnd()).EuclideanNorm() < 50000 or \
                        any(o is not t and o not in dead and o.GetNetCode() == t.GetNetCode() and
                            o.GetLayer() == t.GetLayer() and o.GetWidth() >= t.GetWidth() and
                            o.HitTest(t.GetStart(), 0) and o.HitTest(t.GetEnd(), 0) for o in tracks):
                    dead.append(t)
            if not dead:
                break
        for t in dead:
            b.Remove(t)
        removed += len(dead)
    print("dangling segments removed:", removed)


def geometry(b, netcode):
    nm = 1e-6
    segs, circles, boxes = [], [], []
    for t in b.GetTracks():
        same = t.GetNetCode() == netcode
        if t.GetClass() == "PCB_VIA":
            p = t.GetPosition()
            circles.append((p.x * nm, p.y * nm, t.GetWidth() * nm / 2, same))
        else:
            s, e = t.GetStart(), t.GetEnd()
            segs.append((s.x * nm, s.y * nm, e.x * nm, e.y * nm, t.GetWidth() * nm / 2, same))
    for fp in b.GetFootprints():
        for p in fp.Pads():
            bb = p.GetBoundingBox()
            boxes.append((bb.GetLeft() * nm, bb.GetTop() * nm, bb.GetRight() * nm, bb.GetBottom() * nm,
                          p.GetNetCode() == netcode, p))
    return segs, circles, boxes


def _segd(px, py, x1, y1, x2, y2):
    import math
    dx, dy = x2 - x1, y2 - y1
    L = dx * dx + dy * dy
    u = 0 if L == 0 else max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / L))
    return math.hypot(px - x1 - u * dx, py - y1 - u * dy)


def _seg_seg(a, b_):
    (x1, y1, x2, y2), (x3, y3, x4, y4) = a, b_

    def ccw(ax, ay, bx, by, cx, cy):
        return (cy - ay) * (bx - ax) - (by - ay) * (cx - ax)
    d1, d2 = ccw(x3, y3, x4, y4, x1, y1), ccw(x3, y3, x4, y4, x2, y2)
    d3, d4 = ccw(x1, y1, x2, y2, x3, y3), ccw(x1, y1, x2, y2, x4, y4)
    if (d1 > 0) != (d2 > 0) and (d3 > 0) != (d4 > 0):
        return 0.0
    return min(_segd(x1, y1, x3, y3, x4, y4), _segd(x2, y2, x3, y3, x4, y4),
               _segd(x3, y3, x1, y1, x2, y2), _segd(x4, y4, x1, y1, x2, y2))


def fanout_gnd(b):
    """Give every GND SMD pad that has no track a short trace to its own via (2-layer GND fanout)."""
    import math
    from pcb import OX, OY, W, H, VIA_D, VIA_DRILL
    gnd = b.FindNet("GND")
    gc = gnd.GetNetCode()
    segs, circles, boxes = geometry(b, gc)
    r, cl, hw = VIA_D / 2, 0.2, 0.15
    nm = 1e-6
    n = 0
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if fp.GetReference() == "U1" and p.GetNumber() == "49":
                continue                      # exposed pad already has its via array
            if p.GetNetCode() != gc or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            bb = p.GetBoundingBox()
            L, T, R_, B = bb.GetLeft() * nm, bb.GetTop() * nm, bb.GetRight() * nm, bb.GetBottom() * nm
            if any(L - 0.01 <= x <= R_ + 0.01 and T - 0.01 <= y <= B + 0.01
                   for (x1, y1, x2, y2, w, s) in segs if s for (x, y) in ((x1, y1), (x2, y2))):
                continue
            if any(L - c[2] < c[0] < R_ + c[2] and T - c[2] < c[1] < B + c[2] for c in circles if c[3]):
                continue
            cx, cy = p.GetPosition().x * nm, p.GetPosition().y * nm
            done = False
            for d in [0.9 + 0.15 * i for i in range(10)]:
                for k in range(24):
                    a = 2 * math.pi * k / 24
                    vx, vy = cx + d * math.cos(a), cy + d * math.sin(a)
                    if not (OX + 0.8 < vx < OX + W - 0.8 and OY + 0.8 < vy < OY + H - 0.8):
                        continue
                    ok = all(_segd(vx, vy, *sg[:4]) >= r + sg[4] + cl for sg in segs if not sg[5])
                    ok = ok and all(math.hypot(vx - c[0], vy - c[1]) >= r + c[2] + 0.2 for c in circles)
                    ok = ok and all(not (bx[0] - r - cl < vx < bx[2] + r + cl and bx[1] - r - cl < vy < bx[3] + r + cl)
                                    for bx in boxes if not bx[4])
                    if not ok:
                        continue
                    seg = (cx, cy, vx, vy)
                    ok = all(_seg_seg(seg, sg[:4]) >= hw + sg[4] + cl for sg in segs if not sg[5])
                    if ok:
                        for bx in boxes:
                            if bx[4]:
                                continue
                            for t in [i / 12 for i in range(13)]:
                                qx, qy = cx + (vx - cx) * t, cy + (vy - cy) * t
                                if bx[0] - hw - cl < qx < bx[2] + hw + cl and bx[1] - hw - cl < qy < bx[3] + hw + cl:
                                    ok = False
                                    break
                            if not ok:
                                break
                    if not ok:
                        continue
                    t = pcbnew.PCB_TRACK(b)
                    t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(cx), pcbnew.FromMM(cy)))
                    t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(vx), pcbnew.FromMM(vy)))
                    t.SetWidth(pcbnew.FromMM(2 * hw))
                    t.SetLayer(pcbnew.F_Cu)
                    t.SetNet(gnd)
                    b.Add(t)
                    v = pcbnew.PCB_VIA(b)
                    v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(vx), pcbnew.FromMM(vy)))
                    v.SetWidth(pcbnew.FromMM(VIA_D))
                    v.SetDrill(pcbnew.FromMM(VIA_DRILL))
                    v.SetNet(gnd)
                    b.Add(v)
                    segs.append((cx, cy, vx, vy, hw, True))
                    circles.append((vx, vy, r, True))
                    n += 1
                    done = True
                    break
                if done:
                    break
            if not done:
                print("fanout: no room for", fp.GetReference(), p.GetNumber())
    print("GND fanout vias:", n)


def stitch(b, pitch=2.0, edge=1.0):
    """Add GND stitching vias wherever there is room (ties the two GND pours together)."""
    import math
    from pcb import OX, OY, W, H, VIA_D, VIA_DRILL
    gnd = b.FindNet("GND")
    nm = 1e-6
    segs, circles, boxes = [], [], []
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            p = t.GetPosition()
            circles.append((p.x * nm, p.y * nm, t.GetWidth() * nm / 2, t.GetNetCode() == gnd.GetNetCode()))
        else:
            s, e = t.GetStart(), t.GetEnd()
            segs.append((s.x * nm, s.y * nm, e.x * nm, e.y * nm, t.GetWidth() * nm / 2,
                         t.GetNetCode() == gnd.GetNetCode()))
    for fp in b.GetFootprints():
        for p in fp.Pads():
            bb = p.GetBoundingBox()
            boxes.append((bb.GetLeft() * nm, bb.GetTop() * nm, bb.GetRight() * nm, bb.GetBottom() * nm,
                          p.GetNetCode() == gnd.GetNetCode() and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD))
    r = VIA_D / 2
    cl = 0.25
    import json
    bp = os.path.join(os.path.dirname(__file__), "bad_vias.json")
    bad = json.load(open(bp)) if os.path.exists(bp) else []

    def segd(px, py, x1, y1, x2, y2):
        dx, dy = x2 - x1, y2 - y1
        L = dx * dx + dy * dy
        u = 0 if L == 0 else max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / L))
        return math.hypot(px - x1 - u * dx, py - y1 - u * dy)
    n = 0
    y = edge
    while y <= H - edge:
        x = edge
        while x <= W - edge:
            px, py = OX + x, OY + y
            ok = not any(abs(px - bx) < 0.05 and abs(py - by) < 0.05 for bx, by in bad)
            for ccx, ccy in ((2, 2), (W - 2, 2), (2, H - 2), (W - 2, H - 2)):
                if abs(x - ccx) < 2 and abs(y - ccy) < 2 and (x - ccx) * (ccx - W / 2) > 0 \
                        and (y - ccy) * (ccy - H / 2) > 0 and math.hypot(x - ccx, y - ccy) > 2 - edge:
                    ok = False
            for (x1, y1, x2, y2, hw, same) in segs:
                need = r + hw + (0.05 if same else cl)
                if segd(px, py, x1, y1, x2, y2) < need:
                    ok = False
                    break
            if ok:
                for (cx, cy, cr, same) in circles:
                    if math.hypot(px - cx, py - cy) < r + cr + 0.3:
                        ok = False
                        break
            if ok:
                for (l, t, rr, bt, same) in boxes:
                    m = r + (0.3 if same else cl + 0.1)
                    if l - m < px < rr + m and t - m < py < bt + m:
                        ok = False
                        break
            if ok:
                v = pcbnew.PCB_VIA(b)
                v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(px), pcbnew.FromMM(py)))
                v.SetWidth(pcbnew.FromMM(VIA_D))
                v.SetDrill(pcbnew.FromMM(VIA_DRILL))
                v.SetNet(gnd)
                b.Add(v)
                circles.append((px, py, r, True))
                n += 1
            x += pitch
        y += pitch
    ep = os.path.join(os.path.dirname(__file__), "extra_vias.json")
    for px, py in (json.load(open(ep)) if os.path.exists(ep) else []):
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(px), pcbnew.FromMM(py)))
        v.SetWidth(pcbnew.FromMM(VIA_D))
        v.SetDrill(pcbnew.FromMM(VIA_DRILL))
        v.SetNet(gnd)
        b.Add(v)
        n += 1
    print("stitching vias:", n)


if __name__ == "__main__":
    {"export": export, "import": do_import}[sys.argv[1]]()
