"""Tests for the .frd parser and the stress verifier (Saint-Venant edition)."""
import math

import pytest

from verifiers.ccx_io import parse_frd
from verifiers.stress import check_stress_bounds, von_mises

# Lines copied from the real regenerated phase-0 .frd (fixed width, no separators)
FRD = """ -1         1 0.00000E+00 0.00000E+00 0.00000E+00
 -1         2 5.00000E-02 0.00000E+00 0.00000E+00
 -1      9999    1    2    3    4    5    6    7    8
 -3
 -4  DISP        4    1
 -5  D1          1    2    1    0
 -5  D2          1    2    2    0
 -5  D3          1    2    3    0
 -5  ALL         1    2    0    0    1ALL
 -1         1-1.57576E-06 0.00000E+00 0.00000E+00
 -1         2-1.55824E-06-1.65053E-06 5.76291E-08
 -3
 -4  STRESS      6    1
 -5  SXX         1    4    1    1
 -5  SYY         1    4    2    2
 -5  SZZ         1    4    3    3
 -5  SXY         1    4    1    2
 -5  SYZ         1    4    2    3
 -5  SZX         1    4    3    1
 -1         1 1.45000E+06 0.00000E+00 0.00000E+00 0.00000E+00 0.00000E+00 0.00000E+00
 -1         2-1.45000E+06 0.00000E+00 0.00000E+00 0.00000E+00 0.00000E+00 0.00000E+00
 -3
"""


def test_node_coords_are_parsed():
    nodes = parse_frd(FRD)["nodes"]
    assert nodes[2] == pytest.approx([5.0e-02, 0.0, 0.0])


def test_disp_block_is_parsed_fixed_width():
    r = parse_frd(FRD)["results"]["DISP"]
    assert r[1] == pytest.approx([-1.57576e-06, 0.0, 0.0])
    assert r[2][0] == pytest.approx(-1.55824e-06)   # value glued to the node id


def test_stress_block_has_six_components():
    r = parse_frd(FRD)["results"]["STRESS"]
    assert len(r[1]) == 6
    assert r[2][0] == pytest.approx(-1.45e6)


def test_blocks_stay_separate():
    assert set(parse_frd(FRD)["results"]) == {"DISP", "STRESS"}


def test_von_mises_uniaxial_and_pure_shear():
    assert von_mises(1.5e6, 0, 0, 0, 0, 0) == pytest.approx(1.5e6)
    assert von_mises(0, 0, 0, 1e6, 0, 0) == pytest.approx(math.sqrt(3) * 1e6)


def _frd(sxx, hot=0.0):
    """Node 1 on the bottom fiber carries sxx; node 3 (top face) may be a hot load zone."""
    return {
        "nodes": {1: [0.5, 0.0, 0.05], 2: [0.25, 0.05, 0.05], 3: [0.5, 0.1, 0.05]},
        "results": {"STRESS": {1: [sxx, 0, 0, 0, 0, 0],
                               2: [0.0] * 6,
                               3: [hot, 0, 0, 0, 0, 0]}},
    }


def test_converged_stresses_pass():
    ok, reason = check_stress_bounds(_frd(1.45e6), P=1000, L=1, b=0.1, h=0.1)
    assert ok, reason          # fiber sigma 1.45 MPa vs 1.5 MPa: ratio 0.967


def test_units_error_is_flagged():
    ok, reason = check_stress_bounds(_frd(1.45e12), P=1000, L=1, b=0.1, h=0.1)
    assert not ok and "above" in reason


def test_flat_stresses_are_flagged():
    ok, reason = check_stress_bounds(_frd(1.45e3), P=1000, L=1, b=0.1, h=0.1)
    assert not ok and "below" in reason


def test_hot_load_zone_is_ignored_saint_venant():
    # The whole-beam max lives in the load zone and grows with refinement:
    # it must NOT drive the verdict, but stays visible in the reason.
    ok, reason = check_stress_bounds(_frd(1.45e6, hot=5.0e6), P=1000, L=1, b=0.1, h=0.1)
    assert ok, reason
    assert "5" in reason


def test_missing_stress_block_is_a_verdict_not_a_crash():
    ok, reason = check_stress_bounds({"nodes": {}, "results": {}},
                                     P=1000, L=1, b=0.1, h=0.1)
    assert not ok and "STRESS" in reason
def test_element_records_are_skipped():
    # Elements reuse the '-1' prefix with narrow integer fields: the crash
    # of 27/11 taught us - skipped in the mesh, garbage inside result blocks.
    nodes = parse_frd(FRD)["nodes"]
    assert 9999 not in nodes
    assert set(nodes) == {1, 2}
