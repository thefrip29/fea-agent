#!/usr/bin/env python3
"""Generate a simply supported beam .inp for CalculiX (ccx).
Usage: python scripts/make_beam_inp.py [nx ny nz] [--reduced
Defaults: 20 8 8, fully integrated C3D8. With --reduced: C3D8R.
Units: SI (m, N, Pa). Bending plane is x-y, load acts along -y.
"""
import sys

args = [a for a in sys.argv[1:] if not a.startswith("-")]
ETYPE = "C3D8R" if "--reduced" in sys.argv else "C3D8"
try:
    NX, NY, NZ = (int(a) for a in args[:3])
except ValueError:
    NX, NY, NZ = 20, 8, 8

L, H, B = 1.0, 0.1, 0.1        # beam length, height, width (m)
E, NU = 2.1e11, 0.3            # steel
P = 1000.0                     # total applied load (N)
OUT = f"beam_{ETYPE.lower()}_{NX}_{NY}_{NZ}.inp"   # element type in name: no overwrites


def nid(i, j, k):
    """Node number for grid indices (i, j, k), 1-based and collision-free."""
    return 1 + i + j * (NX + 1) + k * (NX + 1) * (NY + 1)


nodes = [
    f"{nid(i,j,k)}, {L*i/NX:.6f}, {H*j/NY:.6f}, {B*k/NZ:.6f}"
    for k in range(NZ + 1) for j in range(NY + 1) for i in range(NX + 1)
]

elements = []
for k in range(NZ):
    for j in range(NY):
        for i in range(NX):
            n = [nid(i, j, k), nid(i, j, k + 1), nid(i + 1, j, k + 1), nid(i + 1, j, k),
                 nid(i, j + 1, k), nid(i, j + 1, k + 1),
                 nid(i + 1, j + 1, k + 1), nid(i + 1, j + 1, k)]
            elements.append(f"{len(elements)+1}, " + ", ".join(map(str, n)))

fmid = [nid(NX // 2, NY, k) for k in range(NZ + 1)]   # loaded nodes: top edge at x = L/2
supp0 = [nid(0, j, k) for k in range(NZ + 1) for j in range(NY + 1)]
supp1 = [nid(NX, j, k) for k in range(NZ + 1) for j in range(NY + 1)]
anchor = {1: nid(0, NY // 2, NZ // 2), 3: nid(0, 0, 0)}

p_node = -P / len(fmid)   # spread the load: no stress singularity at the point

lines = ["*HEADING", "Simply supported beam, mid-span load - fea-agent",
         "*NODE, NSET=NALL", *nodes,
         f"*ELEMENT, TYPE={ETYPE}, ELSET=EALL", *elements,
         "*NSET, NSET=FMID", *map(str, fmid),
         "*NSET, NSET=NSUPP0", *map(str, supp0),
         "*NSET, NSET=NSUPP1", *map(str, supp1)]
for dof, node in anchor.items():
    lines += [f"*NSET, NSET=NANCH{dof}", str(node)]
lines += ["*MATERIAL, NAME=STEEL", "*ELASTIC", f"{E:.1f}, {NU}",
          "*SOLID SECTION, ELSET=EALL, MATERIAL=STEEL",
          "*BOUNDARY",
          "NSUPP0, 2, 2, 0.0",
          "NSUPP1, 2, 2, 0.0",
          "NANCH1, 1, 1, 0.0", "NANCH3, 3, 3, 0.0",
          "*STEP", "*STATIC", "*CLOAD", f"FMID, 2, {p_node:.6f}",
          "*NODE PRINT, NSET=FMID", "U",
          "*NODE PRINT, NSET=NSUPP0, TOTALS=YES", "RF",
          "*NODE PRINT, NSET=NSUPP1, TOTALS=YES", "RF",
          "*END STEP"]

with open(OUT, "w") as f:
    f.write("\n".join(lines) + "\n")

I = B * H ** 3 / 12
print(f"{OUT}: {len(nodes)} nodes, {len(elements)} elements")
print(f"analytic: delta = {P*L**3/(48*E*I):.3e} m, "
      f"sigma = {(P*L/4)*(H/2)/I:.3e} Pa, reactions = {P/2:.0f} N each")
