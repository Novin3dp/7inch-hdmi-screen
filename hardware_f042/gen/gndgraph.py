"""Union-find over GND pour fragments on both layers, linked by GND vias / PTH pads."""
import os
import pcbnew
HW = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
b = pcbnew.LoadBoard(os.path.join(HW, "lcd_f042.kicad_pcb"))
gnd = b.FindNet("GND").GetNetCode()
frags = []
for z in b.Zones():
    if z.GetNetCode() == gnd:
        L = z.GetLayer()
        fp = z.GetFilledPolysList(L)
        for i in range(fp.OutlineCount()):
            frags.append((b.GetLayerName(L), fp.Outline(i)))
par = list(range(len(frags)))
def f(a):
    while par[a] != a:
        par[a] = par[par[a]]; a = par[a]
    return a
links = [t.GetPosition() for t in b.GetTracks() if t.GetClass() == "PCB_VIA" and t.GetNetCode() == gnd]
links += [p.GetPosition() for fp in b.GetFootprints() for p in fp.Pads() if p.GetNetCode() == gnd and p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
for p in links:
    hit = [i for i, (L, ol) in enumerate(frags) if ol.PointInside(p, 400000)]
    for i in hit[1:]:
        par[f(i)] = f(hit[0])
comps = {}
for i in range(len(frags)):
    comps.setdefault(f(i), []).append(i)
print(len(frags), "fragments,", len(comps), "groups")
for k, v in sorted(comps.items(), key=lambda kv: len(kv[1])):
    if len(v) < 5:
        for i in v:
            bb = frags[i][1].BBox(); c = bb.Centre()
            print("small group", k, frags[i][0], round(c.x/1e6-100, 2), round(c.y/1e6-80, 2), round(bb.GetWidth()/1e6, 2), round(bb.GetHeight()/1e6, 2))

# report what sits in the small groups
import json, sys
main = max(comps.values(), key=len)
bad = []
for k, v in comps.items():
    if v is main:
        continue
    for i in v:
        L, ol = frags[i]
        for fp in b.GetFootprints():
            for p in fp.Pads():
                if p.GetNetCode() == gnd and ol.PointInside(p.GetPosition(), 100000):
                    print("  pad in group:", fp.GetReference(), p.GetNumber(), L)
        for t in b.GetTracks():
            if t.GetClass() == "PCB_VIA" and t.GetNetCode() == gnd and ol.PointInside(t.GetPosition(), 400000):
                bad.append([t.GetPosition().x / 1e6, t.GetPosition().y / 1e6])
print("vias in isolated groups:", bad)
if "--drop" in sys.argv:
    p = os.path.join(os.path.dirname(__file__), "bad_vias.json")
    old = json.load(open(p)) if os.path.exists(p) else []
    json.dump(old + bad, open(p, "w"))
