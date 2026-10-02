"""Generate the project-specific footprint and symbol libraries (lcd_board.*)."""
import os
import uuid
from sexpr import parse, dump, Sym, find
from design import LT

HW = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
FPDIR = os.path.join(HW, "lcd_board.pretty")
SYMFILE = os.path.join(HW, "lcd_board.kicad_sym")
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


def qfn76():
    """Lontium LT8619C QFN-76 9x9 mm, 0.4 mm pitch, EP 5.81 x 6.31 mm (datasheet R1.4, fig 9.1)."""
    name = "Lontium_QFN-76_9x9mm_P0.4mm_EP5.81x6.31mm"
    fp = [Sym("footprint"), name, [Sym("version"), 20221018], [Sym("generator"), Sym("pcbnew")],
          [Sym("layer"), "F.Cu"],
          [Sym("descr"), "Lontium LT8619C QFN-76 9x9mm P0.4mm, EP 5.81x6.31mm (D2 x E2 nominal)"],
          [Sym("attr"), Sym("smd")],
          fp_text("reference", "REF**", 0, -6.0, "F.SilkS"),
          fp_text("value", name, 0, 6.0, "F.Fab", 0.6)]
    pitch, n = 0.4, 19
    padc, padl, padw = 4.4, 0.85, 0.22   # pad centre radius, length, width
    num = 1
    for side in range(4):
        for i in range(n):
            off = (i - (n - 1) / 2) * pitch
            if side == 0:      # left, top -> bottom
                x, y, w, h = -padc, off, padl, padw
            elif side == 1:    # bottom, left -> right
                x, y, w, h = off, padc, padw, padl
            elif side == 2:    # right, bottom -> top
                x, y, w, h = padc, -off, padl, padw
            else:              # top, right -> left
                x, y, w, h = -off, -padc, padw, padl
            fp.append(smd(str(num), round(x, 3), round(y, 3), w, h))
            num += 1
    # exposed pad (copper slightly smaller than package pad) + paste windows (~55%)
    epw, eph = 5.6, 6.1
    fp.append(smd("77", 0, 0, epw, eph, layers=("F.Cu", "F.Mask"), shape="rect"))
    for ix in (-1.4, 0, 1.4):
        for iy in (-1.95, -0.65, 0.65, 1.95):
            fp.append(smd("77", ix, iy, 1.0, 1.0, layers=("F.Paste",), shape="rect"))
    # thermal vias inside EP
    for ix in (-2.1, -0.7, 0.7, 2.1):
        for iy in (-2.6, -1.3, 0, 1.3, 2.6):
            fp.append([Sym("pad"), "77", Sym("thru_hole"), Sym("circle"), [Sym("at"), ix, iy],
                       [Sym("size"), 0.6, 0.6], [Sym("drill"), 0.3], [Sym("layers"), "*.Cu"],
                       [Sym("zone_connect"), 2]])
    b = 4.5
    for (x1, y1, x2, y2) in [(-b, -b, b, -b), (b, -b, b, b), (b, b, -b, b), (-b, b, -b, -b)]:
        fp.append(fp_line(x1, y1, x2, y2, "F.Fab", 0.1))
    s = 4.6
    for (x1, y1, x2, y2) in [(-s, -s, -3.9, -s), (s, -s, 3.9, -s), (s, -s, s, -3.9), (s, s, 3.9, s),
                             (s, s, s, 3.9), (-s, s, -3.9, s), (-s, s, -s, 3.9)]:
        fp.append(fp_line(x1, y1, x2, y2, "F.SilkS", 0.12))
    fp.append([Sym("fp_circle"), [Sym("center"), -5.0, -4.6], [Sym("end"), -4.85, -4.6],
               [Sym("stroke"), [Sym("width"), 0.3], [Sym("type"), Sym("solid")]],
               [Sym("fill"), Sym("solid")], [Sym("layer"), "F.SilkS"]])
    c = 5.35
    for (x1, y1, x2, y2) in [(-c, -c, c, -c), (c, -c, c, c), (c, c, -c, c), (-c, c, -c, -c)]:
        fp.append(fp_line(x1, y1, x2, y2, "F.CrtYd", 0.05))
    return name, fp


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


def write_footprints():
    os.makedirs(FPDIR, exist_ok=True)
    for name, fp in (qfn76(), fpc50()):
        with open(os.path.join(FPDIR, name + ".kicad_mod"), "w") as f:
            f.write(dump(fp) + "\n")


# ------------------------------------------------------------------ symbols
def pin(num, name, typ, x, y, rot, length=2.54):
    return [Sym("pin"), Sym(typ), Sym("line"), [Sym("at"), x, y, rot], [Sym("length"), length],
            [Sym("name"), name, [Sym("effects"), [Sym("font"), [Sym("size"), 1.27, 1.27]]]],
            [Sym("number"), str(num), [Sym("effects"), [Sym("font"), [Sym("size"), 1.27, 1.27]]]]]


def lt8619c_symbol():
    names = {1: "VCCA18", 2: "RXC-", 3: "RXC+", 4: "VTERM", 5: "RX0-", 6: "RX0+", 7: "VCCA33",
             8: "RX1-", 9: "RX1+", 10: "VTERM", 11: "RX2-", 12: "RX2+", 13: "VCCA18", 14: "NC",
             15: "CEC", 16: "REXT", 17: "ESDA", 18: "ESCL", 19: "IIS_SD0/SPDIF", 20: "VCC33",
             21: "IIS_WS", 22: "IIS_SCLK", 23: "IIS_MCLK", 24: "RESET_N", 25: "VDD18", 26: "TD3+",
             27: "TD3-", 36: "VCC33_TTL", 53: "DE", 54: "HS", 55: "VS", 56: "PCLK", 57: "VCC33_TTL",
             58: "VDD18", 59: "PVCC18", 60: "XTAL_O", 61: "XTAL_I", 62: "VCCA33_XTAL", 63: "GPIO15",
             64: "VCC33", 65: "CSDA", 66: "CSCL", 67: "VDD18", 68: "IIS_SD3", 69: "IIS_SD2",
             70: "IIS_SD1", 71: "SPDIF", 72: "NC", 73: "GPIO13", 74: "RX_HPD", 75: "DSDA_RX",
             76: "DSCL_RX", 77: "EP(GND)"}
    lvds = {28: "TDC+", 29: "TDC-", 30: "TD2+", 31: "TD2-", 32: "TD1+", 33: "TD1-", 34: "TD0+",
            35: "TD0-", 37: "TC3+", 38: "TC3-", 39: "TCC+", 40: "TCC-", 41: "TC2+", 42: "TC2-",
            43: "TC1+", 44: "TC1-", 45: "TC0+", 46: "TC0-"}
    for d in range(24):
        p = {23: 28, 22: 29, 21: 30, 20: 31, 19: 32, 18: 33, 17: 34, 16: 35, 15: 37, 14: 38, 13: 39,
             12: 40, 11: 41, 10: 42, 9: 43, 8: 44, 7: 45, 6: 46, 5: 47, 4: 48, 3: 49, 2: 50, 1: 51, 0: 52}[d]
        names[p] = "D%d" % d + ("_" + lvds[p] if p in lvds else "")
    types = {}
    for p, n in names.items():
        if n.startswith(("VCC", "VDD", "PVCC", "VTERM")) or n == "EP(GND)":
            types[p] = "power_in"
        elif n == "NC":
            types[p] = "no_connect"
        elif n.startswith(("D", "TD", "IIS", "SPDIF", "PCLK", "XTAL_O", "RX_HPD", "HS", "VS")) and not n.startswith("DS"):
            types[p] = "output"
        elif n.startswith(("RX", "REXT", "RESET", "XTAL_I", "CSCL", "DSCL")):
            types[p] = "input"
        else:
            types[p] = "bidirectional"
    types[53] = "output"
    left = [1, 13, 59, 25, 58, 67, None, 4, 10, 7, 62, 20, 64, 36, 57, None,
            3, 2, 6, 5, 9, 8, 12, 11, None, 76, 75, 74, 15, None, 61, 60, 16, None, 66, 65, 24,
            None, 17, 18, 63, 73, None, 14, 72, None, 77]
    right = [52, 51, 50, 49, 48, 47, 46, 45, None, 44, 43, 42, 41, 40, 39, 38, 37, None,
             35, 34, 33, 32, 31, 30, 29, 28, None, 53, 54, 55, 56, None, 26, 27, None,
             19, 21, 22, 23, 68, 69, 70, 71]
    assert sorted(p for p in left + right if p) == list(range(1, 78)), "pin list"
    h = max(len(left), len(right))
    top = (h - 1) * 2.54 / 2
    top = round(top / 2.54) * 2.54
    W = 22.86
    body = [Sym("symbol"), "LT8619C_0_1",
            [Sym("rectangle"), [Sym("start"), -W / 2, top + 2.54], [Sym("end"), W / 2, top - h * 2.54],
             [Sym("stroke"), [Sym("width"), 0.254], [Sym("type"), Sym("default")]],
             [Sym("fill"), [Sym("type"), Sym("background")]]]]
    pins = [Sym("symbol"), "LT8619C_1_1"]
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
    sym = [Sym("symbol"), "LT8619C", [Sym("in_bom"), Sym("yes")], [Sym("on_board"), Sym("yes")],
           prop("Reference", "U", top + 5.08), prop("Value", "LT8619C", top + 3.81),
           prop("Footprint", "lcd_board:Lontium_QFN-76_9x9mm_P0.4mm_EP5.81x6.31mm", 0, True),
           prop("Datasheet", "LT8619C_Datasheet_R1.4", 0, True),
           prop("ki_description", "Lontium HDMI 1.4 receiver to TTL RGB / LVDS, QFN-76", 0, True),
           body, pins]
    return sym


def write_symbols():
    lib = [Sym("kicad_symbol_lib"), [Sym("version"), 20220914], [Sym("generator"), Sym("kicad_symbol_editor")],
           lt8619c_symbol()]
    with open(SYMFILE, "w") as f:
        f.write(dump(lib) + "\n")


if __name__ == "__main__":
    write_footprints()
    write_symbols()
    print("libs written to", HW)
