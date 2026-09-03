import importlib
import importlib.util
import os
import subprocess
import sys


_PYTHON_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = "/app" if os.path.isdir("/app") else os.path.dirname(_PYTHON_DIR)
_ASSETS_DIR = os.path.join(_PROJECT_ROOT, "assets")
_REQUIREMENTS_PATH = os.path.join(_PROJECT_ROOT, "requirements.txt")

_PACKAGE_IMPORTS = {
    "numpy": "numpy",
    "Pillow": "PIL",
    "reportlab": "reportlab",
    "qrcode": "qrcode",
    "smbus2": "smbus2",
    "pyserial": "serial",
    "Adafruit-Blinka": "board",
    "adafruit-circuitpython-mpu6050": "adafruit_mpu6050",
    "adafruit-circuitpython-ina219": "adafruit_ina219",
}


def _requirements_packages() -> list[str]:
    if not os.path.isfile(_REQUIREMENTS_PATH):
        return []
    packages: list[str] = []
    with open(_REQUIREMENTS_PATH, encoding="utf-8") as req:
        for line in req:
            package = line.strip()
            if package and not package.startswith("#"):
                packages.append(package)
    return packages


def _module_for_package(package: str) -> str:
    base = package.split("==", 1)[0].split(">=", 1)[0].split("<=", 1)[0].strip()
    return _PACKAGE_IMPORTS.get(base, base.replace("-", "_"))


def _can_import(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def _run_pip(args: list[str]) -> bool:
    result = subprocess.run(
        [sys.executable, "-m", "pip", *args],
        check=False,
        text=True,
    )
    importlib.invalidate_caches()
    return result.returncode == 0


def _install_package(package: str) -> None:
    module_name = _module_for_package(package)
    if _can_import(module_name):
        return

    print(f"[BOOT] Missing {module_name}; installing {package}.", flush=True)
    attempts = [
        ["install", "--find-links", _ASSETS_DIR, package],
        ["install", "--user", package],
        ["install", package],
    ]

    for args in attempts:
        if _run_pip(args) and _can_import(module_name):
            return

    try:
        import ensurepip

        ensurepip.bootstrap()
        importlib.invalidate_caches()
    except Exception as e:
        print(f"[BOOT] ensurepip failed while installing {package}: {e}", flush=True)

    if _run_pip(["install", package]) and _can_import(module_name):
        return

    raise ImportError(f"Unable to install required package {package!r} for module {module_name!r}")


def ensure_runtime_dependencies(packages: list[str] | None = None) -> None:
    
    for package in packages or _requirements_packages():
        _install_package(package)
