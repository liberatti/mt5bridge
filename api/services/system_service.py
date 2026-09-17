import os
import time
import shutil
import logging
import subprocess
import threading
from typing import Dict, Any, Optional
from services.mt5_gateway import gateway_client as mt5
from services.base_service import BaseService
from utils.template import render_template as render_ini_template

logger = logging.getLogger("system_service")


class SystemService(BaseService):
    """
    Service responsible for terminal status, build version, error states, and account balance.
    """

    def version(self) -> Dict[str, Any]:
        """
        Retrieve MetaTrader 5 terminal version, build number, and build release date.

        Returns:
            dict: {"version": int, "build": int, "release_date": str}
        """
        self.ensure_initialized()
        v = mt5.version()
        return {"version": v[0], "build": v[1], "release_date": v[2]}

    def last_error(self) -> Dict[str, Any]:
        """
        Retrieve the last recorded error code and description from the terminal.

        Returns:
            dict: {"code": int, "description": str}
        """
        err = mt5.last_error()
        return {"code": err[0], "description": err[1]}

    def terminal_info(self) -> Dict[str, Any]:
        """
        Retrieve current MetaTrader 5 terminal state, connection status, trade permissions, and paths.

        Returns:
            dict: Complete terminal configuration and status properties.

        Raises:
            RuntimeError: If terminal info could not be fetched.
        """
        self.ensure_initialized()
        info = mt5.terminal_info()
        if info is None:
            raise RuntimeError(f"Failed to get terminal info: {mt5.last_error()}")
        return info._asdict()

    def account_info(self) -> Dict[str, Any]:
        """
        Retrieve trading account financial state (balance, equity, profit, margin, leverage).

        Returns:
            dict: Complete account info properties.

        Raises:
            RuntimeError: If account info could not be fetched.
        """
        self.ensure_initialized()
        info = mt5.account_info()
        if info is None:
            raise RuntimeError(f"Failed to get account info: {mt5.last_error()}")
        return info._asdict()

    def login(
        self,
        login: int,
        password: str,
        server: str,
        symbol: Optional[str] = None,
        timeout: int = 45,
    ) -> Dict[str, Any]:
        """
        Dynamically authenticate MetaTrader 5 with new account credentials.

        Updates environment variables, re-renders common.ini, restarts terminal64.exe under Wine,
        and waits for the gateway to reconnect.

        Args:
            login (int): MT5 account login ID.
            password (str): MT5 account password.
            server (str): MT5 broker server name (e.g. MetaQuotes-Demo, ClearCorretora-PRD).
            symbol (str, optional): Default symbol for chart startup.
            timeout (int, optional): Timeout in seconds to wait for gateway reconnection.

        Returns:
            dict: Account financial info after successful authentication.
        """
        logger.info(
            "Initiating dynamic login for account %s on server %s...", login, server
        )

        # 1. Update runtime environment variables
        os.environ["MT5_LOGIN"] = str(login)
        os.environ["MT5_PASSWORD"] = str(password)
        os.environ["MT5_SERVER"] = str(server)
        if not symbol:
            symbol = "PETR4" if "XP" in str(server).upper() else "EURUSD"
        os.environ["MT5_STARTUP_SYMBOL"] = str(symbol)

        # 2. Locate paths
        wineprefix = os.environ.get("WINEPREFIX", "/home/mt5user/.mt5")
        mt5_dir = os.path.join(wineprefix, "drive_c", "Program Files", "MetaTrader 5")
        ini_path = os.path.join(mt5_dir, "config", "common.ini")

        # Synchronize servers.dat catalog if available
        servers_dst = os.path.join(mt5_dir, "config", "servers.dat")
        for srv_candidate in [
            (
                "/opt/setup/config/servers_xp.dat"
                if "XP" in str(server).upper()
                else "/opt/setup/config/servers.dat"
            ),
            "/opt/setup/config/servers.dat",
            os.path.join(
                os.path.dirname(__file__), "..", "..", "config", "servers.dat"
            ),
        ]:
            if os.path.isfile(srv_candidate):
                try:
                    os.makedirs(os.path.dirname(servers_dst), exist_ok=True)
                    shutil.copyfile(srv_candidate, servers_dst)
                    logger.info(
                        "Synchronized servers catalog from %s to %s",
                        srv_candidate,
                        servers_dst,
                    )
                    break
                except Exception as e:
                    logger.warning("Failed to copy servers catalog: %s", e)

        # Locate template candidate
        candidates = [
            "/opt/setup/config/common.ini.j2",
            os.path.join(
                os.path.dirname(__file__), "..", "..", "config", "common.ini.j2"
            ),
            os.path.join(os.path.dirname(__file__), "..", "config", "common.ini.j2"),
            os.path.abspath("config/common.ini.j2"),
        ]
        template_path = None
        for c in candidates:
            if os.path.isfile(c):
                template_path = c
                break

        # 3. Render common.ini with updated credentials
        if template_path:
            logger.info("Re-rendering common.ini from template: %s", template_path)
            try:
                render_ini_template(
                    template_path,
                    ini_path,
                    {
                        "MT5_LOGIN": str(login),
                        "MT5_PASSWORD": str(password),
                        "MT5_SERVER": str(server),
                        "MT5_STARTUP_SYMBOL": str(
                            symbol or os.environ.get("MT5_STARTUP_SYMBOL", "EURUSD")
                        ),
                    },
                )
            except Exception as e:
                logger.error("Failed to render common.ini template: %s", e)
                raise RuntimeError(f"Failed to generate common.ini: {e}")
        else:
            logger.warning(
                "common.ini.j2 template not found. Direct file update will be attempted."
            )

        # 4. Mark uninitialized
        BaseService._initialized = False

        # 5. Terminate existing terminal64.exe process
        logger.info("Stopping active MetaTrader 5 terminal process...")
        if shutil.which("pkill"):
            subprocess.run(["pkill", "-9", "-f", "terminal64.exe"], capture_output=True)
        elif os.name == "nt":
            subprocess.run(
                ["taskkill", "/F", "/IM", "terminal64.exe"], capture_output=True
            )
        time.sleep(2.0)

        # 6. Launch new terminal64.exe process in Wine
        terminal_exe = os.path.join(mt5_dir, "terminal64.exe")
        if os.path.isfile(terminal_exe):
            logger.info(
                "Restarting terminal64.exe in background with updated common.ini..."
            )
            env = dict(os.environ)
            env["DISPLAY"] = os.environ.get("DISPLAY", ":0")
            wine_bin = shutil.which("wine") or "wine"
            cmd = [
                wine_bin,
                "terminal64.exe",
                "/portable",
                r"/config:config\common.ini",
            ]
            subprocess.Popen(
                cmd,
                cwd=mt5_dir,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True if os.name != "nt" else False,
            )

            # Auto-dismiss startup modals in background
            def _dismiss_delayed():
                for _ in range(5):
                    time.sleep(1.5)
                    BaseService._inspect_and_dismiss_modal_windows()

            threading.Thread(target=_dismiss_delayed, daemon=True).start()
        else:
            logger.warning(
                "terminal64.exe not found at %s. Skipping terminal restart.",
                terminal_exe,
            )

        # 7. Wait for Gateway reconnection
        logger.info("Waiting for MT5 TCP Gateway to reconnect...")
        self.ensure_initialized(retries=timeout, delay=1.0)

        # 8. Fetch account info to verify successful connection
        logger.info("Verifying trading account state after login...")
        account_data = None
        for _ in range(15):
            try:
                info = mt5.account_info()
                if info:
                    acc_dict = info._asdict()
                    account_data = acc_dict
                    if acc_dict.get("login") == login:
                        break
            except Exception:
                pass
            time.sleep(1.0)

        if not account_data:
            raise RuntimeError(
                f"Terminal reconectado com sucesso, mas a conta {login} ainda não foi sincronizada."
            )

        logger.info(
            "Dynamic login successful! Account: %s, Server: %s, Balance: %s",
            account_data.get("login"),
            account_data.get("server"),
            account_data.get("balance"),
        )
        return account_data
