"""Run DRC on the board and print a summary.  python3.12 check.py [board] [--fill] [--all]"""
import collections
import os
import re
import sys

import pcbnew

HW = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
path = next((a for a in sys.argv[1:] if a.endswith(".kicad_pcb")), os.path.join(HW, "lcd_board.kicad_pcb"))
b = pcbnew.LoadBoard(path)
if "--fill" in sys.argv:
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.Save(path)
    b = pcbnew.LoadBoard(path)
rep = "/tmp/drc_report.txt"
pcbnew.WriteDRCReport(b, rep, pcbnew.EDA_UNITS_MILLIMETRES, True)
txt = open(rep).read()
items = re.findall(r"^\[(\w+)\]: (.*?)\n((?:    .*\n)+)", txt, re.M)
cnt = collections.Counter(k for k, _, _ in items)
print(dict(cnt))
# remember stitching vias that only touch one layer so the next import skips them
import json
bad = []
for k, msg, body in items:
    if k == "via_dangling":
        m = re.search(r"@\(([\d.]+) mm, ([\d.]+) mm\): Via \[GND\]", body)
        if m:
            bad.append([float(m.group(1)), float(m.group(2))])
if "--fill" in sys.argv:
    old = json.load(open(os.path.join(os.path.dirname(__file__), "bad_vias.json"))) if os.path.exists(
        os.path.join(os.path.dirname(__file__), "bad_vias.json")) else []
    json.dump(old + bad, open(os.path.join(os.path.dirname(__file__), "bad_vias.json"), "w"))
show = "--all" in sys.argv
for k, msg, body in items:
    if k == "unconnected_items" and not show:
        continue
    if k in ("silk_overlap", "silk_over_copper", "silk_edge_clearance", "text_height", "text_thickness", "lib_footprint_mismatch", "lib_footprint_issues") and not show:
        continue
    print(k, msg, body.strip().replace("\n", " | ")[:300])
