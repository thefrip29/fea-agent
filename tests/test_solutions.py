"""Closed-form solutions tested against hand-computed oracles (phase-0 values)."""
import pytest

from solutions.closed_form import (
    i_rect, delta_midspan_3pb, sigma_max_3pb, delta_tension, sigma_tension,
)


def test_i_rect_matches_hand_computation():
    # b = h = 0.1 m -> I = 0.1 * 0.1**3 / 12 = 8.3333e-6 m^4, computed by hand
    assert i_rect(0.1, 0.1) == pytest.approx(8.3333e-6, rel=1e-4)


def test_delta_3pb_matches_the_phase0_reference():
    # delta = PL^3/(48EI) = 1000 / (48 * 2.1e11 * 8.3333e-6) = 1.19048e-5 m
    d = delta_midspan_3pb(P=1000, L=1.0, E=2.1e11, b=0.1, h=0.1)
    assert d == pytest.approx(1.19048e-5, rel=1e-4)


def test_sigma_3pb_matches_the_phase0_reference():
    # M = PL/4 = 250 N.m; sigma = M*(h/2)/I = 250 * 0.05 / 8.3333e-6 = 1.5 MPa
    assert sigma_max_3pb(P=1000, L=1.0, b=0.1, h=0.1) == pytest.approx(1.5e6, rel=1e-4)


def test_tension_hand_case():
    # F = 1e3 N, A = 1e-4 m^2, L = 0.5 m: delta = FL/(AE) = 500 / 2.1e7 = 2.381e-5 m
    assert delta_tension(F=1e3, A=1e-4, L=0.5, E=2.1e11) == pytest.approx(2.38095e-5, rel=1e-4)
    # sigma = F/A = 1e3 / 1e-4 = 1e7 Pa = 10 MPa
    assert sigma_tension(F=1e3, A=1e-4) == pytest.approx(1e7)


def test_invalid_section_raises():
    # A negative section is a modeling error: DETECT, never compute nonsense.
    with pytest.raises(ValueError):
        i_rect(-1.0, 0.5)
