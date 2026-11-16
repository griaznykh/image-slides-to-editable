#!/usr/bin/env bash
# Creates the Python venv used by the scripts (easyocr + OpenCV + python-pptx, CPU only).
set -euo pipefail
DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$DIR/.venv"
if [ -x "$VENV/bin/python" ] && "$VENV/bin/python" -c "import easyocr, cv2, pptx" 2>/dev/null; then
  echo "venv ready: $VENV"; exit 0
fi
python3 -m venv "$VENV"
"$VENV/bin/pip" install -q --index-url https://download.pytorch.org/whl/cpu torch torchvision
"$VENV/bin/pip" install -q easyocr opencv-python-headless python-pptx pillow
"$VENV/bin/python" -c "import easyocr, cv2, pptx; print('venv ready:', '$VENV')"
