import subprocess
import os
import pytest

def test_validate_cdf_runs_successfully():
    metadata_path = os.path.abspath("./cross_cdf/data/metadata_cdf.json")
    cdf_path = os.path.abspath("./cross_cdf/data/tyndp_scenarios_cdf.csv")

    result = subprocess.run(
        ["validate-cdf", f"--metadata={metadata_path}", f"--cdf={cdf_path}"],
        capture_output=True,
        text=True
    )

    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)

    # You can assert based on expected success or message
    assert result.returncode == 0
    assert "error" not in result.stderr.lower()

