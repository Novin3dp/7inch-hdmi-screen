"""Compare the netlist exported from the generated schematic with design.py."""
import subprocess
import sys
from sexpr import parse, find, find1
from design import nets, PARTS

net_file = "/tmp/net.net"
subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr", "-o", net_file,
                "../lcd_f042.kicad_sch"], check=True, capture_output=True)
tree = parse(open(net_file).read())
sch = {}
for n in find(find1(tree, "nets"), "net"):
    name = find1(n, "name")[1].lstrip("/")
    nodes = {(find1(x, "ref")[1], find1(x, "pin")[1]) for x in find(n, "node")}
    if name.startswith("unconnected-") or name.startswith("Net-("):
        if len(nodes) > 1:
            print("UNNAMED NET WITH >1 NODE", name, nodes)
        continue
    sch[name] = nodes
des = {k: set(v) for k, v in nets().items()}
ok = True
for k in sorted(set(des) | set(sch)):
    if des.get(k) != sch.get(k):
        ok = False
        print("MISMATCH", k, "design-only:", des.get(k, set()) - sch.get(k, set()),
              "sch-only:", sch.get(k, set()) - des.get(k, set()))
comps = {find1(c, "ref")[1] for c in find(find1(tree, "components"), "comp")}
missing = {p.ref for p in PARTS} - comps
print("components in schematic:", len(comps), "missing:", missing)
print("NETLIST MATCH" if ok and not missing else "NETLIST DIFFERS")
sys.exit(0 if ok and not missing else 1)
