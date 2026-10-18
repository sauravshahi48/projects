import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    for name in [
        "company-document-assistant",
        "support-ticket-classifier",
        "customer-churn-predictor",
    ]:
        print(f"Checking {name}", flush=True)
        subprocess.run(
            [sys.executable, "-m", "pytest", "-q"], cwd=ROOT / "projects" / name, check=True
        )
