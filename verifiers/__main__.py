"""Entry point: python -m verifiers ./run_dir"""
import sys

from verifiers.cli import main

sys.exit(main(sys.argv[1:]))
