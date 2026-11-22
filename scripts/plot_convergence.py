"""Plot C3D8 vs C3D8R mesh convergence along the beam length."""
import glob
import re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

P, L, H, B, E, NU = 1000.0, 1.0, 0.1, 0.1, 2.1e11, 0.3
KAPPA = 5 / 6
I, A = B * H ** 3 / 12, B * H
DELTA_EB = P * L**3 / (48 * E * I)
DELTA_3D = DELTA_EB + P * L / (4 * KAPPA * E / (2 * (1 + NU)) * A)


def midspan_deflection(path):
    """Min uy over the FMID displacement block of a .dat file."""
    dy, in_block = [], False
    for line in open(path):
        if "displacements" in line and "FMID" in line:
            in_block = True
            continue
        if in_block:
            s = line.strip()
            if not s:                     # blank line: skip, block not over
                continue
            if not s[0].isdigit():        # next block header: stop
                break
            dy.append(float(line.split()[2]))
    if not dy:
        raise ValueError(f"no FMID displacement data found in {path}")
    return abs(min(dy))


def runs(etype, ny=16):
    found = []
    for f in glob.glob(f"Output/beam_{etype}_*_{ny}_8.dat"):
        m = re.search(rf"Output/beam_{etype}_(\d+)_{ny}_8\.dat$", f)
        if m:
            found.append((int(m.group(1)), f))
    return sorted(found)


print(f"references: EB = {1e6*DELTA_EB:.3f} um,  3D target = {1e6*DELTA_3D:.3f} um\n")
print(f"{'element':8} {'nx':>4} {'defl (um)':>10} {'vs EB':>7} {'vs 3D':>7}")
for etype, color, marker in [("c3d8", "tab:blue", "o"), ("c3d8r", "green", "s")]:
    xs, ys = [], []
    for nx, f in runs(etype):
        d = 1e6 * midspan_deflection(f)
        xs.append(nx)
        ys.append(d)
        print(f"{etype.upper():8} {nx:>4} {d:>10.3f} {100*(d-1e6*DELTA_EB)/(1e6*DELTA_EB):>6.1f}%"
              f" {100*(d-1e6*DELTA_3D)/(1e6*DELTA_3D):>6.1f}%")
    plt.plot(xs, ys, marker + "-", color=color, label=etype.upper())

plt.axhline(DELTA_EB * 1e6, color="red", ls="--", label="Euler-Bernoulli (no shear)")
plt.axhline(DELTA_3D * 1e6, color="gray", ls=":", label="3D target (EB + shear)")
plt.xscale("log")
plt.xlabel("elements along the length (nx)")
plt.ylabel("mid-span deflection (um)")
plt.legend()
plt.savefig("docs/convergence.png", dpi=150, bbox_inches="tight")
print("\nsaved docs/convergence.png")
