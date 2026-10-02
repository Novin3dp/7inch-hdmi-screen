"""List GND pour fragments that contain no via / through-hole pad (not tied to the other layer)."""
import os
import pcbnew
HW = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
b = pcbnew.LoadBoard(os.path.join(HW, "lcd_board.kicad_pcb"))
gnd = b.FindNet("GND").GetNetCode()
pts = []
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA" and t.GetNetCode() == gnd:
        pts.append(t.GetPosition())
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetNetCode() == gnd and p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
            pts.append(p.GetPosition())
res = []
for z in b.Zones():
    if z.GetNetCode() != gnd:
        continue
    layer = z.GetLayer()
    fp = z.GetFilledPolysList(layer)
    for i in range(fp.OutlineCount()):
        ol = fp.Outline(i)
        bb = ol.BBox()
        has = any(ol.PointInside(p, 400000) for p in pts)
        if not has:
            area = abs(ol.Area()) / 1e12
            c = bb.Centre()
            res.append((b.GetLayerName(layer), round(c.x / 1e6 - 100, 2), round(c.y / 1e6 - 80, 2), round(area, 2),
                        round(bb.GetWidth() / 1e6, 2), round(bb.GetHeight() / 1e6, 2)))
for r in sorted(res, key=lambda r: -r[3]):
    print(r)
print(len(res), "fragments without via")

# ---- add a via inside every unstitched fragment where both layers have GND copper
import json
import math
import sys
if "--fix" in sys.argv:
    fills = {}
    for z in b.Zones():
        if z.GetNetCode() == gnd:
            fills[z.GetLayer()] = z.GetFilledPolysList(z.GetLayer())
    other = {pcbnew.F_Cu: pcbnew.B_Cu, pcbnew.B_Cu: pcbnew.F_Cu}
    R = 0.36
    added = []
    for z in b.Zones():
        if z.GetNetCode() != gnd:
            continue
        L = z.GetLayer()
        fp = fills[L]
        for i in range(fp.OutlineCount()):
            ol = fp.Outline(i)
            if any(ol.PointInside(p, 400000) for p in pts):
                continue
            bb = ol.BBox()
            done = False
            step = 150000
            y = bb.GetTop()
            while y <= bb.GetBottom() and not done:
                x = bb.GetLeft()
                while x <= bb.GetRight() and not done:
                    ok = True
                    for k in range(12):
                        a = 2 * math.pi * k / 12
                        q = pcbnew.VECTOR2I(int(x + R * 1e6 * math.cos(a)), int(y + R * 1e6 * math.sin(a)))
                        if not fp.Contains(q) or not fills[other[L]].Contains(q):
                            ok = False
                            break
                    if ok and fp.Contains(pcbnew.VECTOR2I(int(x), int(y))):
                        added.append([x / 1e6, y / 1e6])
                        done = True
                    x += step
                y += step
    path = os.path.join(os.path.dirname(__file__), "extra_vias.json")
    old = json.load(open(path)) if os.path.exists(path) else []
    json.dump(old + added, open(path, "w"))
    print("added", len(added), "island vias")
