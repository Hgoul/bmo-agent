#!/bin/bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$BASE_DIR"

# Give the desktop session (audio, network) a moment to finish settling
# before we launch, since this runs right as the desktop autostarts.
sleep 5

source venv/bin/activate
exec python agent.py >> agent_run.log 2>&1
