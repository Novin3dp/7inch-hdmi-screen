"""Generate the project-specific footprint and symbol libraries (lcd_dsi.*)."""
import _shared  # noqa: F401  (sexpr/symlib from hardware/gen)
import os
import uuid
from sexpr import parse, dump, Sym, find

HW = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
FPDIR = os.path.join(HW, "lcd_dsi.pretty")
SYMFILE = os.path.join(HW, "lcd_dsi.kicad_sym")
KFP = "/usr/share/kicad/footprints"


def u():
    return str(uuid.uuid4())


def fp_text(kind, text, x, y, layer, size=1.0):
    return [Sym("fp_text"), Sym(kind), text, [Sym("at"), x, y], [Sym("layer"), layer],
            [Sym("effects"), [Sym("font"), [Sym("size"), size, size], [Sym("thickness"), 0.15 * size]]]]


def fp_line(x1, y1, x2, y2, layer, w):
    return [Sym("fp_line"), [Sym("start"), x1, y1], [Sym("end"), x2, y2],
            [Sym("stroke"), [Sym("width"), w], [Sym("type"), Sym("solid")]], [Sym("layer"), layer]]


def smd(num, x, y, w, h, layers=("F.Cu", "F.Paste", "F.Mask"), shape="roundrect", extra=None):
    p = [Sym("pad"), num, Sym("smd"), Sym(shape), [Sym("at"), x, y], [Sym("size"), w, h],
         [Sym("layers")] + list(layers)]
    if shape == "roundrect":
        p.append([Sym("roundrect_rratio"), 0.25])
    if extra:
        p += extra
    return p


def fpc50():
    """FH12(A)-50S-0.5SH land pattern with pads renumbered so that pad n == AT070TN92 FPC pin n.

    Orientation (footprint at 0 deg): FPC enters from +Y (board edge), solder tails at -Y.
    Seen from the top with the FPC entering from below, panel pin 1 is on the RIGHT.
    This matches the panel FPC folded behind the module into a TOP-contact connector
    (FH12A, recommended by the Innolux spec), and equally the unfolded case.
    """
    src = parse(open(os.path.join(KFP, "Connector_FFC-FPC.pretty",
                                  "Hirose_FH12-50S-0.5SH_1x50-1MP_P0.50mm_Horizontal.kicad_mod")).read())
    name = "FPC_50P_P0.5_TopContact_AT070TN92"
    src[1] = name
    out = []
    for e in src:
        if isinstance(e, list) and e and e[0] == "pad" and e[1] not in ("MP", ""):
            e[1] = str(51 - int(e[1]))
        if isinstance(e, list) and e and e[0] == "descr":
            e[1] = ("50-pin 0.5mm FPC, Hirose FH12A-50S-0.5SH land pattern, pads numbered as AT070TN92 "
                    "FPC pins (pin 1 at +X). Use a TOP-contact connector.")
        if isinstance(e, list) and e and e[0] == "fp_line":
            # move pin-1 marker (fab chevron at -12.25) to the +X side
            st, en = e[1], e[2]
            sx, ex = float(st[1]), float(en[1])
            if abs(sx + 12.75) < 0.01 and abs(ex + 12.25) < 0.01:
                st[1], en[1] = -sx, -ex
            if sx == -12.66 and ex == -12.66:
                st[1], en[1] = 12.66, 12.66
        out.append(e)
    out.append(fp_text("user", "FPC IN (contacts up)", 0, 3.0, "F.Fab", 0.6))
    return name, out


def fpc15_dsi():
    """1.0 mm 15-pin FPC (TE 1-84953-5 land pattern) with pads numbered as Raspberry Pi DSI pins,
    mirrored (pad n sits where the TE pad 16-n is).  With the footprint at 180 deg (FPC entering
    from the top edge) this puts lane 0, clock and lane 1 left-to-right in the order that lets the
    pairs reach the ICN6211 with a single crossing.  Use a DUAL-contact connector: flipping the
    cable over at this end mirrors the mapping (see README)."""
    src = parse(open(os.path.join(KFP, "Connector_FFC-FPC.pretty",
                                  "TE_1-84953-5_1x15-1MP_P1.0mm_Horizontal.kicad_mod")).read())
    name = "FPC_15P_P1.0_PiDSI"
    src[1] = name
    out = []
    for e in src:
        if isinstance(e, list) and e and e[0] == "pad" and e[1] not in ("MP", ""):
            e[1] = str(16 - int(e[1]))
        if isinstance(e, list) and e and e[0] == "descr":
            e[1] = ("Raspberry Pi DSI 15-pin 1.0mm FPC, TE 1-84953-5 land pattern, pads numbered as Pi DSI "
                    "pins, mirrored. Use a dual-contact connector.")
        out.append(e)
    out.append(fp_text("user", "Pi DSI (pin 1 = GND)", 0, 4.0, "F.Fab", 0.6))
    return name, out


def qfn48_icn():
    """KiCad QFN-48 6x6 P0.4 EP4.2 (ICN6211 V0.5 package: EP 4.2 x 4.2 mm) with 4x4 thermal vias
    enlarged to 0.3 mm drill / 0.6 mm pad (JLCPCB standard via)."""
    src = parse(open(os.path.join(KFP, "Package_DFN_QFN.pretty",
                                  "QFN-48-1EP_6x6mm_P0.4mm_EP4.2x4.2mm_ThermalVias.kicad_mod")).read())
    name = "QFN-48-1EP_6x6mm_P0.4mm_EP4.2x4.2mm_Vias0.3"
    src[1] = name
    for e in src:
        if isinstance(e, list) and e and e[0] == "pad" and len(e) > 2 and str(e[2]) == "thru_hole":
            for k in e:
                if isinstance(k, list) and k and k[0] == "size":
                    k[1], k[2] = 0.6, 0.6
                if isinstance(k, list) and k and k[0] == "drill":
                    k[1] = 0.3
    return name, src


def write_footprints():
    os.makedirs(FPDIR, exist_ok=True)
    for name, fp in (fpc50(), fpc15_dsi(), qfn48_icn()):
        with open(os.path.join(FPDIR, name + ".kicad_mod"), "w") as f:
            f.write(dump(fp) + "\n")


# ------------------------------------------------------------------ symbols
def pin(num, name, typ, x, y, rot, length=2.54):
    return [Sym("pin"), Sym(typ), Sym("line"), [Sym("at"), x, y, rot], [Sym("length"), length],
            [Sym("name"), name, [Sym("effects"), [Sym("font"), [Sym("size"), 1.27, 1.27]]]],
            [Sym("number"), str(num), [Sym("effects"), [Sym("font"), [Sym("size"), 1.27, 1.27]]]]]


def icn6211_symbol():
    names = {1: "DATA18", 2: "DATA19", 3: "VDD3", 4: "DATA20", 5: "DATA21", 6: "DATA22", 7: "DATA23",
             8: "TEST", 9: "SCL", 10: "SDA", 11: "EN", 12: "VDD1", 13: "REF_CLK", 14: "DA0P", 15: "DA0N",
             16: "DA1P", 17: "DA1N", 18: "DACP", 19: "DACN", 20: "DA2P", 21: "DA2N", 22: "DA3P", 23: "DA3N",
             24: "VDD2", 25: "PCLK", 26: "HSYNC", 27: "VSYNC", 28: "DATA_EN", 29: "DATA0", 30: "DATA1",
             31: "DATA2", 32: "DATA3", 33: "DATA4", 34: "DATA5", 35: "GND", 36: "DATA6", 37: "DATA7",
             38: "DATA8", 39: "DATA9", 40: "VCORE", 41: "DATA10", 42: "DATA11", 43: "DATA12", 44: "DATA13",
             45: "DATA14", 46: "DATA15", 47: "DATA16", 48: "DATA17", 49: "EP(GND)"}
    types = {}
    for p, n in names.items():
        if n.startswith("VDD") or n in ("GND", "EP(GND)"):
            types[p] = "power_in"
        elif n == "VCORE":
            types[p] = "power_out"
        elif n.startswith(("DATA", "PCLK", "HSYNC", "VSYNC")):
            types[p] = "output"
        elif n == "SDA":
            types[p] = "bidirectional"
        else:
            types[p] = "input"
    data = {d: p for p, n in names.items() if n.startswith("DATA") and n != "DATA_EN" for d in [int(n[4:])]}
    left = [12, 24, 3, 40, None, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, None, 9, 10, 11, 13, 8,
            None, 35, 49]
    right = [data[d] for d in range(8)] + [None] + [data[d] for d in range(8, 16)] + [None] + \
        [data[d] for d in range(16, 24)] + [None, 28, 25, 26, 27]
    assert sorted(p for p in left + right if p) == list(range(1, 50)), "pin list"
    h = max(len(left), len(right))
    top = round(((h - 1) * 2.54 / 2) / 2.54) * 2.54
    W = 20.32
    body = [Sym("symbol"), "ICN6211_0_1",
            [Sym("rectangle"), [Sym("start"), -W / 2, top + 2.54], [Sym("end"), W / 2, top - h * 2.54],
             [Sym("stroke"), [Sym("width"), 0.254], [Sym("type"), Sym("default")]],
             [Sym("fill"), [Sym("type"), Sym("background")]]]]
    pins = [Sym("symbol"), "ICN6211_1_1"]
    for i, p in enumerate(left):
        if p:
            pins.append(pin(p, names[p], types[p], -W / 2 - 5.08, round(top - i * 2.54, 2), 0, 5.08))
    for i, p in enumerate(right):
        if p:
            pins.append(pin(p, names[p], types[p], W / 2 + 5.08, round(top - i * 2.54, 2), 180, 5.08))

    def prop(k, v, y, hide=False):
        e = [Sym("effects"), [Sym("font"), [Sym("size"), 1.27, 1.27]]]
        if hide:
            e.append(Sym("hide"))
        return [Sym("property"), k, v, [Sym("at"), 0, y, 0], e]
    return [Sym("symbol"), "ICN6211", [Sym("in_bom"), Sym("yes")], [Sym("on_board"), Sym("yes")],
            prop("Reference", "U", top + 5.08), prop("Value", "ICN6211", top + 3.81),
            prop("Footprint", "lcd_dsi:QFN-48-1EP_6x6mm_P0.4mm_EP4.2x4.2mm_Vias0.3", 0, True),
            prop("Datasheet", "ICN6211 Specification V0.5 (Chipone)", 0, True),
            prop("ki_description", "Chipone MIPI DSI to RGB888 bridge, QFN-48 6x6 mm", 0, True),
            body, pins]


def write_symbols():
    lib = [Sym("kicad_symbol_lib"), [Sym("version"), 20220914], [Sym("generator"), Sym("kicad_symbol_editor")],
           icn6211_symbol()]
    with open(SYMFILE, "w") as f:
        f.write(dump(lib) + "\n")


if __name__ == "__main__":
    write_footprints()
    write_symbols()
    print("libs written to", HW)
