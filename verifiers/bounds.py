"""Bounds verifier: a FEM answer must live within a multiplicative band of the analytic reference."""
from solutions.closed_form import delta_midspan_3pb


def check_bounds(value, reference, factor=1.15):
    """Check that value lies within [reference/factor, reference*factor].

    Returns (ok, reason). The band is multiplicative: it stays meaningful
    whatever the magnitude of the quantity (um deflection or MPa stress).
    BOTH sides alert: too small = model too stiff (locking, coarse mesh),
    too large = load/properties/units nonsense.
    """
    if factor <= 1:
        raise ValueError(f"factor must be > 1, got {factor}")
    if value <= 0 or reference <= 0:
        raise ValueError(f"value and reference must be positive, got {value}, {reference}")

    ratio = value / reference
    band = f"[{1/factor:.2f}, {factor:.2f}]"
    if ratio < 1 / factor:
        return False, (f"ratio {ratio:.3f} below the {band} band: "
                       "too small, model too stiff (locking? coarse mesh?) or wrong units")
    if ratio > factor:
        return False, (f"ratio {ratio:.3f} above the {band} band: "
                       "too large, load or properties wrong? wrong units?")
    return True, f"ratio {ratio:.3f} within the {band} band"


def check_deflection_bounds(fem_delta, P, L, E, b, h, factor=1.15):
    """Judge a FEM mid-span deflection against the Euler-Bernoulli reference.

    Phase 0 taught us the reference is a LOWER BOUND of the 3D solution
    (~+4.5% at L/h = 10) but a converged run stays within a few percent.
    A deflection far BELOW the analytic value is the signature of a locked,
    under-resolved mesh: same alarm value as far above.
    """
    ref = delta_midspan_3pb(P, L, E, b, h)
    ok, detail = check_bounds(fem_delta, ref, factor)
    return ok, f"deflection {fem_delta:.4g} m vs analytic {ref:.4g} m: {detail}"
