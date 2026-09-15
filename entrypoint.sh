#!/usr/bin/env bash
set -e

# If running as root, fix volume permissions and drop to mt5user with gosu
if [ "$(id -u)" = "0" ]; then
    mkdir -p /home/mt5user/.mt5 /home/mt5user/api /tmp/.X11-unix
    chown -R mt5user:mt5group /home/mt5user
    chown root:root /tmp/.X11-unix
    chmod 1777 /tmp/.X11-unix
    exec gosu mt5user "$0" "$@"
fi

# ========================================================
# Running as non-root user (mt5user)
# ========================================================

export HOME=/home/mt5user
export PATH="/opt/wine-staging/bin:${PATH}"
export DISPLAY=${DISPLAY:-:0}
export SCREEN_RESOLUTION=${SCREEN_RESOLUTION:-1280x1024x24}
export WINEPREFIX=${WINEPREFIX:-/home/mt5user/.mt5}
export WINEDEBUG=${WINEDEBUG:--all}
export WINEDLLOVERRIDES="mscoree,mshtml="
export WINEARCH=win64

export MT5_PORTABLE=${MT5_PORTABLE:-1}
export MT5_PATH=${MT5_PATH:-"C:\\Program Files\\MetaTrader 5\\terminal64.exe"}
export MT5_TIMEOUT=${MT5_TIMEOUT:-20000}

MT5_DIR="${WINEPREFIX}/drive_c/Program Files/MetaTrader 5"

echo "========================================================"
echo "      MetaTrader 5 Flask REST API (Headless)            "
echo "========================================================"
echo "Porta da API: ${PORT:-5000}"
echo "Wine Prefix: $WINEPREFIX"
echo "Wine Binary: $(which wine 2>/dev/null || echo 'wine')"
echo "========================================================"

# Cleanup existing X locks
rm -f /tmp/.X0-lock /tmp/.X11-unix/X0

# 1. Start Xvfb (Virtual Framebuffer for headless Wine execution)
echo "[1/3] Iniciando servidor gráfico virtual (Xvfb)..."
Xvfb :0 -screen 0 ${SCREEN_RESOLUTION} -ac +extension GLX +render -noreset >/dev/null 2>&1 &
XVFB_PID=$!
sleep 1

# 2. Check and restore pre-built template if volume is missing essential files (system.reg or terminal64.exe)
echo "[2/3] Verificando integridade do ambiente Wine + MT5..."
if [ ! -f "$WINEPREFIX/system.reg" ] || [ ! -f "$MT5_DIR/terminal64.exe" ]; then
    echo "[2/3] Sincronizando template pre-construido para o volume..."
    if [ -d "/opt/wine-template" ] && [ -f "/opt/wine-template/system.reg" ]; then
        cp -a /opt/wine-template/. "$WINEPREFIX/"
    fi

    # Se ainda faltar terminal64.exe apos template, executar instalador e aguardar
    if [ ! -f "$MT5_DIR/terminal64.exe" ]; then
        echo "[2/3] terminal64.exe ausente. Executando instalador do MetaTrader 5..."
        wine /opt/setup/mt5setup.exe /auto &
        for i in $(seq 1 45); do
            [ -f "$MT5_DIR/terminal64.exe" ] && break
            echo "[2/3] Aguardando download e instalacao do terminal64.exe ($i/45)..."
            sleep 2
        done
        sleep 3
    fi
fi

if [ -f "$MT5_DIR/terminal64.exe" ]; then
    echo "[2/3] Ambiente configurado com sucesso! terminal64.exe presente em $MT5_DIR"
else
    echo "[2/3] AVISO: terminal64.exe nao encontrado em $MT5_DIR."
fi

# 3. Preparacao e inicializacao do MetaTrader 5
echo "[3/3] Preparando e iniciando ambiente do MetaTrader 5..."
if [ -f "$MT5_DIR/terminal64.exe" ]; then
    # Sincronizar scripts MQL5
    mkdir -p "$MT5_DIR/MQL5/Experts" "$MT5_DIR/config"
    if [ -d "/opt/setup/mql5" ]; then
        cp -r /opt/setup/mql5/* "$MT5_DIR/MQL5/" 2>/dev/null || true
    fi

    # Renderizar template Jinja2 do common.ini com variaveis de ambiente
    if [ -f "/opt/setup/config/common.ini.j2" ]; then
        python3 /home/mt5user/api/utils/template.py "/opt/setup/config/common.ini.j2" "$MT5_DIR/config/common.ini"
    fi

    # Compilar RestGateway.mq5
    if [ -f "$MT5_DIR/MQL5/Experts/RestGateway.mq5" ]; then
        echo "[3/3] Compilando RestGateway.mq5 com metaeditor64.exe..."
        (
            cd "$MT5_DIR"
            wine metaeditor64.exe /compile:MQL5\\Experts\\RestGateway.mq5 /log:MQL5\\Experts\\RestGateway.log || true
        )
        sleep 2
        for logf in "$MT5_DIR/MQL5/Experts/RestGateway.log" "$MT5_DIR/metaeditor.log" "$MT5_DIR/logs/metaeditor.log"; do
            if [ -f "$logf" ]; then
                echo "[3/3] === LOG DE COMPILAÇÃO ($logf) ==="
                tail -n 25 "$logf"
                echo "======================================"
            fi
        done
    fi

    # Watchdog continuo para fechar dialogos modais no Xvfb
    (
        while true; do
            sleep 2
            if command -v xdotool >/dev/null 2>&1; then
                xdotool key Escape 2>/dev/null || true
            fi
        done
    ) &
    WATCHDOG_PID=$!

    # Inicializar o terminal MT5 em background com a configuracao common.ini
    echo "[3/3] Iniciando terminal64.exe em background (/portable /config:config\\common.ini)..."
    (
        cd "$MT5_DIR"
        wine terminal64.exe /portable /config:config\\common.ini &
    )
    TERMINAL_PID=$!



    GATEWAY_READY=0
    echo "[3/3] Aguardando conexao do MT5 e inicializacao do RestGateway na porta 22347..."
    for i in $(seq 1 25); do
        if python3 -c "import socket; s = socket.socket(); s.settimeout(0.8); s.connect(('127.0.0.1', 22347)); s.close()" 2>/dev/null; then
            echo "[3/3] MetaTrader 5 RestGateway TCP pronto e respondendo na porta 22347!"
            GATEWAY_READY=1
            break
        fi
        echo "[3/3] Inicializando ambiente MT5 e carregando EA ($i/25)..."
        sleep 1
    done

    if [ "$GATEWAY_READY" -ne 1 ]; then
        echo "========================================================"
        echo " [ERRO FATAL] O MetaTrader 5 Gateway TCP não respondeu  "
        echo "========================================================"
        echo "--> Últimas linhas dos logs do terminal MT5:"
        tail -n 30 "$MT5_DIR/logs/"*.log 2>/dev/null || true
        echo "--> Últimas linhas dos logs do MetaEditor / Experts:"
        tail -n 30 "$MT5_DIR/logs/metaeditor.log" "$MT5_DIR/metaeditor.log" "$MT5_DIR/MQL5/Experts/RestGateway.log" 2>/dev/null || true
        kill $TERMINAL_PID $WATCHDOG_PID $XVFB_PID 2>/dev/null || true
        wineserver -k 2>/dev/null || true
        exit 1
    fi
else
    echo "[ERRO FATAL] terminal64.exe nao encontrado em $MT5_DIR."
    exit 1
fi


echo "========================================================"
echo "      Iniciando Servidor Flask REST API na porta 5000   "
echo "========================================================"

cleanup() {
    echo "Encerrando serviços..."
    kill $TERMINAL_PID $WATCHDOG_PID $XVFB_PID 2>/dev/null || true
    wineserver -k 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM

exec python3 /home/mt5user/api/app.py

