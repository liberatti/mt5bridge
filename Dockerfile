FROM ubuntu:24.04

LABEL maintainer="liberatti"
LABEL description="MetaTrader 5 on Linux with WineHQ and Native Python Flask REST API"

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8 \
    PATH="/opt/wine-staging/bin:${PATH}" \
    PORT=5000 \
    HOST=0.0.0.0

# 1. Dependências do Sistema Operacional, Python nativo e utilitários base
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    wget \
    gnupg \
    locales \
    cabextract \
    xvfb \
    xdotool \
    x11-utils \
    procps \
    net-tools \
    gosu \
    winbind \
    python3 \
    python3-pip \
    python3-venv \
    && locale-gen en_US.UTF-8 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 2. Instalação de dependências Python nativas no Linux
COPY api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --break-system-packages -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

# 3. Habilitação de arquitetura 32-bit (i386) e instalação do WineHQ Staging
RUN dpkg --add-architecture i386 \
    && mkdir -pm755 /etc/apt/keyrings \
    && wget -O /etc/apt/keyrings/winehq-archive.key https://dl.winehq.org/wine-builds/winehq.key \
    && wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/ubuntu/dists/noble/winehq-noble.sources \
    && apt-get update \
    && apt-get install -y --install-recommends winehq-staging \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 4. Download do instalador oficial do MetaTrader 5
RUN mkdir -p /opt/setup \
    && curl -fsSL "https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe" -o /opt/setup/mt5setup.exe \
    && chmod -R 755 /opt/setup

# 5. Criação do usuário não-root (mt5user)
RUN (userdel -r ubuntu 2>/dev/null || true) \
    && (groupdel ubuntu 2>/dev/null || true) \
    && groupadd -g 1000 mt5group \
    && useradd -u 1000 -g mt5group -m -s /bin/bash mt5user \
    && mkdir -p /home/mt5user/.mt5 /home/mt5user/api /opt/wine-template /opt/setup/mql5 \
    && chown -R mt5user:mt5group /home/mt5user /opt/setup /opt/wine-template

# ========================================================
# Construção do Wine Template e Compilação do MQL5 Gateway (como mt5user)
# ========================================================
USER mt5user
ENV WINEPREFIX=/opt/wine-template \
    WINEDEBUG=-all \
    WINEARCH=win64 \
    WINEDLLOVERRIDES="mscoree,mshtml="

COPY --chown=mt5user:mt5group mql5/ /opt/setup/mql5/

# Inicialização do Wine prefix, MT5 e compilação do RestGateway.mq5
RUN Xvfb :99 -screen 0 1024x768x16 >/dev/null 2>&1 & XPID=$! \
    && export DISPLAY=:99 \
    && sleep 2 \
    && echo "==> [1/3] Inicializando Wineboot..." \
    && wine wineboot -u \
    && sleep 2 \
    && echo "==> [2/3] Executando instalador do MetaTrader 5..." \
    && (wine /opt/setup/mt5setup.exe /auto &) \
    && for i in $(seq 1 45); do \
        [ -f "/opt/wine-template/drive_c/Program Files/MetaTrader 5/terminal64.exe" ] && break; \
        sleep 2; \
    done \
    && sleep 3 \
    && echo "==> [3/3] Compilando MQL5 RestGateway Expert Advisor..." \
    && mkdir -p "/opt/wine-template/drive_c/Program Files/MetaTrader 5/MQL5/Experts" \
    && cp -r /opt/setup/mql5/* "/opt/wine-template/drive_c/Program Files/MetaTrader 5/MQL5/" \
    && (cd "/opt/wine-template/drive_c/Program Files/MetaTrader 5" && wine metaeditor64.exe /compile:MQL5\\Experts\\RestGateway.mq5 /log:MQL5\\Experts\\RestGateway.log || true) \
    && sleep 2 \
    && echo "==> Finalizando wineserver..." \


    && wineserver -k 2>/dev/null || true \
    && kill $XPID 2>/dev/null || true

# ========================================================
# Finalização da imagem
# ========================================================
USER root
COPY --chown=mt5user:mt5group api/ /home/mt5user/api/
COPY --chown=mt5user:mt5group mql5/ /opt/setup/mql5/
COPY --chown=mt5user:mt5group config/ /opt/setup/config/
COPY --chown=mt5user:mt5group entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh


# Restaurar variáveis para o runtime
ENV WINEPREFIX=/home/mt5user/.mt5 \
    WINEDEBUG=-all \
    WINEDLLOVERRIDES="mscoree,mshtml=" \
    DISPLAY=:0 \
    SCREEN_RESOLUTION=1280x1024x24

EXPOSE 5000

ENTRYPOINT ["/entrypoint.sh"]
