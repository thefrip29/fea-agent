from verifiers.equilibrium import check_equilibrium


def test_beam_3pb_is_in_equilibrium():
    result = {"reactions": [500.0, 500.0], "applied_load": 1000.0}
    ok, reason = check_equilibrium(result, tol=1e-6)
    assert ok, reason


def test_unbalanced_run_fails():
    result = {"reactions": [400.0, 500.0], "applied_load": 1000.0}
    ok, reason = check_equilibrium(result, tol=1e-6)
    assert not ok   # a FALSE case must be detected

