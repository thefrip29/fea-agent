"""Command-line entry: judge a whole run directory with the college of verifiers."""
import argparse

from pathlib import Path

from verifiers.bounds import check_deflection_bounds
from verifiers.ccx_io import read_dat, read_frd
from verifiers.equilibrium import check_equilibrium
from verifiers.stress import check_stress_bounds

# The phase-0 textbook beam (SI), used as default judgment context.
BEAM = {"P": 1000.0, "L": 1.0, "E": 2.1e11, "b": 0.1, "h": 0.1}
REACTION_SETS = ("NSUPP0", "NSUPP1")   # supports: fy of their total_force
DEFLECTION_SET = "FMID"                # mid-span section: max |vy| = deflection


def run_checks(run_dir, beam=BEAM, factor=1.15, eq_tol=1e-6):
    """Judge one run directory. Returns (all_ok, [(name, ok, reason), ...]).

    One run = one sealed box: exactly one .dat and one .frd expected,
    anything else is a wiring error and we raise rather than guess.
    """
    dats = sorted(Path(run_dir).glob("*.dat"))
    frds = sorted(Path(run_dir).glob("*.frd"))
    if len(dats) != 1 or len(frds) != 1:
        raise ValueError(f"expected exactly one .dat and one .frd in {run_dir}, "
                         f"found {len(dats)} .dat and {len(frds)} .frd")
    d = read_dat(dats[0])
    frd = read_frd(frds[0])

    # Fact 1: support reactions vs applied load.
    reactions = [d["sets"][s]["total_force"][1] for s in REACTION_SETS]
    eq = check_equilibrium({"reactions": reactions, "applied_load": beam["P"]},
                           tol=eq_tol)

    # Fact 2: mid-span deflection vs the Euler-Bernoulli answer key.
    u = d["sets"][DEFLECTION_SET]["displacements"]
    fem_delta = max(abs(v[1]) for v in u.values())
    bd = check_deflection_bounds(fem_delta, **beam, factor=factor)

    # Fact 3: tension fiber stress vs the closed-form sigma_max.
    st = check_stress_bounds(frd, P=beam["P"], L=beam["L"], b=beam["b"], h=beam["h"], factor=factor)

    verdicts = [("equilibrium", *eq), ("bounds", *bd), ("stress", *st)]
    return all(ok for _, ok, _ in verdicts), verdicts


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Judge a CalculiX run directory: prints PASS/FAIL with reasons, "
                    "exit code 0 (PASS) or 1 (FAIL).")
    parser.add_argument("run_dir",
                        help="directory containing exactly one .dat and one .frd")
    parser.add_argument("--factor", type=float, default=1.15,
                        help="bounds tolerance policy (default 1.15)")
    args = parser.parse_args(argv)

    all_ok, verdicts = run_checks(args.run_dir, factor=args.factor)
    for name, ok, reason in verdicts:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {reason}")
    print("PASS" if all_ok else "FAIL")
    return 0 if all_ok else 1
