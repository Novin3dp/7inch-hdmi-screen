"""Build the DSI board PCB (placement, outline, pre-routed DSI pairs, zones) with the pcbnew API.

Run with the system python that has pcbnew:  python3.12 pcb.py
"""
import math
import os
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(__file__))
from design import PARTS, ICN, FPC  # noqa: E402

HW = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(HW, "lcd_dsi.kicad_pcb")
KFP = "/usr/share/kicad/footprints"

W, H = 68.0, 42.0          # board size (mm)
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
CX, CY = 33.0, 17.5        # ICN6211 centre (rotated 180: DSI pins face J1 at the top)
J1X, J1Y = 34.0, 7.3       # Pi DSI connector (180: FPC enters from the top edge)
J3X = 32.0                 # panel FPC (pin 1 on the right)
R4X = 27.2                 # PCLK series resistor
PL = {
    # --- DSI + ICN6211
    "J1": (J1X, J1Y, 180),
    "U1": (CX, CY, 180),
    "C5": (37.4, 13.4, 0),         # VDD1 (pin 12)
    "C6": (29.2, 14.2, 0),         # VDD2 (pin 24)
    "C7": (41.8, 21.6, 90),        # VDD3 (pin 3, via + B.Cu)
    "C8": (41.8, 18.8, 90),
    "C11": (31.2, 24.6, 270),      # VCORE (pin 40), fed by a pre-routed T
    "C9": (32.8, 24.6, 270),
    "R1": (40.2, 15.2, 0),         # DSI_EN pull-down
    "R2": (42.6, 11.8, 90),        # DSI I2C pull-ups
    "R3": (44.0, 11.8, 90),
    "R4": (27.2, 15.3, 180),       # PCLK series (pad 1 = PCLK on the right)
    # --- panel connector + configuration
    "J3": (J3X, H - 4.5, 0),
    "R15": (41.6, 29.8, 90),       # MODE
    "R16": (42.8, 29.8, 90),       # HS
    "R17": (44.0, 29.8, 90),       # VS
    "R18": (19.6, 31.6, 90),       # DITHB
    "R19": (25.2, 31.6, 90),       # LR
    "R20": (24.0, 31.6, 90),       # UD
    "R21": (21.6, 28.0, 90),       # DSI_EN -> LCD_RST
    "C13": (22.8, 31.6, 90),
    "C27": (45.2, 29.8, 90),
    "C28": (46.4, 29.8, 90),
    # --- bias supply (left)
    "R5": (6.8, 13.4, 0),          # DSI_EN -> BIAS_EN RC
    "C14": (3.6, 13.4, 90),
    "Q1": (3.6, 18.0, 0),
    "Q2": (3.6, 22.6, 0),
    "R22": (6.8, 16.2, 0),
    "R23": (6.8, 24.6, 0),
    "C29": (7.2, 20.3, 90),
    "U7": (10.6, 21.0, 0),
    "L1": (10.6, 26.4, 0),
    "D1": (15.4, 23.6, 90),
    "R24": (14.2, 18.0, 0),
    "R25": (14.2, 16.9, 0),
    "C30": (14.2, 19.1, 0),
    "C31": (18.0, 19.6, 90),
    "C32": (20.0, 19.6, 90),
    "C41": (21.6, 19.6, 90),
    "C33": (6.0, 30.2, 90),
    "D2": (8.4, 32.0, 90),
    "C34": (11.0, 32.8, 90),
    "R26": (13.0, 32.0, 90),
    "D3": (15.0, 32.6, 90),
    "C35": (17.4, 33.0, 90),
    "C36": (4.0, 30.2, 90),
    "D4": (4.2, 34.4, 0),
    "C37": (7.4, 36.0, 0),
    "R27": (10.6, 36.0, 0),
    "D5": (13.4, 37.8, 0),
    "C38": (13.4, 39.8, 0),
    "R28": (19.8, 24.4, 90),
    "RV1": (19.6, 28.0, 180),
    "R29": (23.6, 27.0, 90),
    "C39": (23.4, 23.4, 90),
    "U8": (24.4, 20.0, 0),
    "R30": (20.6, 34.4, 90),
    "C40": (22.0, 34.4, 90),
    # --- power (top-left: 3.3 V LDO; right: Pi header)
    "U2": (11.0, 5.4, 0),
    "C3": (16.6, 3.4, 90),
    "C4": (18.2, 3.4, 90),
    "D7": (16.6, 7.4, 0),
    "R34": (19.4, 7.4, 0),
    "J2": (W - 3.0, 3.5, 0),
    "F1": (59.6, 3.6, 90),
    "C1": (56.6, 3.6, 90),
    "C2": (54.8, 3.6, 90),
    # --- backlight (right)
    "U9": (56.0, 22.0, 0),
    "L2": (56.0, 27.4, 0),
    "D6": (51.4, 23.4, 90),
    "C42": (51.4, 28.4, 90),
    "C43": (59.6, 23.0, 90),
    "C44": (57.6, 18.8, 0),
    "R31": (48.6, 25.6, 90),
    "R32": (53.6, 18.8, 0),
    # --- touch
    "J4": (59.4, H - 4.5, 0),
    "R37": (58.0, 32.8, 0),
    "C52": (61.2, 32.8, 0),
    # --- test points
    "TP1": (52.0, 8.2, 0), "TP2": (21.4, 3.0, 0), "TP3": (2.2, 9.2, 0), "TP4": (19.2, 37.0, 0),
    "TP5": (2.2, 39.6, 0), "TP6": (23.6, 37.6, 0), "TP7": (49.0, 34.0, 0),
}


def preroute(board, net):
    """Hand-placed DSI pairs Pi connector -> ICN6211 (lane 1 crosses the clock: clock dips to B.Cu)."""
    jx = lambda p: J1X + p - 8                     # mirrored DSI footprint at 180 deg
    JP = J1Y + 1.8                                 # J1 pad centre y
    cx = lambda p: CX + 2.2 - (p - 13) * 0.4       # ICN6211 top-side pin x (pins 13..24)
    CP = CY - 2.95                                 # ICN6211 top-side pad centre y
    w = 0.2
    # lane 0: straight
    track(board, net("DSI_D0_N"), [(cx(15), CP), (cx(15), 12.0), (jx(8), 11.6), (jx(8), JP)], w=w)
    track(board, net("DSI_D0_P"), [(cx(14), CP), (cx(14), 11.8), (jx(9), 11.6), (jx(9), JP)], w=w)
    # lane 1: up, then left above the clock vias to the far-left connector pads
    track(board, net("DSI_D1_N"), [(cx(17), CP), (cx(17), 12.9), (jx(2) + 0.5, 12.9), (jx(2), 12.4),
                                   (jx(2), JP)], w=w)
    track(board, net("DSI_D1_P"), [(cx(16), CP), (cx(16), 12.4), (jx(3) + 0.5, 12.4), (jx(3), 11.9),
                                   (jx(3), JP)], w=w)
    # clock: short stubs to vias, bottom layer under lane 1, vias in front of the connector
    ya, yb = 13.45, 10.9
    for n, p, vx, jp in (("DSI_CK_N", 19, CX - 0.95, 5), ("DSI_CK_P", 18, CX - 0.1, 6)):
        track(board, net(n), [(cx(p), CP), (cx(p), CP - 0.45), (vx, ya)], w=0.15)
        via(board, net(n), vx, ya)
        track(board, net(n), [(vx, ya), (jx(jp), ya - (vx - jx(jp))), (jx(jp), yb)], layer=pcbnew.B_Cu, w=w)
        via(board, net(n), jx(jp), yb)
        track(board, net(n), [(jx(jp), yb), (jx(jp), JP)], w=w)
    # ICN6211 escape stubs for the remaining pins (I2C, EN, VDD1, VDD2); GND pins 8/13/35 tie into the EP.
    for p in (9, 10, 11, 12):
        y = CY + 2.2 - (p - 1) * 0.4
        track(board, net(ICN[p]), [(CX + 2.95, y), (CX + 4.1, y)], w=0.15)
    track(board, net("+3V3"), [(CX - 2.2, CP), (CX - 2.2, CP - 0.45)], w=0.2)                        # pin 24
    track(board, net("ICN_VCORE"), [(CX - 1.0, CY + 2.95), (CX - 1.0, CY + 5.5)], w=0.2)             # pin 40
    track(board, net("ICN_VCORE"), [(CX - 1.8, CY + 5.95), (CX - 1.8, CY + 5.5), (CX - 0.2, CY + 5.5),
                                     (CX - 0.2, CY + 5.95)], w=0.25)
    for x in (CX - 1.8, CX - 0.2):                     # VCORE caps: GND pad straight to a via
        track(board, net("GND"), [(x, CY + 7.875), (x, CY + 8.85)], w=0.3)
        via(board, net("GND"), x, CY + 8.85)
    # VDD3 (pin 3) sits between B3 and B4: stub + via between the B3 and B4 columns, decoupled on B.Cu
    y3 = CY + 2.2 - 2 * 0.4
    track(board, net("+3V3"), [(CX + 2.95, y3), (CX + 4.85, y3), (CX + 4.85, y3 + 0.8)], w=0.2)
    via(board, net("+3V3"), CX + 4.85, y3 + 0.8)
    track(board, net("GND"), [(CX + 2.95, CY + 2.2 - 7 * 0.4), (CX + 1.8, CY + 2.2 - 7 * 0.4)], w=0.15)   # pin 8
    track(board, net("GND"), [(CX - 2.95, CY - 2.2 + 10 * 0.4), (CX - 1.8, CY - 2.2 + 10 * 0.4)], w=0.15)  # pin 35
    track(board, net("GND"), [(CX + 2.2, CP), (CX + 2.2, CP + 0.9), (CX + 1.9, CP + 1.2)], w=0.15)      # pin 13
    rgb_bus(board, net)


def rgb_bus(board, net):
    """Hand-routed RGB bus ICN6211 -> J3: every line drops in its own column (0.35..0.4 mm pitch),
    then a 30 degree jog onto its FPC pad.  Lane order is planar except DE (pin 28 -> FPC 9), which
    takes the bottom layer under the whole bus."""
    tan30 = math.tan(math.radians(30))
    JP = H - 4.5 - 1.85                                  # J3 pad centre y
    jx3 = lambda pin: J3X + 12.25 - (pin - 1) * 0.5      # J3 pad x (pin 1 on the right)
    fpc = {n: int(k) for k, n in FPC.items() if isinstance(n, str) and n.startswith("LCD_") and k != "MP"}
    Y1 = 31.0                                            # where the columns start jogging onto the pads

    def drop(n, pts, col):
        tx = jx3(fpc[n])
        track(board, net(n), pts + [(col, Y1), (tx, Y1 + abs(tx - col) / tan30), (tx, JP)], w=0.15)

    # left side: R0..R5 (pins 29..34), R6 (pin 36) -> columns 26.8 .. 28.9
    for k, p in enumerate((29, 30, 31, 32, 33, 34, 36)):
        y = CY - 2.2 + (p - 25) * 0.4
        col = 26.8 + 0.35 * k
        drop(ICN[p], [(CX - 2.95, y), (col, y)], col)
    # bottom side: R7, G0, G1 jog left (30 deg) past the VCORE caps, G2..B1 jog right
    for p in (37, 38, 39):
        x = CX - 2.2 + (p - 37) * 0.4
        col = x - 1.25
        drop(ICN[p], [(x, CY + 2.95), (x, 21.0), (col, 21.0 + 1.25 / tan30)], col)
    for p in range(41, 49):
        x = CX - 2.2 + (p - 37) * 0.4
        col = x + 1.15
        drop(ICN[p], [(x, CY + 2.95), (x, 21.0), (col, 21.0 + 1.15 / tan30)], col)
    # right side: B2, B3 below the VDD3 via, B4..B7 around it
    for p, col in ((1, 36.75), (2, 37.15), (4, 38.55), (5, 38.95), (6, 39.35), (7, 39.75)):
        y = CY + 2.2 - (p - 1) * 0.4
        drop(ICN[p], [(CX + 2.95, y), (col, y)], col)
    # PCLK -> R4 (22R) -> DCLK in the leftmost column
    track(board, net("ICN_PCLK"), [(CX - 2.95, CY - 2.2), (R4X + 0.8, CY - 2.2)], w=0.15)
    tx = jx3(37)
    track(board, net("LCD_DCLK"), [(R4X - 0.8, CY - 2.2), (R4X - 0.8, Y1), (tx, Y1 + abs(tx - R4X + 0.8) / tan30),
                                   (tx, JP)], w=0.15)
    # DE: via next to the pin, bottom layer under the bus, up again beside FPC pin 9
    yd = CY - 2.2 + 3 * 0.4
    track(board, net("LCD_DE"), [(CX - 2.95, yd), (28.6, yd), (28.4, yd - 0.2)], w=0.15)
    via(board, net("LCD_DE"), 28.4, yd - 0.2)
    track(board, net("LCD_DE"), [(28.4, yd - 0.2), (28.4, 33.0), (jx3(9), 33.0)], layer=pcbnew.B_Cu, w=0.15)
    via(board, net("LCD_DE"), jx3(9), 33.0)
    track(board, net("LCD_DE"), [(jx3(9), 33.0), (jx3(9), JP)], w=0.15)


TXT_X = 52.0
FIXED = {"J1", "U1", "J2", "J3", "J4", "C11", "C9", "R4", "U7", "U9", "L1", "L2", "U2"}
# areas reserved for routing (no footprints): DSI field and the RGB bus field
NO_PLACE = [(25.5, 10.4, 36.0, 14.0), (25.9, 14.7, 29.1, 34.5), (29.1, 21.0, 40.6, 34.5), (36.3, 17.0, 40.6, 21.0)]


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
    path = os.path.join(HW, "lcd_dsi.pretty") if lib == "lcd_dsi" else os.path.join(KFP, lib + ".pretty")
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

    POWER_NETS = ["GND", "+5V", "+5V_IN", "+3V3", "BOOST_IN", "AVDD_SW", "AVDD", "BL_SW", "VLED_A", "VLED_K"]
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
        for txt, y, size in (("novin3dp.ir", 11.0, 1.3), ("DSI7", 13.2, 1.3)):
            t = pcbnew.PCB_TEXT(board)
            t.SetText(txt)
            t.SetLayer(pcbnew.F_SilkS)
            t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
            t.SetTextThickness(mm(0.2))
            t.SetPosition(pt(TXT_X, y))
            board.Add(t)
    if prep:
        # keep the bottom layer under the DSI pairs free of other signals
        keepout(board, pcbnew.B_Cu, [(26.5, 9.6), (36.0, 9.6), (36.0, 14.2), (26.5, 14.2)], tracks=True, vias=False)
        for t in board.GetTracks():
            t.SetLocked(True)
    return board


if __name__ == "__main__":
    board = make(prep=True)
    board.Save(OUT)
    print("saved", OUT)
