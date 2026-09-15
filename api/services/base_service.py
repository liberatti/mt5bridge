import os
import time
import glob
import subprocess
import logging
from services.mt5_gateway import gateway_client as mt5

logger = logging.getLogger("base_service")


class BaseService:
    """
    Base class providing common MetaTrader 5 initialization and state management.
    """

    _initialized = False

    @classmethod
    def _inspect_and_dismiss_modal_windows(cls):
        """
        Fecha qualquer diálogo modal de primeiro uso via xdotool no Xvfb.
        """
        try:
            subprocess.run(["xdotool", "key", "Escape"], capture_output=True, timeout=1)
        except Exception:
            pass

    @classmethod
    def _dump_diagnostics(cls, path):
        logger.info("=== DIAGNÓSTICO DO AMBIENTE WINE / MT5 ===")
        # 1. Processos ativos no Linux
        try:
            res = subprocess.run(
                ["ps", "aux"], capture_output=True, text=True, timeout=5
            )
            logger.info("Processos ativos no container:\n%s", res.stdout or res.stderr)
        except Exception as e:
            logger.warning("Falha ao executar ps aux: %s", e)

        # 2. Logs internos gerados pelo MT5
        try:
            wineprefix = os.environ.get("WINEPREFIX", "/home/mt5user/.mt5")
            mt5_dir = os.path.join(wineprefix, "drive_c", "Program Files", "MetaTrader 5")
            log_patterns = [
                os.path.join(mt5_dir, "logs", "*.log"),
                os.path.join(mt5_dir, "MQL5", "Logs", "*.log"),
                os.path.join(mt5_dir, "MQL5", "Experts", "*.log"),
            ]
            for pattern in log_patterns:
                for fpath in glob.glob(pattern):
                    with open(fpath, "r", errors="ignore") as f:
                        lines = f.readlines()[-15:]
                        logger.info("Ultimas linhas de %s:\n%s", fpath, "".join(lines))
        except Exception as e:
            logger.warning("Falha ao verificar logs do MT5: %s", e)
        logger.info("===========================================")

    @classmethod
    def ensure_initialized(cls, retries=15, delay=1.0):
        if cls._initialized:
            return True


        from services.mt5_gateway import gateway_client

        logger.info(
            "Verificando conexao com MetaTrader 5 via Gateway TCP (%s:%d)...",
            gateway_client.host,
            gateway_client.port,
        )

        last_err = None
        for attempt in range(1, retries + 1):
            try:
                # 1. Inspecionar e fechar qualquer diálogo modal pendente no Wine
                cls._inspect_and_dismiss_modal_windows()

                # 2. Testar ping via Gateway TCP puro
                if gateway_client.ping():
                    cls._initialized = True
                    logger.info(
                        "MT5 Gateway TCP conectado com sucesso em %s:%d! Versao: %s",
                        gateway_client.host,
                        gateway_client.port,
                        gateway_client.version(),
                    )
                    return True

                last_err = f"TCP Gateway nao respondeu em {gateway_client.host}:{gateway_client.port}"
                logger.info("Attempt %d/%d: Aguardando inicializacao do Gateway TCP...", attempt, retries)

            except Exception as e:
                last_err = e
                logger.warning("Attempt %d/%d: Erro na verificacao do Gateway: %s", attempt, retries, e)

            if attempt < retries:
                time.sleep(delay)

        cls._initialized = False
        cls._dump_diagnostics(os.environ.get("MT5_PATH", "C:/Program Files/MetaTrader 5/terminal64.exe"))
        raise RuntimeError(f"MT5 Gateway initialization failed: {last_err}")


