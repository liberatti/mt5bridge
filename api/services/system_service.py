import logging
from services.mt5_gateway import gateway_client as mt5
from services.base_service import BaseService

logger = logging.getLogger("system_service")


class SystemService(BaseService):
    def version(self):
        self.ensure_initialized()
        v = mt5.version()
        return {"version": v[0], "build": v[1], "release_date": v[2]}

    def last_error(self):
        err = mt5.last_error()
        return {"code": err[0], "description": err[1]}

    def terminal_info(self):
        self.ensure_initialized()
        info = mt5.terminal_info()
        if info is None:
            raise RuntimeError(f"Failed to get terminal info: {mt5.last_error()}")
        return info._asdict()

    def account_info(self):
        self.ensure_initialized()
        info = mt5.account_info()
        if info is None:
            raise RuntimeError(f"Failed to get account info: {mt5.last_error()}")
        return info._asdict()
