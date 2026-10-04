"""Fabrication outputs: Gerbers + drill (zip), BOM and pick-and-place (JLCPCB format), images.

  python3 fab.py        (needs kicad-cli on PATH)
"""
import csv
import os
import shutil
import subprocess
import sys
import zipfile
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(__file__))
from design import PARTS  # noqa: E402

HW = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
PCB = os.path.join(HW, "lcd_f042.kicad_pcb")
OUT = os.path.join(HW, "fab")
GERB = os.path.join(OUT, "gerbers")


def run(*a):
    r = subprocess.run(a, capture_output=True, text=True)
    if r.returncode:
        print(r.stdout, r.stderr)
        raise SystemExit("failed: " + " ".join(a))


def gerbers():
    shutil.rmtree(GERB, ignore_errors=True)
    os.makedirs(GERB)
    run("kicad-cli", "pcb", "export", "gerbers", "-o", GERB + "/",
        "--layers", "F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts",
        "--subtract-soldermask", "--no-x2", PCB)
    run("kicad-cli", "pcb", "export", "drill", "-o", GERB + "/", "--format", "excellon",
        "--excellon-separate-th", "--generate-map", "--map-format", "gerberx2", PCB)
    z = os.path.join(OUT, "lcd_f042_gerbers.zip")
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as f:
        for n in sorted(os.listdir(GERB)):
            f.write(os.path.join(GERB, n), n)
    print("gerbers ->", z)


def bom():
    groups = OrderedDict()
    for p in sorted(PARTS, key=lambda p: (p.fp, p.value, p.ref)):
        if p.dnp or p.ref.startswith("TP"):
            continue
        key = (p.value, p.fp, p.mpn, p.lcsc)
        groups.setdefault(key, []).append(p.ref)
    path = os.path.join(OUT, "bom_jlcpcb.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "MPN", "LCSC Part #", "Qty"])
        for (val, fp, mpn, lcsc), refs in groups.items():
            refs.sort(key=lambda r: (r.rstrip("0123456789"), int("0" + r[len(r.rstrip("0123456789")):])))
            w.writerow([val, ",".join(refs), fp.split(":")[1], mpn, lcsc, len(refs)])
    print("bom ->", path)
    dnp = [p.ref for p in PARTS if p.dnp]
    print("not populated:", dnp)


def cpl():
    tmp = os.path.join(OUT, "pos_kicad.csv")
    run("kicad-cli", "pcb", "export", "pos", "-o", tmp, "--format", "csv", "--units", "mm",
        "--side", "front", PCB)
    dnp = {p.ref for p in PARTS if p.dnp} | {p.ref for p in PARTS if p.ref.startswith("TP")}
    path = os.path.join(OUT, "cpl_jlcpcb.csv")
    with open(tmp) as fi, open(path, "w", newline="") as fo:
        r = csv.DictReader(fi)
        w = csv.writer(fo)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for row in r:
            if row["Ref"] in dnp:
                continue
            w.writerow([row["Ref"], row["PosX"] + "mm", row["PosY"] + "mm", "Top", row["Rot"]])
    os.remove(tmp)
    print("cpl ->", path, "(rotations may need the usual JLC per-package offsets: check in their viewer)")


def images():
    img = os.path.join(HW, "..", "docs", "img")
    os.makedirs(img, exist_ok=True)
    for name, layers in [("f042_pcb_top", "F.Cu,F.SilkS,F.Mask,Edge.Cuts"), ("f042_pcb_bottom", "B.Cu,B.SilkS,Edge.Cuts"),
                         ("f042_pcb_assembly", "F.Fab,F.SilkS,Edge.Cuts,F.CrtYd")]:
        svg = os.path.join(img, name + ".svg")
        run("kicad-cli", "pcb", "export", "svg", "-o", svg, "--layers", layers, "--page-size-mode", "2",
            "--exclude-drawing-sheet", PCB)
        if shutil.which("rsvg-convert"):
            run("rsvg-convert", "-w", "1600", "-b", "white", svg, "-o", svg.replace(".svg", ".png"))
            os.remove(svg)
    sch = os.path.join(HW, "lcd_f042.kicad_sch")
    run("kicad-cli", "sch", "export", "pdf", "-o", os.path.join(HW, "..", "docs", "schematic_f042.pdf"), sch)
    print("images/pdf -> docs/")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    gerbers()
    bom()
    cpl()
    images()
