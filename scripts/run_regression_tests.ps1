$ErrorActionPreference = "Stop"

# Windows convenience wrapper. The main regression entry point is now cross-platform:
#   python scripts/run_regression_tests.py
python scripts/run_regression_tests.py @args
