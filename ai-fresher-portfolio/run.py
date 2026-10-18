"""Run one portfolio application from the repository root."""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
APPS = {
    "documents": ("company-document-assistant", ["-m", "docassist"]),
    "tickets": ("support-ticket-classifier", ["ticket_app.py"]),
    "churn": ("customer-churn-predictor", ["churn_app.py"]),
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", choices=APPS)
    args = parser.parse_args()
    folder, command = APPS[args.project]
    try:
        result = subprocess.run([sys.executable, *command], cwd=ROOT / "projects" / folder)
        raise SystemExit(result.returncode)
    except KeyboardInterrupt:
        pass
