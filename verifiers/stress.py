"""Stress verifier: judge the physics, not the load zone (Saint-Venant)."""
import math

from solutions.closed_form import sigma_max_3pb

from verifiers.bounds import check_bounds


def von_mises(sxx, syy, szz, sxy, syz, szx):
    """Equivalent stress from the 6 components, frd order."""
    return math.sqrt(sxx * sxx + syy * syy + szz * szz
                     - sxx * syy - syy * szz - szz * sxx
                     + 3.0 * (sxy * sxy + syz * syz + szx * szx))


def check_stress_bounds(frd, P, L, b, h, factor=1.15, fiber_tol=1e-6):
    """Judge the bending stress on the tension fiber (bottom face, y = 0).

    Lesson from the real files: the whole-beam max von Mises lives in the
    load application zone and GROWS with mesh refinement (nx=160 reached
    2.8 MPa vs 1.5 analytic - Saint-Venant). The physics to judge is the
    mid-span bending fiber, one beam height away from the load: sigma_xx
    there converges to the closed-form sigma_max. The whole-beam max stays
    in the reason, as info only.

    frd: the dict returned by parse_frd. A run without STRESS block or
    without coords is a verdict, not a crash.
    """
    stress = frd.get("results", {}).get("STRESS")
    nodes = frd.get("nodes", {})
    if not stress:
        return False, "no STRESS block in the frd: the deck never requested S fields"
    fiber = {n: vals for n, vals in stress.items()
             if n in nodes and abs(nodes[n][1]) <= fiber_tol}
    if not fiber:
        return False, "no node found on the y=0 face: coords missing or unexpected mesh"

    sigma = max(abs(vals[0]) for vals in fiber.values())        # sigma_xx on the fiber
    vm_all = max(von_mises(*vals) for vals in stress.values())  # info only, load zone
    ref = sigma_max_3pb(P, L, b, h)
    ok, detail = check_bounds(sigma, ref, factor)
    return ok, (f"tension fiber sigma_xx {sigma:.4g} Pa vs analytic {ref:.4g} Pa: "
                f"{detail} (whole-beam max von Mises {vm_all:.4g} Pa, load zone, info)")
