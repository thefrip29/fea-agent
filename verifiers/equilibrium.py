"""Equilibrium verifier: support reactions must balance the applied load."""


def check_equilibrium(result, tol=1e-6):
    """Check that the sum of support reactions balances the applied load.

    result: {"reactions": [r1, r2, ...], "applied_load": P}
    tol: relative tolerance on |sum(reactions) - load| / |load|.

    Returns (ok, reason): a boolean and a human-readable explanation,
    designed so that the caller (CLI, agent) can log the verdict as is.
    """
    reactions = result["reactions"]
    applied = abs(result["applied_load"])

    if applied == 0:
        # Nothing to balance: refuse rather than divide by zero further down.
        return False, "applied load is zero: nothing to balance"

    total = sum(abs(r) for r in reactions)
    error = abs(total - applied) / applied
    reason = (f"reactions sum {total:.6g} vs applied load {applied:.6g}"
              f" (relative gap {error:.2e}, tol {tol:.0e})")
    return error <= tol, reason

