# Clean-environment smoke test for PRAE.
#
# Builds a minimal image from a stock Python base and runs the full
# test suite. The integration suite (tests/integration/test_end_to_end.py)
# exercises the complete PRAE lifecycle in a fresh project:
#   bootstrap -> init -> new_track -> new_exp -> record_result
#   -> lock_infra -> check_phase_gate -> generate_phase_gate -> advance_phase
#
# This gives a locally reproducible clean-environment check that does
# not depend on GitHub Actions.
#
# Usage:
#   docker build -t prae-smoke .
#   docker run --rm prae-smoke
#
# To drop into a shell inside the clean environment instead:
#   docker run --rm -it prae-smoke bash

FROM python:3.12-slim

WORKDIR /prae
COPY . /prae

RUN pip install --no-cache-dir pyyaml pytest pytest-cov

# Default: run the full suite as the clean-env smoke.
CMD ["pytest", "tests/", "-v"]
