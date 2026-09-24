#!/usr/bin/env bash
set -e

MT5_DIR="${WINEPREFIX}/drive_c/Program Files/MetaTrader 5"

echo "========================================================"
echo "      MetaTrader 5 Flask REST API (Headless)            "
echo "========================================================"
echo "API Port: ${PORT:-5000}"
echo "Wine Prefix: $WINEPREFIX"
echo "Wine Binary: $(which wine 2>/dev/null || echo 'wine')"
echo "========================================================"

# Configure ALSA dummy null device to suppress audio driver logs
mkdir -p /home/mt5user
cat << 'EOF' > /home/mt5user/.asoundrc
pcm.!default {
    type null
}
ctl.!default {
    type null
}
EOF

# Cleanup existing X locks
rm -f /tmp/.X0-lock /tmp/.X11-unix/X0

# 1. Start Xvfb (Virtual Framebuffer for headless Wine execution)
echo "[1/3] Starting virtual framebuffer display server (Xvfb)..."
Xvfb :0 -screen 0 ${SCREEN_RESOLUTION} -ac +extension GLX +render -noreset >/dev/null 2>&1 &
XVFB_PID=$!
sleep 1

# 2. Check and restore pre-built template if volume is missing essential files (system.reg or terminal64.exe)
echo "[2/3] Checking Wine + MT5 environment integrity..."
if [ ! -f "$WINEPREFIX/system.reg" ] || [ ! -f "$MT5_DIR/terminal64.exe" ]; then
    echo "[2/3] Synchronizing pre-built template into persistent volume..."
    if [ -d "/opt/wine-template" ] && [ -f "/opt/wine-template/system.reg" ]; then
        cp -a /opt/wine-template/. "$WINEPREFIX/"
    fi

    # If terminal64.exe is still missing after template restore, run MT5 installer
    if [ ! -f "$MT5_DIR/terminal64.exe" ]; then
        echo "[2/3] terminal64.exe missing. Running MetaTrader 5 web installer..."
        wine /opt/setup/mt5setup.exe /auto &
        for i in $(seq 1 45); do
            [ -f "$MT5_DIR/terminal64.exe" ] && break
            echo "[2/3] Waiting for terminal64.exe download and installation ($i/45)..."
            sleep 2
        done
        sleep 3
    fi
fi

if [ -f "$MT5_DIR/terminal64.exe" ]; then
    echo "[2/3] Environment configured successfully! terminal64.exe present at $MT5_DIR"
else
    echo "[2/3] WARNING: terminal64.exe not found at $MT5_DIR."
fi

# 3. Preparation and startup of MetaTrader 5
echo "[3/3] Preparing and starting MetaTrader 5 runtime..."
if [ -f "$MT5_DIR/terminal64.exe" ]; then
    # Synchronize MQL5 scripts
    mkdir -p "$MT5_DIR/MQL5/Experts" "$MT5_DIR/config"
    if [ -d "/opt/setup/mql5" ]; then
        cp -r /opt/setup/mql5/* "$MT5_DIR/MQL5/" 2>/dev/null || true
    fi

    # Synchronize server catalog (servers.dat / servers_xp.dat / servers_btg.dat)
    if [[ "$MT5_SERVER" =~ ^XP ]] && [ -f "/opt/setup/config/servers_xp.dat" ]; then
        echo "[3/3] Loading XP Investimentos server catalog (servers_xp.dat)..."
        cp -f "/opt/setup/config/servers_xp.dat" "$MT5_DIR/config/servers.dat"
    elif [[ "$MT5_SERVER" =~ (BTG|BancoBTG) ]] && [ -f "/opt/setup/config/servers_btg.dat" ]; then
        echo "[3/3] Loading BTG Pactual server catalog (servers_btg.dat)..."
        cp -f "/opt/setup/config/servers_btg.dat" "$MT5_DIR/config/servers.dat"
    elif [ -f "/opt/setup/config/servers.dat" ]; then
        echo "[3/3] Synchronizing servers.dat into MT5 config..."
        cp -f "/opt/setup/config/servers.dat" "$MT5_DIR/config/servers.dat"
    fi

    # Smart startup symbol default according to broker environment
    if [[ "$MT5_SERVER" =~ (^XP|BTG|BancoBTG) ]] && [ "${MT5_STARTUP_SYMBOL:-EURUSD}" = "EURUSD" ]; then
        echo "[3/3] B3 broker ($MT5_SERVER) detected: defaulting startup symbol to PETR4 for B3 compatibility."
        export MT5_STARTUP_SYMBOL="PETR4"
    elif [[ "$MT5_SERVER" =~ ^MetaQuotes ]] && [ "$MT5_STARTUP_SYMBOL" = "PETR4" ]; then
        echo "[3/3] MetaQuotes broker detected: defaulting startup symbol to EURUSD for Forex compatibility."
        export MT5_STARTUP_SYMBOL="EURUSD"
    fi

    # Render Jinja2 template for common.ini with environment variables
    if [ -f "/opt/setup/config/common.ini.j2" ]; then
        python3 /home/mt5user/api/utils/template.py "/opt/setup/config/common.ini.j2" "$MT5_DIR/config/common.ini"
    fi

    # Compile RestGateway.mq5
    if [ -f "$MT5_DIR/MQL5/Experts/RestGateway.mq5" ]; then
        echo "[3/3] Compiling RestGateway.mq5 with metaeditor64.exe..."
        (
            cd "$MT5_DIR"
            wine metaeditor64.exe /compile:MQL5\\Experts\\RestGateway.mq5 /log:MQL5\\Experts\\RestGateway.log || true
        )
        sleep 2
        for logf in "$MT5_DIR/MQL5/Experts/RestGateway.log" "$MT5_DIR/metaeditor.log" "$MT5_DIR/logs/metaeditor.log"; do
            if [ -f "$logf" ]; then
                echo "[3/3] === COMPILATION LOG ($logf) ==="
                tail -n 25 "$logf"
                echo "======================================"
            fi
        done
    fi

    # Render Jinja2 template for default chart template (default.tpl)
    mkdir -p "$MT5_DIR/Profiles/Templates" "$MT5_DIR/MQL5/Profiles/Templates" "$MT5_DIR/templates"
    if [ -f "/opt/setup/config/default.tpl.j2" ]; then
        python3 /home/mt5user/api/utils/template.py "/opt/setup/config/default.tpl.j2" "$MT5_DIR/Profiles/Templates/default.tpl"
        cp "$MT5_DIR/Profiles/Templates/default.tpl" "$MT5_DIR/MQL5/Profiles/Templates/default.tpl" 2>/dev/null || true
        cp "$MT5_DIR/Profiles/Templates/default.tpl" "$MT5_DIR/templates/default.tpl" 2>/dev/null || true
    fi

    # Dismiss initial "Open an Account" wizard dialog if it pops up on startup
    (
        sleep 5
        if command -v xdotool >/dev/null 2>&1; then
            WID=$(xdotool search --name "Open an account" 2>/dev/null | head -n 1 || true)
            if [ -n "$WID" ]; then
                xdotool key --window "$WID" Escape 2>/dev/null || true
            else
                xdotool key Escape 2>/dev/null || true
            fi
        fi
    ) &
    WATCHDOG_PID=$!

    # Launch MT5 terminal in background with common.ini startup config
    echo "[3/3] Starting terminal64.exe in background (/portable /config:config\\common.ini)..."
    (
        cd "$MT5_DIR"
        wine terminal64.exe /portable /config:config\\common.ini &
    )
    TERMINAL_PID=$!

    STARTUP_TIMEOUT=${MT5_STARTUP_TIMEOUT:-90}
    GATEWAY_READY=0
    echo "[3/3] Waiting for MT5 startup and RestGateway TCP listener on port 22347 (timeout: ${STARTUP_TIMEOUT}s)..."
    for i in $(seq 1 "$STARTUP_TIMEOUT"); do
        if python3 -c "import socket; s = socket.socket(); s.settimeout(0.8); s.connect(('127.0.0.1', 22347)); s.close()" 2>/dev/null; then
            echo "[3/3] MetaTrader 5 RestGateway TCP ready and responding on port 22347!"
            GATEWAY_READY=1
            break
        fi
        echo "[3/3] Initializing MT5 environment and loading EA ($i/$STARTUP_TIMEOUT)..."
        sleep 1
    done

    if [ "$GATEWAY_READY" -ne 1 ]; then
        echo "========================================================"
        echo " [FATAL ERROR] MetaTrader 5 TCP Gateway failed to respond"
        echo "========================================================"
        echo "--> Last lines of MT5 terminal logs:"
        tail -n 30 "$MT5_DIR/logs/"*.log 2>/dev/null || true
        echo "--> Last lines of MQL5 Expert Advisor logs:"
        tail -n 30 "$MT5_DIR/MQL5/Logs/"*.log "$MT5_DIR/MQL5/logs/"*.log 2>/dev/null || true
        echo "--> Last lines of MetaEditor logs:"
        tail -n 30 "$MT5_DIR/logs/metaeditor.log" "$MT5_DIR/metaeditor.log" "$MT5_DIR/MQL5/Experts/RestGateway.log" 2>/dev/null || true
        kill $TERMINAL_PID $WATCHDOG_PID $XVFB_PID 2>/dev/null || true
        wineserver -k 2>/dev/null || true
        exit 1
    fi
else
    echo "[FATAL ERROR] terminal64.exe not found at $MT5_DIR."
    exit 1
fi

echo "========================================================"
echo "      Starting Flask REST API Server on port 5000       "
echo "========================================================"

cleanup() {
    echo "Shutting down services..."
    kill $TERMINAL_PID $WATCHDOG_PID $XVFB_PID 2>/dev/null || true
    wineserver -k 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM

exec python3 /home/mt5user/api/app.py
