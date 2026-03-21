#!/bin/bash
# VPS Authentication Script for SimplyMiles
#
# This script starts a virtual display (Xvfb) and VNC server so you can
# run the browser-based SimplyMiles login remotely.
#
# Usage:
#   1. SSH to VPS: ssh alex@REDACTED_VPS_IP
#   2. Run: bash ~/aa_scraper/scripts/vps_auth.sh
#   3. Connect VNC Viewer from Mac to VPS_IP:5900 (password: REDACTED_VNC_PASS)
#   4. Complete login in browser window
#   5. Run: screen -r auth (and press Enter to save)
#   6. Test: python scrapers/simplymiles_api.py --test

set -e

# Configuration
DISPLAY_NUM=99
SCREEN_RES="1280x720x24"
VNC_PORT=5900
VNC_PASS="REDACTED_VNC_PASS"

echo "=== SimplyMiles VPS Auth Setup ==="

# Kill any existing processes
pkill -f "Xvfb :${DISPLAY_NUM}" 2>/dev/null || true
pkill -f "x11vnc" 2>/dev/null || true
screen -S auth -X quit 2>/dev/null || true
sleep 1

# Start virtual display
echo "[1/4] Starting Xvfb virtual display..."
Xvfb :${DISPLAY_NUM} -screen 0 ${SCREEN_RES} &
sleep 2

# Set display
export DISPLAY=:${DISPLAY_NUM}

# Start VNC server with password
echo "[2/4] Starting VNC server on port ${VNC_PORT}..."
x11vnc -display :${DISPLAY_NUM} -passwd ${VNC_PASS} -forever -bg -rfbport ${VNC_PORT}
sleep 1

# Get VPS IP
VPS_IP=$(hostname -I | awk '{print $1}')

# Start browser in screen session
echo "[3/4] Launching browser in screen session..."
cd ~/aa_scraper
source venv/bin/activate
screen -dmS auth bash -c "export DISPLAY=:${DISPLAY_NUM} && python scripts/setup_auth.py; exec bash"

echo ""
echo "=========================================="
echo "VNC server ready!"
echo ""
echo "Connect VNC Viewer to: ${VPS_IP}:${VNC_PORT}"
echo "Password: ${VNC_PASS}"
echo ""
echo "After logging in, run:"
echo "  screen -r auth"
echo "Then press Enter to save the session"
echo "=========================================="
echo ""
echo "[4/4] Waiting for you to complete login..."
echo "When done, run: screen -r auth && press Enter"
echo ""
echo "To clean up later, run:"
echo "  pkill -f 'Xvfb :${DISPLAY_NUM}' ; pkill -f x11vnc"
