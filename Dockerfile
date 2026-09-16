FROM ubuntu:24.04

LABEL org.opencontainers.image.title="mt5bridge"
LABEL org.opencontainers.image.description="MetaTrader 5 on Linux with WineHQ and Native Python Flask REST API"
LABEL org.opencontainers.image.source="https://github.com/liberatti/mt5bridge"
LABEL org.opencontainers.image.url="https://github.com/liberatti/mt5bridge"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL maintainer="liberatti"

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8 \
    PATH="/opt/wine-staging/bin:${PATH}" \
    PORT=5000 \
    HOST=0.0.0.0

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
    winbind \
    git \
    python3 \
    python3-pip \
    && locale-gen en_US.UTF-8 \
    && echo 'pcm.!default { type null }' > /etc/asound.conf \
    && echo 'ctl.!default { type null }' >> /etc/asound.conf \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
              /usr/share/doc/* \
              /usr/share/man/* \
              /var/cache/debconf/*-old

RUN dpkg --add-architecture i386 \
    && mkdir -pm755 /etc/apt/keyrings \
    && wget -O /etc/apt/keyrings/winehq-archive.key https://dl.winehq.org/wine-builds/winehq.key \
    && wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/ubuntu/dists/noble/winehq-noble.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends winehq-staging \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
              /usr/share/doc/* \
              /usr/share/man/* \
              /var/cache/debconf/*-old

RUN mkdir -p /opt/setup \
    && curl -fsSL "https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe" -o /opt/setup/mt5setup.exe \
    && chmod -R 755 /opt/setup
RUN (userdel -r ubuntu 2>/dev/null || true) \
    && (groupdel ubuntu 2>/dev/null || true) \
    && groupadd -g 1000 mt5group \
    && useradd -u 1000 -g mt5group -m -s /bin/bash mt5user \
    && mkdir -p /home/mt5user/.mt5 /home/mt5user/api /opt/wine-template /opt/setup/mql5 /tmp/.X11-unix \
    && chmod 1777 /tmp/.X11-unix \
    && chown -R mt5user:mt5group /home/mt5user /opt/setup /opt/wine-template

ENV WINEPREFIX=/opt/wine-template \
    WINEDEBUG=-all \
    WINEARCH=win64 \
    WINEDLLOVERRIDES="mscoree,mshtml="

COPY --chown=mt5user:mt5group mql5/ /opt/setup/mql5/

RUN Xvfb :99 -screen 0 1024x768x16 >/dev/null 2>&1 & XPID=$! \
    && export DISPLAY=:99 \
    && echo "==> [1/3] Inicializando Wineboot..." \
    && wine wineboot -u \
    && wineserver -w \
    && echo "==> [2/3] Executando instalador do MetaTrader 5..." \
    && (wine /opt/setup/mt5setup.exe /auto &) \
    && for i in $(seq 1 45); do \
        [ -f "/opt/wine-template/drive_c/Program Files/MetaTrader 5/terminal64.exe" ] && break; \
        sleep 2; \
    done \
    && wineserver -w \
    && echo "==> [3/3] Compilando MQL5 RestGateway Expert Advisor..." \
    && mkdir -p "/opt/wine-template/drive_c/Program Files/MetaTrader 5/MQL5/Experts" \
    && cp -r /opt/setup/mql5/* "/opt/wine-template/drive_c/Program Files/MetaTrader 5/MQL5/" \
    && (cd "/opt/wine-template/drive_c/Program Files/MetaTrader 5" && wine metaeditor64.exe /compile:MQL5\\Experts\\RestGateway.mq5 /log:MQL5\\Experts\\RestGateway.log || true) \
    && wineserver -w \
    && echo "==> Finalizando wineserver..." \
    && wineserver -k 2>/dev/null || true \
    && kill $XPID 2>/dev/null || true \
    && rm -rf /opt/wine-template/drive_c/users/mt5user/Temp/* \
              /opt/wine-template/drive_c/windows/Logs/* \
              /opt/wine-template/drive_c/windows/temp/* \
              /opt/wine-template/drive_c/users/mt5user/Application\ Data/MetaQuotes/WebInstall*

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --break-system-packages -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

COPY --chown=mt5user:mt5group api/ /home/mt5user/api/
COPY --chown=mt5user:mt5group mql5/ /opt/setup/mql5/
COPY --chown=mt5user:mt5group config/ /opt/setup/config/
COPY --chown=mt5user:mt5group entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

ENV HOME=/home/mt5user \
    WINEPREFIX=/home/mt5user/.mt5 \
    WINEDEBUG=+err \
    WINEDLLOVERRIDES="mscoree,mshtml=" \
    WINEARCH=win64 \
    DISPLAY=:0 \
    SCREEN_RESOLUTION=1024x768x16 \
    MT5_PORTABLE=1 \
    MT5_PATH="C:/Program Files/MetaTrader 5/terminal64.exe" \
    MT5_STARTUP_EXPERT="RestGateway" \
    PORT=5000 \
    HOST=0.0.0.0 \
    THREADS=4 \
    MT5_STARTUP_TIMEOUT=90 \
    MT5_GATEWAY_HOST=127.0.0.1 \
    MT5_GATEWAY_PORT=22347 \
    MT5_GATEWAY_TIMEOUT=10.0
USER mt5user
EXPOSE 5000

ENTRYPOINT ["/entrypoint.sh"]
