"""Load symbols from KiCad .kicad_sym libraries and list their pins."""
import os
from sexpr import parse, find, find1

SYMDIR = "/usr/share/kicad/symbols"
_cache = {}


def load_lib(lib):
    if lib not in _cache:
        path = lib if lib.endswith(".kicad_sym") else os.path.join(SYMDIR, lib + ".kicad_sym")
        _cache[lib] = parse(open(path).read())
    return _cache[lib]


def get_symbol(lib, name):
    """Return the symbol s-expr, resolving 'extends'."""
    tree = load_lib(lib)
    for s in find(tree, "symbol"):
        if s[1] == name:
            ext = find1(s, "extends")
            if ext:
                base = get_symbol(lib, ext[1])[0]
                return s, base
            return s, None
    raise KeyError(name)


def pins(lib, name):
    s, base = get_symbol(lib, name)
    src = base if base is not None else s
    out = []

    def walk(e, unit):
        for x in e:
            if isinstance(x, list) and x and x[0] == "symbol":
                parts = x[1].rsplit("_", 2)
                if len(parts) == 3 and not parts[-2].isdigit(): parts = [x[1]]
                walk(x, int(parts[-2]) if len(parts) == 3 else unit)
            elif isinstance(x, list) and x and x[0] == "pin":
                at = find1(x, "at")
                nm = find1(x, "name")[1]
                num = find1(x, "number")[1]
                ln = find1(x, "length")
                out.append(dict(num=num, name=nm, type=str(x[1]), x=float(at[1]), y=float(at[2]),
                                rot=float(at[3]) if len(at) > 3 else 0.0,
                                length=float(ln[1]) if ln else 2.54, unit=unit,
                                hidden=any(a == "hide" for a in x)))
    walk(src, 0)
    return out


if __name__ == "__main__":
    import sys
    for p in sorted(pins(sys.argv[1], sys.argv[2]), key=lambda p: (len(p["num"]), p["num"])):
        print(p["num"], p["name"], p["type"], "unit", p["unit"], "hidden" if p["hidden"] else "")
