#!/bin/bash



















set -euo pipefail
PIP="pip3 --no-cache-dir"
APT="sudo apt-get -y --no-install-recommends"

BOLD='\033[1m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${BOLD}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
fail()  { echo -e "${RED}[FAIL]${NC}  $*"; exit 1; }






































































































info "=== PHASE 2: SYSTEM LIBRARIES ==="

wait_for_lock() {
  while sudo fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1 || sudo fuser /var/lib/apt/lists/lock >/dev/null 2>&1 || sudo fuser /var/lib/dpkg/lock >/dev/null 2>&1; do
    warn "Apt/Dpkg is locked by another process. Waiting 5 seconds..."
    sleep 5
  done
}

info "Waiting for any background updates to finish..."
wait_for_lock

info "Refreshing apt lists..."
sudo apt-get update -qq

info "Installing required system libraries..."
$APT install \
  python3 \
  python3-pip \
  python3-dev \
  python3-setuptools \
  python3-wheel \
  build-essential \
  libffi-dev \
  libssl-dev \
  sqlite3 \
  libsqlite3-dev \
  portaudio19-dev \
  libportaudio2 \
  libasound2-dev \
  alsa-utils \
  libflac-dev \
  libopus-dev \
  ffmpeg \
  curl \
  wget \
  git \
  ca-certificates

ok "System libraries installed."




info "=== PHASE 3: PYTHON LIBRARIES ==="


info "Upgrading pip, setuptools, wheel..."
python3 -m pip install --break-system-packages --upgrade --ignore-installed pip setuptools wheel


install_pkg() {
  local pkg="$1"
  local extra="${2:-}"
  local tarball_url="${3:-}"

  info "Installing $pkg ..."

  if pip3 install --break-system-packages $extra "$pkg" 2>/dev/null; then
    ok "$pkg installed (pip)"
    return 0
  fi

  warn "$pkg: normal install failed, trying --no-build-isolation ..."
  if pip3 install --break-system-packages --no-build-isolation $extra "$pkg" 2>/dev/null; then
    ok "$pkg installed (--no-build-isolation)"
    return 0
  fi

  if [ -n "$tarball_url" ]; then
    warn "$pkg: pip failed, downloading source tarball ..."
    local tmp_dir
    tmp_dir="$(mktemp -d)"
    local fname
    fname="$(basename "$tarball_url")"
    if wget -q -O "$tmp_dir/$fname" "$tarball_url"; then
      tar -xzf "$tmp_dir/$fname" -C "$tmp_dir" 2>/dev/null || \
        pip3 install --break-system-packages "$tmp_dir/$fname" && \
        { ok "$pkg installed (tarball)"; rm -rf "$tmp_dir"; return 0; }

      local src_dir
      src_dir="$(find "$tmp_dir" -maxdepth 1 -type d | tail -1)"
      if [ -f "$src_dir/setup.py" ]; then
        (cd "$src_dir" && python3 setup.py install --user) && \
          { ok "$pkg installed (setup.py)"; rm -rf "$tmp_dir"; return 0; }
      fi
      rm -rf "$tmp_dir"
    fi
  fi

  warn "$pkg: ALL install methods failed — will continue, but this package may be missing!"
  return 1
}


install_pkg "requests"
install_pkg "numpy"
install_pkg "Pillow"



info "Installing PyAudio and python3-sounddevice via apt for binary stability..."
$APT install python3-pyaudio python3-sounddevice || true


install_pkg "sounddevice"



install_pkg "SpeechRecognition"


install_pkg "pyserial" \
  "" \
  "https://files.pythonhosted.org/packages/source/p/pyserial/pyserial-3.5.tar.gz"


install_pkg "opencv-python-headless" \
  "" \
  ""

install_pkg "pyzbar" \
  "" \
  "https://files.pythonhosted.org/packages/source/p/pyzbar/pyzbar-0.1.9.tar.gz"


install_pkg "flask"
install_pkg "flask-socketio"
install_pkg "python-socketio"
install_pkg "eventlet"


install_pkg "smbus2"
install_pkg "pyserial"
install_pkg "Adafruit-Blinka"
install_pkg "adafruit-circuitpython-mpu6050"
install_pkg "adafruit-circuitpython-ina219"




info "=== PHASE 4: VERIFICATION ==="

FAIL_COUNT=0
check_import() {
  local mod="$1"
  if python3 -c "import $mod" 2>/dev/null; then
    ok "import $mod"
  else
    warn "import $mod (may still work via arduino-app-helpers SDK)"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
}

check_import "requests"
check_import "numpy"
check_import "PIL"
check_import "serial"
check_import "sounddevice"
check_import "speech_recognition"
check_import "flask"
check_import "flask_socketio"
check_import "cv2"
check_import "pyzbar"
check_import "sqlite3"


info "Disk usage after install:"
df -h / 2>/dev/null | tail -1

echo ""
if [ "$FAIL_COUNT" -eq 0 ]; then
  ok "====================================================="
  ok " MES-BOT environment is CLEAN and READY.            "
  ok "====================================================="
else
  warn "=================================================================="
  warn " $FAIL_COUNT package(s) could not be verified.                    "
  warn " They may still work if the Arduino SDK provides them at runtime. "
  warn "=================================================================="
fi
