"""Tests for the CalculiX .dat parser (phase-0 traps encoded as regression tests)."""
import pytest

from verifiers.ccx_io import parse_dat

DAT_SAMPLE = """
 displacements (vx,vy,vz) for set FMID and time  0.1000000E+01

         179  3.264921E-08 -1.119008E-05  1.589387E-07
         180  1.563774E-15 -1.271248E-05  4.647312E-22

 forces (fx,fy,fz) for set NSUPP0 and time  0.1000000E+01

         501  0.000000E+00  5.000000E+02  0.000000E+00

 total force (fx,fy,fz) for set NSUPP0 and time  0.1000000E+01

  0.000000E+00  5.000000E+02  0.000000E+00
"""


def test_displacements_block_is_parsed():
    d = parse_dat(DAT_SAMPLE)
    u = d["sets"]["FMID"]["displacements"][179]
    assert u == pytest.approx([3.264921e-08, -1.119008e-05, 1.589387e-07])


def test_blank_line_after_header_is_survived():
    # Phase-0 trap: a blank line separates the block header from its data.
    d = parse_dat(DAT_SAMPLE)
    assert 180 in d["sets"]["FMID"]["displacements"]


def test_forces_and_total_are_parsed():
    d = parse_dat(DAT_SAMPLE)
    assert d["sets"]["NSUPP0"]["forces"][501][1] == pytest.approx(500.0)
    assert d["sets"]["NSUPP0"]["total_force"] == pytest.approx([0.0, 500.0, 0.0])


def test_unknown_blocks_are_tolerated():
    d = parse_dat(" stresses (xx,yy,zz) for set EALL and time 0.1000000E+01\n\n"
                  " 1  2.0 3.0 4.0\n")
    assert d["sets"] == {}          # skipped, not our business yet


def test_numeric_garbage_outside_blocks_raises():
    # The parser must DETECT garbage, not silently swallow it.
    with pytest.raises(ValueError, match="line 2"):
        parse_dat("\n 1.0 2.0 3.0\n")
