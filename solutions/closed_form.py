"""Closed-form solutions: the analytic answers the verifiers compare against.

Pure functions, SI units everywhere, no solver involved. The oracles in
tests are values computed BY HAND: this library is what gets tested.
"""


def i_rect(b, h):
    """Second moment of area of a rectangular section, bending about the h axis."""
    if b <= 0 or h <= 0:
        raise ValueError(f"section dimensions must be positive, got b={b}, h={h}")
    return b * h ** 3 / 12


def delta_midspan_3pb(P, L, E, b, h):
    """Mid-span deflection, simply supported beam, point load at mid-span.

    Euler-Bernoulli (no shear): a LOWER BOUND of the 3D solution.
    Phase 0 measured the 3D answer ~4.5% above this at L/h = 10:
    bounds verifiers must account for that margin.
    """
    return P * L ** 3 / (48 * E * i_rect(b, h))


def sigma_max_3pb(P, L, b, h):
    """Max bending stress at mid-span: sigma = M*c/I with M = P*L/4."""
    M = P * L / 4
    return M * (h / 2) / i_rect(b, h)


def delta_tension(F, L, A, E):
    """Elongation of a bar under axial tension: delta = F*L/(A*E)."""
    return F * L / (A * E)


def sigma_tension(F, A):
    """Normal stress in a bar under axial load: sigma = F/A."""
    return F / A
