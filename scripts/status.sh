#!/usr/bin/env bash
# Project status snapshot: paste the full output back to the mentor.
set -u
cd "$(dirname "$0")/.."                      # always run from the repo root
[ -f .venv/bin/activate ] && source .venv/bin/activate

echo "=== GIT: last commits ==="
git log --oneline -8
echo
echo "=== GIT: pending changes ==="
git status -s
echo
echo "=== TESTS ==="
python -m pytest -q 2>&1 | tail -3
echo
echo "=== PHASE 1 FILES ==="
ls verifiers tests solutions tasks pyproject.toml 2>&1
echo
echo "=== INTEGRATION: phase-0 data judged by phase-1 verifier ==="
python - <<'EOF'
from verifiers.ccx_io import read_dat
from verifiers.equilibrium import check_equilibrium

d = read_dat("Output/beam_c3d8_20_16_8.dat")
r = [d["sets"][s]["total_force"][1] for s in ("NSUPP0", "NSUPP1")]
print(check_equilibrium({"reactions": r, "applied_load": 1000.0}, tol=1e-6))
EOF

