"""Generate the hierarchical KiCad schematic from design.py.

Every symbol pin gets a short wire and a global label carrying its net name (or a no-connect
flag), so the schematic is electrically identical to the PCB netlist and fully readable.
"""
import os
import uuid

from sexpr import Sym, dump, find, find1
import symlib
from design import PARTS, SHEETS

HW = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
PROJECT = "lcd_board"
LOCAL_SYMLIB = os.path.join(HW, "lcd_board.kicad_sym")
ROOT_UUID = "0a6b6d8e-3f1c-4c1d-9a7e-2b8f1c000001"
G = 1.27


def U():
    return str(uuid.uuid4())


def snap(v):
    return round(v / G) * G


def lib_path(lib):
    return LOCAL_SYMLIB if lib == "lcd_board" else lib


def flat_symbol(lib, name):
    """Return the symbol flattened (extends resolved) and renamed to 'lib:name'."""
    s, base = symlib.get_symbol(lib_path(lib), name)
    full = "%s:%s" % (lib, name)
    out = [Sym("symbol"), full]
    src_body = base if base is not None else s
    for e in src_body[2:]:
        if isinstance(e, list) and e and e[0] in ("property", "symbol", "extends"):
            continue
        out.append(e)
    props = {}
    for e in find(src_body, "property"):
        props[e[1]] = e
    for e in find(s, "property"):
        props[e[1]] = e
    for p in props.values():
        out.append(p)
    bname = src_body[1]
    for sub in find(src_body, "symbol"):
        sub = list(sub)
        sub[1] = name + sub[1][len(bname):]
        out.append(sub)
    return out


def sym_pins(lib, name):
    return symlib.pins(lib_path(lib), name)


def sym_bbox(lib, name):
    ps = sym_pins(lib, name)
    xs = [p["x"] for p in ps] + [0]
    ys = [p["y"] for p in ps] + [0]
    return min(xs), min(ys), max(xs), max(ys)


def text_len(s):
    return len(s) * 1.0 + 3.0


def effects(hide=False, justify=None, size=1.27):
    e = [Sym("effects"), [Sym("font"), [Sym("size"), size, size]]]
    if justify:
        e.append([Sym("justify")] + [Sym(j) for j in justify.split()])
    if hide:
        e.append(Sym("hide"))
    return e


def place_parts(parts):
    """Shelf-pack symbols; returns {ref: (x, y)} and page size."""
    items = []
    for p in parts:
        x0, y0, x1, y1 = sym_bbox(p.lib, p.sym)
        nets = [n for n in p.pins.values() if n]
        lab = max([text_len(n) for n in nets] + [4])
        w = (x1 - x0) + 2 * (lab + 3) + 6
        h = (y1 - y0) + 12
        items.append((p, x0, y0, x1, y1, w, h, lab))
    items.sort(key=lambda t: -t[6])
    maxw = 380
    x, y, rowh = 15.0, 30.0, 0.0
    pos = {}
    for p, x0, y0, x1, y1, w, h, lab in items:
        if x + w > maxw:
            x, y, rowh = 15.0, y + rowh, 0.0
        ox = snap(x + lab + 3 - x0)
        oy = snap(y + 6 + y1)          # lib y up -> top of symbol at y+6
        pos[p.ref] = (ox, oy)
        x += w
        rowh = max(rowh, h)
    height = y + rowh + 20
    if height <= 277 and maxw <= 400:
        paper = "A3"
    elif height <= 400:
        paper = "A2"
    else:
        paper = "A1"
    return pos, paper


def sheet_file(name):
    return "%s_%s.kicad_sch" % (PROJECT, name)


def build_sheet(sheet, title, page, sheet_uuid):
    parts = [p for p in PARTS if p.sheet == sheet]
    pos, paper = place_parts(parts)
    used = sorted({(p.lib, p.sym) for p in parts})
    lib_symbols = [Sym("lib_symbols")] + [flat_symbol(l, n) for l, n in used]
    body = [Sym("kicad_sch"), [Sym("version"), 20230121], [Sym("generator"), Sym("eeschema")],
            [Sym("uuid"), sheet_uuid], [Sym("paper"), paper],
            [Sym("title_block"), [Sym("title"), title], [Sym("date"), "2026-10-02"], [Sym("rev"), "1.0"],
             [Sym("company"), "AT070TN92 HDMI + USB touch driver"],
             [Sym("comment"), 1, "Generated from hardware/gen/design.py - edit the generator, not this file"]],
            lib_symbols]
    for p in parts:
        ox, oy = pos[p.ref]
        x0, y0, x1, y1 = sym_bbox(p.lib, p.sym)
        inst = [Sym("symbol"), [Sym("lib_id"), "%s:%s" % (p.lib, p.sym)], [Sym("at"), ox, oy, 0],
                [Sym("unit"), 1], [Sym("in_bom"), Sym("yes")], [Sym("on_board"), Sym("yes")],
                [Sym("dnp"), Sym("yes" if p.dnp else "no")], [Sym("uuid"), U()],
                [Sym("property"), "Reference", p.ref, [Sym("at"), ox, snap(oy - y1 - 2.54), 0], effects()],
                [Sym("property"), "Value", p.value, [Sym("at"), ox, snap(oy - y0 + 2.54), 0], effects()],
                [Sym("property"), "Footprint", p.fp, [Sym("at"), ox, oy, 0], effects(hide=True)],
                [Sym("property"), "Datasheet", "", [Sym("at"), ox, oy, 0], effects(hide=True)],
                [Sym("property"), "MPN", p.mpn, [Sym("at"), ox, oy, 0], effects(hide=True)],
                [Sym("property"), "LCSC", p.lcsc, [Sym("at"), ox, oy, 0], effects(hide=True)]]
        for pin in sym_pins(p.lib, p.sym):
            inst.append([Sym("pin"), pin["num"], [Sym("uuid"), U()]])
        inst.append([Sym("instances"), [Sym("project"), PROJECT,
                     [Sym("path"), "/%s/%s" % (ROOT_UUID, sheet_uuid), [Sym("reference"), p.ref], [Sym("unit"), 1]]]])
        body.append(inst)
        # labels
        done = {}
        for pin in sym_pins(p.lib, p.sym):
            px, py = round(ox + pin["x"], 2), round(oy - pin["y"], 2)
            net = p.pins.get(pin["num"], "__missing__")
            if net == "__missing__":
                raise SystemExit("pin %s of %s has no net assignment" % (pin["num"], p.ref))
            key = (px, py)
            if key in done:
                if done[key] != net:
                    raise SystemExit("stacked pins with different nets: %s %s" % (p.ref, pin["num"]))
                continue
            done[key] = net
            r = int(pin["rot"]) % 360
            d = {0: (-1, 0), 180: (1, 0), 90: (0, 1), 270: (0, -1)}[r]
            if net is None:
                body.append([Sym("no_connect"), [Sym("at"), px, py], [Sym("uuid"), U()]])
                continue
            L = 2.54
            ex, ey = round(px + d[0] * L, 2), round(py + d[1] * L, 2)
            body.append([Sym("wire"), [Sym("pts"), [Sym("xy"), px, py], [Sym("xy"), ex, ey]],
                         [Sym("stroke"), [Sym("width"), 0], [Sym("type"), Sym("default")]], [Sym("uuid"), U()]])
            ang = {(-1, 0): 180, (1, 0): 0, (0, 1): 270, (0, -1): 90}[d]
            just = "right" if ang == 180 else "left"
            body.append([Sym("global_label"), net, [Sym("shape"), Sym("passive")], [Sym("at"), ex, ey, ang],
                         [Sym("fields_autoplaced")], effects(justify=just), [Sym("uuid"), U()],
                         [Sym("property"), "Intersheetrefs", "${INTERSHEET_REFS}", [Sym("at"), ex, ey, 0],
                          effects(hide=True)]])
    with open(os.path.join(HW, sheet_file(sheet)), "w") as f:
        f.write(dump(body) + "\n")


NOTES = [
    "AT070TN92 7\" 800x480 TTL panel driver: HDMI (LT8619C) + GT915 touch -> USB HID (STM32F072).",
    "Power: USB-C 5 V (from Raspberry Pi USB port, ~0.7 A max with backlight at 100 %).",
    "Panel power-up order (MCU controlled): DVDD -> RESET -> VGL/AVDD -> VGH -> data -> backlight.",
    "J3 pad numbers equal AT070TN92 FPC pin numbers; use a TOP-contact 0.5 mm 50-pin FPC connector.",
    "VCOM (pins 6/46) is adjustable with RV1 (2.55..4.5 V): trim for minimum flicker.",
]


def build_root():
    root = [Sym("kicad_sch"), [Sym("version"), 20230121], [Sym("generator"), Sym("eeschema")],
            [Sym("uuid"), ROOT_UUID], [Sym("paper"), "A4"],
            [Sym("title_block"), [Sym("title"), "AT070TN92 HDMI + USB-touch driver board"],
             [Sym("date"), "2026-10-02"], [Sym("rev"), "1.0"],
             [Sym("comment"), 1, "LT8619C HDMI->RGB888, TPS61040 bias, TPS61165 backlight, STM32F072 USB touch"]],
            [Sym("lib_symbols")]]
    uuids = {}
    for i, (name, title) in enumerate(SHEETS):
        su = "0a6b6d8e-3f1c-4c1d-9a7e-2b8f1c0001%02d" % (i + 1)
        uuids[name] = su
        x, y = 20 + (i % 2) * 130, 40 + (i // 2) * 45
        root.append([Sym("sheet"), [Sym("at"), x, y], [Sym("size"), 110, 30],
                     [Sym("fields_autoplaced")],
                     [Sym("stroke"), [Sym("width"), 0.1524], [Sym("type"), Sym("solid")]],
                     [Sym("fill"), [Sym("color"), 0, 0, 0, 0.0]], [Sym("uuid"), su],
                     [Sym("property"), "Sheetname", title, [Sym("at"), x, y - 0.7, 0], effects(justify="left bottom")],
                     [Sym("property"), "Sheetfile", sheet_file(name), [Sym("at"), x, y + 30.6, 0],
                      effects(justify="left top")],
                     [Sym("instances"), [Sym("project"), PROJECT, [Sym("path"), "/" + ROOT_UUID, [Sym("page"), str(i + 2)]]]]])
    for i, t in enumerate(NOTES):
        root.append([Sym("text"), t, [Sym("at"), 20, 145 + i * 6, 0], effects(justify="left")])
    root.append([Sym("sheet_instances"), [Sym("path"), "/", [Sym("page"), "1"]]])
    with open(os.path.join(HW, PROJECT + ".kicad_sch"), "w") as f:
        f.write(dump(root) + "\n")
    return uuids


if __name__ == "__main__":
    uuids = build_root()
    for i, (name, title) in enumerate(SHEETS):
        build_sheet(name, title, i + 2, uuids[name])
    print("schematic written")
