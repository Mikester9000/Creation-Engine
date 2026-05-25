#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."

echo "--- Generating test assets (Python pipeline) ---"
TMP_OUT="$(mktemp -d)"
trap 'rm -rf "$TMP_OUT"' EXIT

if ! command -v creation-engine >/dev/null 2>&1; then
  echo "Error: creation-engine CLI not found on PATH. Install it with: pip install -e ."
  exit 1
fi

creation-engine texture --prompt "ps2 jrpg stone" --seed 42 --output "$TMP_OUT"
creation-engine texture --prompt "ps2 jrpg lava rock" --seed 123 --output "$TMP_OUT"
creation-engine map --prompt "forest" --width 20 --height 15 --seed 42 --output "$TMP_OUT"
creation-engine map --prompt "forest with river" --width 20 --height 15 --seed 7 --output "$TMP_OUT"
creation-engine mesh --prompt "ps2 jrpg stone pillar" --seed 42 --output "$TMP_OUT"
creation-engine full-bundle --seed 99 --output "$TMP_OUT"

echo "--- Running quality gate ---"
creation-engine quality-check --output "$TMP_OUT"
creation-engine bundle-audit --output "$TMP_OUT"
creation-engine release-check --output "$TMP_OUT"

echo "--- Running Python test suite ---"
python3 -m pytest tests/test_backend_and_api.py tests/test_cli.py tests/test_gui.py -q

echo "All tests complete."
