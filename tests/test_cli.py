"""CLI tests: a healthy run PASSes, every poison FAILs with the right reason."""
import pytest

from verifiers.cli import run_checks

BEAM = {"P": 1000.0, "L": 1.0, "E": 2.1e11, "b": 0.1, "h": 0.1}


def _dat(fy0=500.0, fy1=500.0, vy=1.12075e-5):
    """A minimal but real-shaped .dat: FMID displacements + two support totals."""
    return f"""displacements (x,y,z) for set FMID and time 0.000000

        21  1.26100E-08 -{vy:.5E}  0.00000E+00
        63  1.26100E-08 -{vy:.5E}  0.00000E+00

 total force (fx,fy,fz) for set NSUPP0 and time 0.000000
  0.00000E+00  {fy0:.5E}  0.00000E+00

 total force (fx,fy,fz) for set NSUPP1 and time 0.000000
  0.00000E+00  {fy1:.5E}  0.00000E+00
"""


def _frd(sxx=1.45e6):
    """A minimal .frd: bottom-fiber node 1 carries sxx, node 2 (mid-height) zero."""
    return f""" -1         1 0.00000E+00 0.00000E+00 0.00000E+00
 -1         2 0.00000E+00 5.00000E-02 0.00000E+00
 -3
 -4  STRESS      6    1
 -5  SXX         1    4    1    1
 -5  SYY         1    4    2    2
 -5  SZZ         1    4    3    3
 -5  SXY         1    4    1    2
 -5  SYZ         1    4    2    3
 -5  SZX         1    4    3    1
 -1         1 {sxx:.5E} 0.00000E+00 0.00000E+00 0.00000E+00 0.00000E+00 0.00000E+00
 -1         2 0.00000E+00 0.00000E+00 0.00000E+00 0.00000E+00 0.00000E+00 0.00000E+00
 -3
"""


@pytest.fixture
def run_dir(tmp_path):
    def make(**kw):
        (tmp_path / "run.dat").write_text(
            _dat(**{k: v for k, v in kw.items() if k in ("fy0", "fy1", "vy")}))
        (tmp_path / "run.frd").write_text(_frd(kw.get("sxx", 1.45e6)))
        return tmp_path
    return make


def test_healthy_run_passes(run_dir):
    ok, verdicts = run_checks(run_dir(), BEAM)
    assert ok
    assert [name for name, _, _ in verdicts] == ["equilibrium", "bounds", "stress"]


def test_unbalanced_run_fails_with_reason(run_dir):
    # Poison 1: reactions 500 + 400 vs load 1000.
    ok, verdicts = run_checks(run_dir(fy1=400.0), BEAM)
    assert not ok
    name, eq_ok, eq_reason = verdicts[0]
    assert name == "equilibrium" and not eq_ok and "gap" in eq_reason


def test_units_error_fails_above(run_dir):
    # Poison 2: deflection in mm read as meters.
    ok, verdicts = run_checks(run_dir(vy=1.12075e-2), BEAM)
    assert not ok
    name, b_ok, b_reason = verdicts[1]
    assert name == "bounds" and not b_ok and "above" in b_reason


def test_locked_mesh_fails_below(run_dir):
    # Poison 3: shear locking (the nx=10 signature).
    ok, verdicts = run_checks(run_dir(vy=8.81e-6), BEAM)
    assert not ok
    name, b_ok, b_reason = verdicts[1]
    assert name == "bounds" and not b_ok and "below" in b_reason


def test_flat_stress_fails_the_third_voice(run_dir):
    # Poison 4: stresses ~1000x too small (wrong E or slipped decimal).
    ok, verdicts = run_checks(run_dir(sxx=1.45e3), BEAM)
    assert not ok
    name, s_ok, s_reason = verdicts[2]
    assert name == "stress" and not s_ok and "below" in s_reason


def test_missing_dat_raises(tmp_path):
    (tmp_path / "run.frd").write_text(_frd())
    with pytest.raises(ValueError):
        run_checks(tmp_path, BEAM)


def test_missing_frd_raises(tmp_path):
    (tmp_path / "run.dat").write_text(_dat())
    with pytest.raises(ValueError):
        run_checks(tmp_path, BEAM)


def test_main_exit_codes(run_dir, capsys):
    from verifiers.cli import main
    assert main([str(run_dir())]) == 0            # healthy: PASS, exit 0
    assert main([str(run_dir(fy1=400.0))]) == 1  # poisoned: FAIL, exit 1
    assert "FAIL" in capsys.readouterr().out

