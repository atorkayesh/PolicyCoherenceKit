#!/usr/bin/env bash
# Starts a virtual X display, a VNC server, the noVNC web client, and Policy Coherence Kit.
# The GUI is then reachable in a browser at http://<host>:<published port>/.
#
# APP_MODE=dev  -> restart the GUI whenever Python files under /app change
# APP_MODE=prod -> require VNC_PASSWORD and restart the GUI if it is closed or crashes
set -euo pipefail

APP_MODE="${APP_MODE:-prod}"
DISPLAY="${DISPLAY:-:99}"
SCREEN_GEOMETRY="${SCREEN_GEOMETRY:-1440x900x24}"
VNC_PORT="${VNC_PORT:-5900}"
VNC_PASSWORD="${VNC_PASSWORD:-}"
WORKSPACE="${WORKSPACE:-/workspace}"
export DISPLAY

log() { echo "[policycoherencekit] $*"; }

if [[ "$APP_MODE" == "prod" && -z "$VNC_PASSWORD" ]]; then
    log "VNC_PASSWORD must be set in production (see .env.example)." >&2
    exit 1
fi

if (( ${#VNC_PASSWORD} > 8 )); then
    log "Note: VNC passwords are limited to 8 characters; only the first 8 are checked." >&2
fi

# Remove a stale display lock left behind by a container restart.
display_number="${DISPLAY#:}"
rm -f "/tmp/.X${display_number}-lock" "/tmp/.X11-unix/X${display_number}"

log "Starting virtual display ${DISPLAY} (${SCREEN_GEOMETRY})"
Xvfb "$DISPLAY" -screen 0 "$SCREEN_GEOMETRY" -nolisten tcp &

for _ in $(seq 1 50); do
    [[ -S "/tmp/.X11-unix/X${display_number}" ]] && break
    sleep 0.1
done

openbox &

vnc_auth=(-nopw)
if [[ -n "$VNC_PASSWORD" ]]; then
    mkdir -p "$HOME/.vnc"
    x11vnc -storepasswd "$VNC_PASSWORD" "$HOME/.vnc/passwd" >/dev/null
    vnc_auth=(-rfbauth "$HOME/.vnc/passwd")
fi

# VNC only listens inside the container; browsers connect through websockify/noVNC.
x11vnc -display "$DISPLAY" -localhost -rfbport "$VNC_PORT" -forever -shared -quiet "${vnc_auth[@]}" &

log "Serving noVNC on container port 6080"
websockify --web /usr/share/novnc "0.0.0.0:6080" "localhost:${VNC_PORT}" >/dev/null 2>&1 &

# Run from the workspace so file dialogs open next to examples/ and exports/. The app
# finds its modules and fonts relative to main.py, so the working directory is free.
mkdir -p "$WORKSPACE/exports"
cd "$WORKSPACE"

if [[ "$APP_MODE" == "dev" ]]; then
    log "Starting Policy Coherence Kit in dev mode (reloads on changes in /app)"
    watchfiles --filter python --sigint-timeout 1 "python /app/main.py" /app &
else
    log "Starting Policy Coherence Kit"
    (while true; do python /app/main.py || true; log "App exited; restarting"; sleep 1; done) &
fi

# If any of the services above dies, exit so Docker's restart policy recovers the container.
wait -n
log "A service exited; stopping container" >&2
exit 1
