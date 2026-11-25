"""Convergence verifier: stability of a quantity under mesh refinement."""
import pytest

from verifiers.convergence import check_convergence

# Real C3D8 campaign: mid-span deflection (um) at nx = 10, 20, 40, 80, 160
CONVERGED = [8.84, 11.21, 12.00, 12.30, 12.39]
OSCILLATING = [10.0, 12.5, 11.0, 12.4]      # not stabilised yet


def test_converged_series_passes():
    ok, reason = check_convergence(CONVERGED, tol=0.02)
    assert ok, reason     # last gap 0.73% <= 2%


def test_oscillating_series_is_flagged():
    # The phase-0 C3D8R lesson: a moving series is not a result.
    ok, reason = check_convergence(OSCILLATING, tol=0.02)
    assert not ok        # last gap 11.3% > 2%


def test_inverted_series_is_flagged():
    # Densities passed in decreasing order: the gap betrays the wiring.
    ok, reason = check_convergence([12.39, 11.21, 8.84], tol=0.02)
    assert not ok        # last gap 26.8%: not a refinement, a regression


def test_tol_is_parametrable():
    ok_strict, _ = check_convergence(OSCILLATING, tol=0.02)
    ok_loose, _ = check_convergence(OSCILLATING, tol=0.15)
    assert not ok_strict
    assert ok_loose      # same series: policy decides


def test_too_short_series_raises():
    with pytest.raises(ValueError):
        check_convergence([12.39])


def test_invalid_tol_raises():
    with pytest.raises(ValueError):
        check_convergence(CONVERGED, tol=1.5)
