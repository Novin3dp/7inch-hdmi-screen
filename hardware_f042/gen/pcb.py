"""Build the PCB (placement, outline, pre-routed critical nets, zones) with the pcbnew API.

Run with the system python that has pcbnew:  python3.12 pcb.py
"""
import math
import os
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(__file__))
from design import PARTS  # noqa: E402

HW = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(HW, "lcd_f042.kicad_pcb")
KFP = "/usr/share/kicad/footprints"

W, H = 80.0, 50.0          # board size (mm)
OX, OY = 100.0, 80.0       # board origin on the KiCad page

# design rules (JLCPCB 2-layer standard capability with margin)
TRACK = 0.15
CLEAR = 0.15
VIA_D, VIA_DRILL = 0.6, 0.3


def mm(x):
    return pcbnew.FromMM(x)


def pt(x, y):
    return pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))


# ------------------------------------------------------------------ placement
# ref: (x, y, rotation_deg)   (x right, y down, board-local mm)
CX, CY = 27.0, 17.0        # LT8619C centre
J1Y = 14.75                # HDMI receptacle origin y (pin 12 = CK- at y 14.0)
PL = {
    # --- HDMI + LT8619C
    "J1": (3.5, J1Y, 270),
    "U1": (CX, CY, 0),
    "Y1": (29.6, 7.7, 0),
    "C9": (26.4, 8.55, 180),
    "C10": (32.8, 6.85, 0),
    "R10": (22.4, 23.975, 270),     # REXT (pin 16), escapes downwards
    "R12": (24.6, 27.4, 90),       # RESET_N pull-down
    "R13": (50.6, 12.4, 0),        # CSDA pull-up
    "R14": (50.6, 13.5, 0),        # CSCL pull-up
    "R11": (33.6, 13.8, 0),        # PCLK series (pin 56)
    "R3": (16.0, 8.0, 0),          # HPD series
    "R4": (12.6, 6.8, 0),
    "R5": (12.6, 5.7, 0),
    "R6": (12.6, 4.6, 0),
    # LT8619C decoupling (one per supply pin)
    "C11": (18.9, 12.4, 180),      # pin1  +1V8A
    "C15": (19.6, 22.4, 90),      # pin13 +1V8A
    "C12": (14.6, 14.7, 180),     # pin4  VTERM   (between TMDS pairs)
    "C13": (14.6, 16.9, 180),     # pin7  VCCA33
    "C14": (14.6, 19.1, 180),     # pin10 VTERM
    "C16": (23.4, 24.4, 270),      # pin20 +3V3
    "C17": (24.5, 24.4, 270),      # pin25 +1V8
    "C18": (33.0, 23.6, 0),      # pin36 +3V3 (TTL)
    "C19": (33.6, 12.6, 0),        # pin57 +3V3 (TTL)
    "C20": (33.9, 11.4, 0),       # pin58 +1V8   (pre-routed)
    "C21": (33.9, 9.9, 0),       # pin59 +1V8A  (pre-routed)
    "C22": (24.4, 10.1, 90),       # pin62 VCCA33_XTAL
    "C23": (25.9, 10.1, 90),       # pin64 +3V3
    "C24": (23.0, 10.6, 90),       # pin67 +1V8
    "C25": (35.0, 3.4, 90),
    "C26": (23.6, 26.6, 0),
    "FB1": (21.0, 27.0, 90),
    "C7": (19.8, 25.6, 90),
    "FB2": (16.0, 25.0, 90),
    "C8": (14.8, 24.6, 90),
    # --- power
    "U3": (40.5, 6.5, 0),          # 1V8
    "C5": (35.0, 6.5, 90),
    "U2": (53.5, 6.5, 0),          # 3V3
    "C3": (47.6, 4.2, 90),
    "C4": (47.6, 7.4, 90),
    "C6": (58.5, 4.8, 90),
    # --- USB-C + MCU
    "J2": (W - 3.65, 24.0, 90),
    "R1": (70.2, 19.4, 90),
    "R2": (70.2, 28.6, 90),
    "U4": (67.4, 24.0, 90),
    "F1": (73.6, 13.0, 90),
    "C1": (69.0, 9.0, 0),
    "C2": (66.0, 9.0, 90),
    "U10": (60.0, 22.0, 0),        # STM32F042F6P6 TSSOP-20 (USB pins 17/18 face the USB-C)
    "C45": (63.6, 19.4, 90),       # VDD  pin16
    "C46": (55.8, 23.6, 90),       # VDDA pin5
    "C47": (54.4, 23.6, 90),
    "C50": (59.4, 15.6, 0),
    "C51": (55.8, 19.6, 90),       # NRST
    "R33": (56.0, 16.6, 0),        # BOOT0
    "SW1": (62.4, 12.4, 0),
    "D7": (64.0, 31.2, 0),
    "R34": (61.0, 31.2, 0),
    "J5": (66.5, 2.2, 90),
    # --- touch
    "J4": (71.0, H - 4.5, 0),
    "R37": (65.6, 38.6, 90),
    "C52": (66.7, 38.6, 90),
    # --- panel connector + misc
    "J3": (39.0, H - 4.5, 0),
    "R15": (49.0, 40.0, 90),
    "R16": (47.9, 40.0, 90),
    "R17": (46.8, 40.0, 90),
    "R18": (27.0, 40.4, 90),
    "R19": (31.0, 40.4, 90),
    "R20": (29.9, 40.4, 90),
    "R21": (28.1, 40.4, 90),
    "C27": (51.0, 38.0, 0),
    "C28": (51.0, 36.8, 0),
    # --- bias supply (bottom-left)
    "Q1": (3.6, 30.0, 0),
    "Q2": (3.6, 34.6, 0),
    "R22": (6.8, 28.2, 0),
    "R23": (6.8, 36.6, 0),
    "C29": (7.2, 32.3, 90),
    "U7": (10.6, 33.0, 0),
    "L1": (10.6, 38.4, 0),
    "D1": (15.4, 35.6, 90),
    "R24": (14.2, 30.0, 0),
    "R25": (14.2, 28.9, 0),
    "C30": (14.2, 31.1, 0),
    "C31": (18.0, 31.6, 90),
    "C32": (20.0, 31.6, 90),
    "C41": (21.6, 31.6, 90),
    "C33": (6.0, 42.2, 90),
    "D2": (8.4, 44.0, 90),
    "C34": (11.0, 44.8, 90),
    "R26": (13.0, 44.0, 90),
    "D3": (15.0, 44.6, 90),
    "C35": (17.4, 44.6, 90),
    "C36": (4.0, 42.2, 90),
    "D4": (4.2, 46.2, 0),
    "C37": (7.4, 47.8, 0),
    "R27": (10.6, 47.8, 0),
    "D5": (13.6, 47.8, 0),
    "C38": (17.0, 47.8, 0),
    "R28": (19.8, 36.4, 90),
    "RV1": (20.0, 40.4, 180),
    "R29": (23.6, 42.6, 90),
    "C39": (23.4, 37.8, 90),
    "U8": (24.4, 34.2, 0),
    "R30": (20.8, 44.8, 90),
    "C40": (22.4, 46.0, 90),
    # --- backlight (bottom-right)
    "U9": (60.0, 41.2, 0),
    "L2": (60.0, 46.4, 0),
    "D6": (56.0, 42.4, 90),
    "C42": (56.0, 47.0, 90),
    "C43": (63.4, 42.0, 90),
    "C44": (61.6, 38.0, 0),
    "R31": (53.4, 39.0, 0),
    "R32": (57.8, 38.0, 0),
    # --- test points
    "TP1": (62.0, 2.2, 0), "TP2": (37.0, 11.0, 0), "TP3": (33.0, 2.0, 0), "TP4": (17.0, 28.8, 0),
    "TP5": (19.2, 48.0, 0), "TP6": (2.2, 48.0, 0), "TP7": (24.45, 41.44, 0), "TP8": (2.2, 39.6, 0),
}


def preroute(board, net):
    """Hand-placed critical routing: TMDS pairs HDMI->LT8619C, LT8619C analog supply pins."""
    tan30 = math.tan(math.radians(30))
    chip_y = lambda p: CY - 3.6 + (p - 1) * 0.4            # left-side pins 1..19
    hdmi_y = lambda n: J1Y + 4.75 - (n - 1) * 0.5          # HDMI pad n
    X_PAD = CX - 4.4          # chip left pad centre
    X0 = CX - 5.1             # end of horizontal escape from chip pads
    X_HD = 3.5 + 5.0          # HDMI pad centre
    X_HE = 10.0               # HDMI-side end of converge diagonals
    X_MID_R = 16.5            # middle region (fanned out) right end
    X_MID_L = 12.6            # middle region left end
    # (chip pin, hdmi pin, net, middle y)
    tm = [(2, 12, "TMDS_CK_N", 13.35), (3, 10, "TMDS_CK_P", 13.85),
          (5, 9, "TMDS_D0_N", 15.55), (6, 7, "TMDS_D0_P", 16.05),
          (8, 6, "TMDS_D1_N", 17.75), (9, 4, "TMDS_D1_P", 18.25),
          (11, 3, "TMDS_D2_N", 19.95), (12, 1, "TMDS_D2_P", 20.45)]
    for cp, hp, n, ym in tm:
        yc, yh = chip_y(cp), hdmi_y(hp)
        dx1 = abs(ym - yc) / tan30
        dx2 = abs(yh - ym) / tan30
        pts = [(X_PAD, yc), (X0, yc), (X0 - dx1, ym), (X_MID_L, ym)]
        if X_HE + dx2 < X_MID_L:
            pts[-1] = (X_HE + dx2, ym)
        pts += [(X_HE, yh), (X_HD, yh)]
        track(board, net(n), pts, w=0.18)
    # analog supply pins between the pairs: pin -> via -> decap -> GND via
    for cp, ym in [(4, 14.7), (7, 16.9), (10, 19.1)]:
        yc = chip_y(cp)
        dx1 = abs(ym - yc) / tan30
        track(board, net("+3V3A"), [(X_PAD, yc), (X0, yc), (X0 - dx1, ym), (16.0, ym), (15.375, ym)], w=0.18)
        via(board, net("+3V3A"), 16.0, ym)
        track(board, net("GND"), [(13.825, ym), (13.0, ym)], w=0.3)
        via(board, net("GND"), 13.0, ym)
    # +3V3A vias tied together on the bottom layer, down to FB2 (+3V3 -> +3V3A)
    track(board, net("+3V3A"), [(16.0, 14.7), (16.0, 23.5)], layer=pcbnew.B_Cu, w=0.3)
    via(board, net("+3V3A"), 16.0, 23.5)
    track(board, net("+3V3A"), [(16.0, 23.5), (16.0, 24.225)], w=0.3)
    # pin 1 (+1V8A): up to a via + decap above the TMDS group
    y1 = chip_y(1)
    track(board, net("+1V8A"), [(X_PAD, y1), (X0, y1), (X0 - 1.0 / tan30, y1 - 1.0), (19.675, y1 - 1.0)], w=0.18)
    via(board, net("+1V8A"), 20.0, y1 - 1.0)
    track(board, net("GND"), [(18.125, 12.4), (17.3, 12.4)], w=0.3)
    via(board, net("GND"), 17.3, 12.4)
    # pin 13 (+1V8A): short, steep escape below the D2+ line to a via
    y13 = chip_y(13)
    track(board, net("+1V8A"), [(X_PAD, y13), (X0, y13), (21.0, 19.0)], w=0.18)
    via(board, net("+1V8A"), 21.0, 19.0)
    # +1V8A bottom trunk: pin-1 via -> pin-13 via -> FB1 (+1V8 -> +1V8A)
    track(board, net("+1V8A"), [(20.0, 12.4), (21.0, 13.4), (21.0, 24.5)], layer=pcbnew.B_Cu, w=0.3)
    via(board, net("+1V8A"), 21.0, 24.5)
    track(board, net("+1V8A"), [(21.0, 24.5), (21.0, 26.225)], w=0.3)
    # USB-C: join the duplicated D+/D- contacts (both plug orientations)
    #   D+ (B6 y23.25, A6 y24.25): behind the pads on top;  D- (A7, B7): in front, via + bottom link
    jx, jy = W - 3.65, 24.0
    xr, xf = jx - 4.045 - 0.725, jx - 4.045 + 0.725         # rear / front pad ends
    track(board, net("USB_DP"), [(xr, jy - 0.75), (xr - 0.55, jy - 0.75), (xr - 0.55, jy + 0.25), (xr, jy + 0.25)])
    for dy in (-0.25, 0.75):
        track(board, net("USB_DM"), [(xf, jy + dy), (xf + 0.55, jy + dy)])
        via(board, net("USB_DM"), xf + 0.55, jy + dy)
    track(board, net("USB_DM"), [(xf + 0.55, jy - 0.25), (xf + 0.55, jy + 0.75)], layer=pcbnew.B_Cu)
    #   VBUS (A4/B9 y26.45, A9/B4 y21.55): vias behind the pads, joined on the bottom layer
    for dy in (-2.45, 2.45):
        track(board, net("VBUS"), [(xr, jy + dy), (xr - 0.7, jy + dy)], w=0.4)
        via(board, net("VBUS"), xr - 0.7, jy + dy)
    track(board, net("VBUS"), [(xr - 0.7, jy - 2.45), (xr - 0.7, jy + 2.45)], layer=pcbnew.B_Cu, w=0.4)
    # pins 58 (VDD18) / 59 (PVCC18, PLL): nested escapes to their decaps on the right
    track(board, net("+1V8"), [(CX + 3.6, CY - 4.4), (CX + 3.6, 11.4), (33.125, 11.4)], w=0.2)
    track(board, net("+1V8A"), [(CX + 3.2, CY - 4.4), (CX + 3.2, 9.9), (33.125, 9.9)], w=0.2)
    for y in (11.4, 9.9):
        track(board, net("GND"), [(34.675, y), (35.4, y)], w=0.3)
        via(board, net("GND"), 35.4, y)
    # pins 65 (CSDA), 66 (CSCL), 67 (VDD18): staggered escapes so both I2C lines get a via
    if PREP:   # only reserves the escape during autorouting; Freerouting feeds pin 67 from below
        track(board, net("+1V8"), [(CX, CY - 4.4), (CX, 12.05), (CX - 0.17, 11.88), (CX - 1.4, 11.88)], w=0.25)
    track(board, net("I2C_SCL"), [(CX + 0.4, CY - 4.4), (CX + 0.4, 11.7), (CX + 0.1, 11.4), (CX + 0.1, 10.9)])
    via(board, net("I2C_SCL"), CX + 0.1, 10.9)
    track(board, net("I2C_SDA"), [(CX + 0.8, CY - 4.4), (CX + 0.8, 10.35)])
    via(board, net("I2C_SDA"), CX + 0.75, 10.35)
    # VCOM: buffer side (TP7) to panel pin 46 on the bottom layer, before the RGB bus is routed
    p46x = 39.0 + 12.25 - 45 * 0.5
    track(board, net("VCOM"), [(p46x, H - 6.35), (p46x, 42.3)], w=0.25)
    via(board, net("VCOM"), p46x, 42.3)
    track(board, net("VCOM"), [(p46x, 42.3), (24.45, 42.3)], layer=pcbnew.B_Cu, w=0.25)
    via(board, net("VCOM"), 24.45, 42.3)
    track(board, net("VCOM"), [(24.45, 42.3), (24.45, 41.44)], w=0.25)
    # REXT: straight down from pin 16, clear of the unused pins 17..19
    y16 = chip_y(16)
    track(board, net("LT_REXT"), [(X_PAD, y16), (21.8, y16), (21.8, 22.4), (22.4, 23.0), (22.4, 23.15)], w=0.2)
    # HDMI GND pins: via in front of each pad (under the receptacle body)
    for hp in (2, 5, 8, 11, 17):
        y = hdmi_y(hp)
        track(board, net("GND"), [(X_HD, y), (6.9, y)], w=0.25)
        via(board, net("GND"), 6.9, y)


FIXED = {"C22", "C23", "TP7", "C20", "C21", "J1", "U1", "J2", "J3", "J4", "U10", "U2", "U3", "Y1", "C11", "C12", "C13", "C14",
         "R10", "FB1", "FB2", "J5", "U7", "U9", "L1", "L2"}
# areas reserved for routing (no footprints): TMDS corridor and RGB bus field
NO_PLACE = [(8.0, 11.6, 22.3, 22.0), (25.0, 26.0, 52.0, 36.0), (25.6, 21.6, 32.0, 26.0)]


def fp_box(fp, margin=0.0):
    xs, ys = [], []
    for g in fp.GraphicalItems():
        if g.GetLayer() == pcbnew.F_CrtYd:
            bb = g.GetBoundingBox()
            xs += [bb.GetLeft(), bb.GetRight()]
            ys += [bb.GetTop(), bb.GetBottom()]
    if not xs:
        for p in fp.Pads():
            bb = p.GetBoundingBox()
            xs += [bb.GetLeft(), bb.GetRight()]
            ys += [bb.GetTop(), bb.GetBottom()]
        margin += 0.25
    f = lambda v: pcbnew.ToMM(v)
    return (f(min(xs)) - OX - margin, f(min(ys)) - OY - margin, f(max(xs)) - OX + margin, f(max(ys)) - OY + margin)


def overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def legalize(board):
    """Move non-fixed footprints to the nearest spot where their courtyard is free."""
    m = 0.2
    placed = [(a - m, b - m, c + m, d + m) for a, b, c, d in PRE]
    fps = list(board.GetFootprints())
    order = [f for f in fps if f.GetReference() in FIXED] + [f for f in fps if f.GetReference() not in FIXED]
    for fp in order:
        ref = fp.GetReference()
        if ref in FIXED:
            placed.append(fp_box(fp))
            continue
        x0, y0 = [pcbnew.ToMM(v) for v in (fp.GetPosition().x, fp.GetPosition().y)]
        best = None
        for r in [i * 0.2 for i in range(0, 60)]:
            n = max(1, int(2 * math.pi * r / 0.2))
            for k in range(n):
                a = 2 * math.pi * k / n
                dx, dy = r * math.cos(a), r * math.sin(a)
                fp.SetPosition(pcbnew.VECTOR2I(mm(x0 + dx), mm(y0 + dy)))
                bx = fp_box(fp)
                if bx[0] < 0.3 or bx[1] < 0.3 or bx[2] > W - 0.3 or bx[3] > H - 0.3:
                    continue
                if any(overlap(bx, p) for p in placed) or any(overlap(bx, z) for z in NO_PLACE):
                    continue
                best = (dx, dy)
                break
            if best:
                break
        if best is None:
            print("legalize: no place for", ref)
            best = (0, 0)
        elif best != (0, 0):
            print("legalize: %s moved %.1f,%.1f" % (ref, best[0], best[1]))
        fp.SetPosition(pcbnew.VECTOR2I(mm(x0 + best[0]), mm(y0 + best[1])))
        placed.append(fp_box(fp))


def load_fp(fpid):
    lib, name = fpid.split(":")
    path = os.path.join(HW, "lcd_f042.pretty") if lib == "lcd_f042" else os.path.join(KFP, lib + ".pretty")
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        raise RuntimeError("footprint not found: " + fpid)
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


def add_line(board, x1, y1, x2, y2, layer, w=0.1):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(pt(x1, y1))
    s.SetEnd(pt(x2, y2))
    s.SetLayer(layer)
    s.SetWidth(mm(w))
    board.Add(s)


def add_arc(board, cx, cy, sx, sy, ang, layer, w=0.1):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_ARC)
    s.SetCenter(pt(cx, cy))
    s.SetStart(pt(sx, sy))
    s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(ang, pcbnew.DEGREES_T))
    s.SetLayer(layer)
    s.SetWidth(mm(w))
    board.Add(s)


def outline(board, r=2.0):
    L = pcbnew.Edge_Cuts
    add_line(board, r, 0, W - r, 0, L)
    add_line(board, W, r, W, H - r, L)
    add_line(board, W - r, H, r, H, L)
    add_line(board, 0, H - r, 0, r, L)
    add_arc(board, r, r, 0, r, 90, L)
    add_arc(board, W - r, r, W - r, 0, 90, L)
    add_arc(board, W - r, H - r, W, H - r, 90, L)
    add_arc(board, r, H - r, r, H, 90, L)


PREP = True   # building the board for Freerouting (vs. the final board)
DRAW = True   # False: only record pre-route geometry (final build takes the copper from the .ses)
PRE = []      # recorded pre-route boxes (x1, y1, x2, y2) incl. half width


def track(board, net, pts, layer=pcbnew.F_Cu, w=TRACK):
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        PRE.append((min(x1, x2) - w / 2, min(y1, y2) - w / 2, max(x1, x2) + w / 2, max(y1, y2) + w / 2))
        if not DRAW:
            continue
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pt(x1, y1))
        t.SetEnd(pt(x2, y2))
        t.SetWidth(mm(w))
        t.SetLayer(layer)
        t.SetNet(net)
        board.Add(t)


def via(board, net, x, y):
    PRE.append((x - VIA_D / 2, y - VIA_D / 2, x + VIA_D / 2, y + VIA_D / 2))
    if not DRAW:
        return
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pt(x, y))
    v.SetWidth(mm(VIA_D))
    v.SetDrill(mm(VIA_DRILL))
    v.SetNet(net)
    board.Add(v)


def zone(board, netinfo, layer, poly, prio=0, clearance=0.25, min_w=0.2, name=None):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(netinfo)
    z.SetAssignedPriority(prio)
    z.SetLocalClearance(mm(clearance))
    z.SetMinThickness(mm(min_w))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    z.SetThermalReliefGap(mm(0.25))
    z.SetThermalReliefSpokeWidth(mm(0.3))
    polyset(z, poly)
    if name:
        z.SetZoneName(name)
    board.Add(z)
    return z


def keepout(board, layer, poly, tracks=True, vias=True, pour=False):
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetLayer(layer)
    z.SetDoNotAllowTracks(tracks)
    z.SetDoNotAllowVias(vias)
    z.SetDoNotAllowCopperPour(pour)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    polyset(z, poly)
    board.Add(z)


def polyset(z, poly):
    ol = z.Outline()
    ol.NewOutline()
    for x, y in poly:
        ol.Append(mm(OX + x), mm(OY + y))


def pad_xy(board, ref, num):
    fp = board.FindFootprintByReference(ref)
    for p in fp.Pads():
        if p.GetNumber() == str(num):
            pos = p.GetPosition()
            return pcbnew.ToMM(pos.x) - OX, pcbnew.ToMM(pos.y) - OY
    raise KeyError((ref, num))


def build():
    board = pcbnew.BOARD()
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(2)
    ds.m_TrackMinWidth = mm(0.127)
    ds.m_MinClearance = mm(0.127)
    ds.m_ViasMinSize = mm(0.5)
    ds.m_MinThroughDrill = mm(0.3)
    ds.m_HoleClearance = mm(0.2)
    ds.m_CopperEdgeClearance = mm(0.3)
    ds.m_SolderMaskMinWidth = mm(0)
    nc = ds.m_NetSettings.m_DefaultNetClass
    nc.SetClearance(mm(CLEAR - 0.01))   # DRC margin for Freerouting rounding (JLC min is 0.127)
    nc.SetTrackWidth(mm(TRACK))
    nc.SetViaDiameter(mm(VIA_D))
    nc.SetViaDrill(mm(VIA_DRILL))
    pwr = pcbnew.NETCLASS("Power")
    pwr.SetClearance(mm(0.2))
    pwr.SetTrackWidth(mm(0.4))
    pwr.SetViaDiameter(mm(0.8))
    pwr.SetViaDrill(mm(0.4))
    ds.m_NetSettings.m_NetClasses["Power"] = pwr

    nets = {}

    def net(name):
        if name not in nets:
            ni = pcbnew.NETINFO_ITEM(board, name)
            board.Add(ni)
            nets[name] = ni
        return nets[name]

    POWER_NETS = ["GND", "+5V", "VBUS", "+3V3", "+1V8", "+1V8A", "+3V3A", "BOOST_IN", "AVDD_SW",
                  "AVDD", "BL_SW", "VLED_A", "VLED_K"]
    for n in POWER_NETS:
        net(n)
    for p in PARTS:
        fp = load_fp(p.fp)
        fp.SetReference(p.ref)
        fp.SetValue(p.value)
        x, y, rot = PL.get(p.ref, (W + 10, 0, 0))
        if p.ref not in PL:
            print("WARNING: unplaced", p.ref)
        fp.SetPosition(pt(x, y))
        fp.SetOrientationDegrees(rot)
        board.Add(fp)
        for pad in fp.Pads():
            n = p.pins.get(pad.GetNumber(), "__missing__")
            if n == "__missing__":
                if pad.GetNumber() not in ("",):
                    print("WARNING: pad without pin mapping", p.ref, pad.GetNumber())
                continue
            if n is not None:
                pad.SetNet(net(n))
        # small, readable silkscreen
        fp.Reference().SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8)))
        fp.Reference().SetTextThickness(mm(0.15))
    outline(board)
    for n in POWER_NETS:
        nets[n].SetNetClass(pwr)
    return board, net


def make(prep):
    """prep=True: board for Freerouting (pre-routes locked, temp keepout).  prep=False: final."""
    global DRAW, PREP
    DRAW = True
    PREP = prep
    PRE.clear()
    board, net = build()
    preroute(board, net)
    legalize(board)
    gnd = net("GND")
    full = [(0, 0), (W, 0), (W, H), (0, H)]
    if not prep:
        # pours only in the final board: GND is routed as a normal net, the pours just add copper
        zone(board, gnd, pcbnew.F_Cu, full, name="GND_TOP")
        zone(board, gnd, pcbnew.B_Cu, full, name="GND_BOT")
    if not prep:
        for txt, y, size in (("novin3dp.ir", 17.2, 1.3), ("HDMI7-F042", 19.4, 1.3)):
            t = pcbnew.PCB_TEXT(board)
            t.SetText(txt)
            t.SetLayer(pcbnew.F_SilkS)
            t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
            t.SetTextThickness(mm(0.2))
            t.SetPosition(pt(44.8, y))
            board.Add(t)
    if prep:
        # keep the bottom layer under the TMDS lines free of other signals
        keepout(board, pcbnew.B_Cu, [(6.0, 11.8), (22.4, 11.8), (22.4, 22.2), (6.0, 22.2)], tracks=True, vias=False)
        for t in board.GetTracks():
            t.SetLocked(True)
    return board


if __name__ == "__main__":
    board = make(prep=True)
    board.Save(OUT)
    print("saved", OUT)
