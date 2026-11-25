"""Bounds verifier: tested against the REAL numbers of the phase-0 campaign."""
import pytest

from solutions.closed_form import delta_midspan_3pb
from verifiers.bounds import check_bounds, check_deflection_bounds

# Phase-0 references: analytic vs converged vs locked.
REF = delta_midspan_3pb(P=1000, L=1.0, E=2.1e11, b=0.1, h=0.1)   # 1.19048e-5 m
CONVERGED = 12.389e-6       # C3D8, nx=160
LOCKED = 8.84e-6            # C3D8, nx=10 (shear locking, -26%)
UNITS_MM_AS_M = 12.389e-3   # deflection in mm read as meters


def test_converged_run_passes():
    ok, reason = check_bounds(CONVERGED, REF, factor=1.15)
    assert ok, reason


def test_locked_coarse_mesh_is_flagged():
    ok, reason = check_bounds(LOCKED, REF, factor=1.15)
    assert not ok
    assert "below" in reason       # under the lower bound: too stiff


def test_units_error_is_flagged():
    ok, reason = check_bounds(UNITS_MM_AS_M, REF, factor=1.15)
    assert not ok
    assert "above" in reason        # way over the band: nonsense detected


def test_factor_is_parametrable():
    # The verdict flips with the policy, not with the physics.
    ok_strict, _ = check_bounds(LOCKED, REF, factor=1.15)
    ok_loose, _ = check_bounds(LOCKED, REF, factor=1.5)
    assert not ok_strict
    assert ok_loose


def test_invalid_factor_raises():
    with pytest.raises(ValueError):
        check_bounds(CONVERGED, REF, factor=0.9)


def test_deflection_wiring_passes_on_converged_data():
    ok, reason = check_deflection_bounds(CONVERGED, 1000, 1.0, 2.1e11, 0.1, 0.1)
    assert ok, reason


def test_deflection_wiring_flags_units_error():
    ok, reason = check_deflection_bounds(UNITS_MM_AS_M, 1000, 1.0, 2.1e11, 0.1, 0.1)
    assert not ok
    assert "above" in reason
