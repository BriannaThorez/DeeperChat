# utilities/requirements.py
import subprocess
import sys
import pkg_resources
from typing import List

def check_and_install_requirements(requirements_file: str = "requirements.txt") -> None:
    """
    Check if all packages in requirements.txt are installed.
    If not, install them automatically.
    
    Args:
        requirements_file: Path to the requirements.txt file
    """
    try:
        with open(requirements_file, 'r') as f:
            required_packages = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        print(f"[Requirements] No {requirements_file} file found - skipping package checks")
        return

    installed_packages = {pkg.key: pkg.version for pkg in pkg_resources.working_set}
    missing_packages = []

    for package in required_packages:
        # Handle cases with version specifiers
        package_name = package.split('==')[0].split('>=')[0].split('<=')[0].strip()
        
        if package_name.lower() not in installed_packages:
            missing_packages.append(package)

    if missing_packages:
        print(f"[Requirements] Installing missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', *missing_packages])
            print("[Requirements] Packages installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"[Requirements] Error installing packages: {e}")
    else:
        print("[Requirements] All required packages are already installed")