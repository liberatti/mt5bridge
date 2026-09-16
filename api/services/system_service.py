import logging
from typing import Dict, Any
from services.mt5_gateway import gateway_client as mt5
from services.base_service import BaseService

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

