#!/bin/bash
set -euo pipefail

# Only run in remote (Claude Code on the web) environments
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

echo "Instalando dependencias del Transcriptor de Videos..."

# Install core dependencies (skip PyQt5 — no display in remote env)
pip install --quiet \
  "google-generativeai>=0.8.0" \
  "tqdm>=4.66.0" \
  "python-dotenv>=1.0.0"

# moviepy and faster-whisper are large; install if not already present
python -c "import moviepy" 2>/dev/null || pip install --quiet "moviepy>=1.0.3"
python -c "import faster_whisper" 2>/dev/null || pip install --quiet "faster-whisper>=1.0.0"

echo "Dependencias listas."
