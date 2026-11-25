"""Convergence verifier: a physical quantity must stabilise as the mesh is refined."""


def check_convergence(series, tol=0.02):
    """Check that the last refinement changed the quantity by less than tol.

    series: values of the quantity at increasing mesh densities, in order.
    Returns (ok, reason): the reason carries the last gap AND the whole
    series, so a caller (CLI, agent) can read where the run stands.
    """
    if len(series) < 2:
        raise ValueError(f"need at least 2 values, got {len(series)}")
    if not (0 < tol < 1):
        raise ValueError(f"tol must be in (0, 1), got {tol}")
    if any(v <= 0 for v in series):
        raise ValueError("series values must be positive")

    last, prev = series[-1], series[-2]
    gap = abs(last - prev) / last
    reason = (f"last refinement gap {gap:.2%} ({prev:.4g} -> {last:.4g}), "
              f"tol {tol:.0%}; series: {', '.join(f'{v:.4g}' for v in series)}")
    return gap <= tol, reason
