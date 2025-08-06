import os
import subprocess
import sys
import platform
from pathlib import Path

def run(cmd, shell=False):
    print(f"👉 Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    subprocess.run(cmd, shell=shell, check=True)

def venv_python(venv_dir: str) -> str:
    is_windows = platform.system() == "Windows"
    scripts = "Scripts" if is_windows else "bin"
    exe = "python.exe" if is_windows else "python3"
    return str(Path(venv_dir) / scripts / exe)

def pip_is_available(vpython: str) -> bool:
    try:
        out = subprocess.run(
            [vpython, "-m", "pip", "--version"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False
        )
        if out.returncode == 0:
            print(f"ℹ️ pip in venv: {out.stdout.strip()}")
            return True
        return False
    except Exception:
        return False

def ensure_pip(vpython: str):
    """
    Try to bootstrap pip if it's not present.
    Prefer ensurepip; if that fails, print a helpful message.
    """
    print("📦 Bootstrapping pip in the venv (using ensurepip)...")
    try:
        run([vpython, "-m", "ensurepip", "--upgrade"])
    except subprocess.CalledProcessError as e:
        # Some Python distributions (e.g., certain Conda builds) may disable ensurepip
        print("⚠️ Could not run ensurepip. If pip is still unavailable, consider installing a "
              "standard Python from python.org or creating the venv with that interpreter.")
        raise e

def main():
    # repo_url = "https://github.com/demirayt/cross_cdf.git"
    project_name = "cross_cdf"
    venv_dir = "cross_cdf_env"

    # # Clone the repo
    # if not os.path.exists(project_name):
    #     run(["git", "clone", repo_url])

    # os.chdir(project_name)

    # Create venv with the current interpreter
    run([sys.executable, "-m", "venv", venv_dir])

    is_windows = platform.system() == "Windows"
    vpython = venv_python(venv_dir)
    pip_cmd = [vpython, "-m", "pip"]

    # ---- pip: check first, only install/upgrade if missing ----
    if not pip_is_available(vpython):
        ensure_pip(vpython)
        # After bootstrapping, upgrade to the latest to avoid old bundled wheels.
        run(pip_cmd + ["install", "--upgrade", "pip"])
    else:
        print("✅ pip already present in the venv; skipping reinstall.")

    # Install dependencies
    if os.path.exists("requirements.txt"):
        run(pip_cmd + ["install", "-r", "requirements.txt"])
    run(pip_cmd + ["install", "-e", "."])

    # Print activation help
    print("\n✅ Setup complete.")
    # print(f"👉 Change directory to {project_name}: cd {project_name}")
    if is_windows:
        print(f"👉 To activate: {venv_dir}\\Scripts\\activate")
    else:
        print(f"👉 To activate: source {venv_dir}/bin/activate")
    print("👉 test with: validate-cdf --metadata=./cross_cdf/data/metadata_cdf.json --cdf=./cross_cdf/data/tyndp_scenarios_cdf.csv")

if __name__ == "__main__":
    main()