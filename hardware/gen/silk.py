"""Place reference designators on the silkscreen so they sit next to (not on) their part,
never on a pad / solder-mask opening, a component body, a silkscreen outline or another
label.  Labels that cannot be placed close to their part are hidden (every reference is
still on the F.Fab assembly layer / docs/img/pcb_assembly.png).
"""
import pcbnew

TEXT_H, TEXT_W = 0.8, 0.15            # JLCPCB-legible minimum
PAD_CLEAR = 0.15                      # silk to pad / mask opening
BODY_CLEAR = 0.05                     # silk to component bodies
TEXT_GAP = 0.15                       # between labels
EDGE = 0.4                            # from board edge
PASSES = [(0.0, 0.3, 0.6, 1.0, 1.5, 2.1, 2.8), (3.4, 4.0)]   # distance steps per pass
SHIFTS = (0.0, -0.6, 0.6, -1.2, 1.2)
DIRS = ((0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (1, -1), (-1, 1), (1, 1))


def _box(bb, m=0.0):
    nm = 1e-6
    return (bb.GetLeft() * nm - m, bb.GetTop() * nm - m, bb.GetRight() * nm + m, bb.GetBottom() * nm + m)


def _hit(a, b, m=0.0):
    return a[0] < b[2] + m and b[0] - m < a[2] and a[1] < b[3] + m and b[1] - m < a[3]


def _body(fp):
    """Package outline: F.Fab graphics, else the courtyard shrunk by its 0.2 mm margin."""
    for layer, shrink in ((pcbnew.F_Fab, 0.0), (pcbnew.F_CrtYd, 0.2)):
        g = [x for x in fp.GraphicalItems() if x.GetLayer() == layer and "TEXT" not in x.GetClass()]
        if g:
            bs = [_box(x.GetBoundingBox()) for x in g]
            return (min(b[0] for b in bs) + shrink, min(b[1] for b in bs) + shrink,
                    max(b[2] for b in bs) - shrink, max(b[3] for b in bs) - shrink)
    return _box(fp.GetBoundingBox(False, False))


def place_labels(board, ox, oy, w, h):
    fps = list(board.GetFootprints())
    pads = [_box(p.GetBoundingBox(), PAD_CLEAR) for fp in fps for p in fp.Pads()]
    bodies = {fp.GetReference(): _body(fp) for fp in fps}
    silk = [_box(g.GetBoundingBox(), 0.1) for fp in fps for g in fp.GraphicalItems()
            if g.GetLayer() == pcbnew.F_SilkS]
    silk += [_box(d.GetBoundingBox(), 0.1) for d in board.GetDrawings() if d.GetLayer() == pcbnew.F_SilkS]
    placed = []

    def free(tb):
        if tb[0] < ox + EDGE or tb[1] < oy + EDGE or tb[2] > ox + w - EDGE or tb[3] > oy + h - EDGE:
            return False
        return not (any(_hit(tb, p) for p in pads) or
                    any(_hit(tb, b, BODY_CLEAR) for b in bodies.values()) or
                    any(_hit(tb, s) for s in silk) or
                    any(_hit(tb, q, TEXT_GAP) for q in placed))

    def try_place(fp, steps):
        t = fp.Reference()
        own = bodies[fp.GetReference()]
        cx, cy = (own[0] + own[2]) / 2, (own[1] + own[3]) / 2
        hw, hh = (own[2] - own[0]) / 2 + 0.2, (own[3] - own[1]) / 2 + 0.2
        for extra in steps:
            for sh in SHIFTS:
                for ang in (0, 90):
                    t.SetTextAngle(pcbnew.EDA_ANGLE(ang, pcbnew.DEGREES_T))
                    t.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(cx), pcbnew.FromMM(cy)))
                    b0 = _box(t.GetBoundingBox())
                    tw, th = (b0[2] - b0[0]) / 2, (b0[3] - b0[1]) / 2
                    for dx, dy in DIRS:
                        px = cx + dx * (hw + tw + extra) + (sh if dx == 0 else 0)
                        py = cy + dy * (hh + th + extra) + (sh if dy == 0 else 0)
                        t.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(px), pcbnew.FromMM(py)))
                        tb = _box(t.GetBoundingBox())
                        if free(tb):
                            placed.append(tb)
                            return True
        return False

    # small parts first: they live in the crowded areas, large parts have room around them
    todo = sorted((fp for fp in fps if fp.Reference().IsVisible()),
                  key=lambda f: bodies[f.GetReference()][2] - bodies[f.GetReference()][0])
    for fp in todo:
        t = fp.Reference()
        t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(TEXT_H), pcbnew.FromMM(TEXT_H)))
        t.SetTextThickness(pcbnew.FromMM(TEXT_W))
    for steps in PASSES:
        left = []
        for fp in todo:
            if not try_place(fp, steps):
                left.append(fp)
        todo = left
    for fp in todo:
        fp.Reference().SetVisible(False)
    hidden = sorted(fp.GetReference() for fp in todo)
    print("silkscreen labels: %d placed, %d hidden %s" % (len(placed), len(hidden), " ".join(hidden)))
    return hidden
