from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union
from services.mt5_gateway import gateway_client as mt5
from services.base_service import BaseService
from utils.parsers import ORDER_TYPE_MAP


class TradeService(BaseService):
    """
    Service handling order placement, simulation, modification, margin/profit computation, and position management.
    """

    def order_check(self, request_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate an order and verify account margin requirements and parameters without sending to market.

        Args:
            request_dict (dict): Trade request parameters (symbol, action, volume, price, type, etc.).

        Returns:
            dict: Simulation result (retcode, balance, equity, margin, margin_free, margin_level, comment).

        Raises:
            RuntimeError: If order check fails.
        """
        self.ensure_initialized()
        res = mt5.order_check(request_dict)
        if res is None:
            raise RuntimeError(f"order_check failed: {mt5.last_error()}")
        return res._asdict()

    def order_send(self, request_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a raw trade transaction request to the MetaTrader 5 trade server.

        Args:
            request_dict (dict): Raw MqlTradeRequest dictionary.

        Returns:
            dict: MqlTradeResult dictionary (retcode, deal, order, volume, price, comment).

        Raises:
            RuntimeError: If dispatching order fails.
        """
        self.ensure_initialized()
        res = mt5.order_send(request_dict)
        if res is None:
            raise RuntimeError(f"order_send failed: {mt5.last_error()}")
        return res._asdict()

    def order_calc_margin(
        self,
        action: Union[str, int],
        symbol: str,
        volume: float,
        price: float,
    ) -> Dict[str, Any]:
        """
        Compute required margin in account currency for an order.

        Args:
            action (str or int): Order type/action (e.g. 'BUY', 'SELL', or integer constant).
            symbol (str): Instrument symbol name.
            volume (float): Order volume in lots.
            price (float): Open price.

        Returns:
            dict: {"action": ..., "symbol": str, "volume": float, "price": float, "margin": float}

        Raises:
            RuntimeError: If calculation fails.
        """
        self.ensure_initialized()
        act = ORDER_TYPE_MAP.get(str(action).upper(), action) if isinstance(action, str) else int(action)
        res = mt5.order_calc_margin(act, symbol, float(volume), float(price))
        if res is None:
            raise RuntimeError(f"order_calc_margin failed: {mt5.last_error()}")
        return {"action": action, "symbol": symbol, "volume": float(volume), "price": float(price), "margin": float(res)}

    def order_calc_profit(
        self,
        action: Union[str, int],
        symbol: str,
        volume: float,
        price_open: float,
        price_close: float,
    ) -> Dict[str, Any]:
        """
        Compute projected profit/loss in account currency for an order.

        Args:
            action (str or int): Order type/action ('BUY', 'SELL').
            symbol (str): Instrument symbol.
            volume (float): Lot volume.
            price_open (float): Open price.
            price_close (float): Close price.

        Returns:
            dict: Calculated profit dictionary with input parameters and float profit.

        Raises:
            RuntimeError: If profit calculation fails.
        """
        self.ensure_initialized()
        act = ORDER_TYPE_MAP.get(str(action).upper(), action) if isinstance(action, str) else int(action)
        res = mt5.order_calc_profit(act, symbol, float(volume), float(price_open), float(price_close))
        if res is None:
            raise RuntimeError(f"order_calc_profit failed: {mt5.last_error()}")
        return {
            "action": action,
            "symbol": symbol,
            "volume": float(volume),
            "price_open": float(price_open),
            "price_close": float(price_close),
            "profit": float(res)
        }

    def orders_total(self) -> Dict[str, int]:
        """
        Get the total count of currently active pending orders.

        Returns:
            dict: {"total": int}
        """
        self.ensure_initialized()
        return {"total": mt5.orders_total()}

    def orders_get(
        self,
        symbol: Optional[str] = None,
        group: Optional[str] = None,
        ticket: Optional[Union[int, str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve active pending orders filtered by symbol, group, or ticket.

        Args:
            symbol (str, optional): Symbol name.
            group (str, optional): Symbol mask pattern.
            ticket (int or str, optional): Unique order ticket ID.

        Returns:
            list[dict]: List of active pending order dictionaries.
        """
        self.ensure_initialized()
        kwargs = {}
        if ticket is not None:
            kwargs["ticket"] = int(ticket)
        elif symbol is not None:
            kwargs["symbol"] = str(symbol)
        elif group is not None:
            kwargs["group"] = str(group)

        orders = mt5.orders_get(**kwargs)
        if orders is None:
            return []
        res = []
        for o in orders:
            item = o._asdict()
            item["time_setup_iso"] = datetime.fromtimestamp(item["time_setup"], tz=timezone.utc).isoformat()
            res.append(item)
        return res

    def positions_total(self) -> Dict[str, int]:
        """
        Get the total count of currently open market positions.

        Returns:
            dict: {"total": int}
        """
        self.ensure_initialized()
        return {"total": mt5.positions_total()}

    def positions_get(
        self,
        symbol: Optional[str] = None,
        group: Optional[str] = None,
        ticket: Optional[Union[int, str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve open market positions filtered by symbol, group, or ticket.

        Args:
            symbol (str, optional): Symbol name.
            group (str, optional): Symbol mask pattern.
            ticket (int or str, optional): Unique position ticket ID.

        Returns:
            list[dict]: List of open position dictionaries with ISO timestamps.
        """
        self.ensure_initialized()
        kwargs = {}
        if ticket is not None:
            kwargs["ticket"] = int(ticket)
        elif symbol is not None:
            kwargs["symbol"] = str(symbol)
        elif group is not None:
            kwargs["group"] = str(group)

        positions = mt5.positions_get(**kwargs)
        if positions is None:
            return []
        res = []
        for p in positions:
            item = p._asdict()
            item["time_iso"] = datetime.fromtimestamp(item["time"], tz=timezone.utc).isoformat()
            if item.get("time_update"):
                item["time_update_iso"] = datetime.fromtimestamp(item["time_update"], tz=timezone.utc).isoformat()
            res.append(item)
        return res

    def _get_filling_mode(self, symbol: str, type_filling: Optional[int] = None) -> int:
        """
        Determine appropriate order filling execution mode for a given symbol.

        Args:
            symbol (str): Instrument symbol.
            type_filling (int, optional): Explicit filling mode override.

        Returns:
            int: MetaTrader 5 filling mode flag constant.
        """
        if type_filling is not None:
            return int(type_filling)
        try:
            sym_info = mt5.symbol_info(symbol)
            if sym_info and hasattr(sym_info, "filling_mode"):
                fm = int(sym_info.filling_mode)
                if fm & 1:
                    return mt5.ORDER_FILLING_FOK
                elif fm & 2:
                    return mt5.ORDER_FILLING_IOC
                elif fm & 4:
                    return mt5.ORDER_FILLING_RETURN
        except Exception:
            pass
        return mt5.ORDER_FILLING_IOC

    def open_order(
        self,
        symbol: str,
        order_type_str: str,
        volume: float,
        price: Optional[float] = None,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        deviation: int = 20,
        comment: str = "",
        magic: int = 0,
        type_filling: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        High-level helper to open a market or pending order.

        Args:
            symbol (str): Instrument symbol (e.g. 'EURUSD').
            order_type_str (str): Order type ('BUY', 'SELL', 'BUY_LIMIT', 'SELL_LIMIT', etc.).
            volume (float): Lot size.
            price (float, optional): Target price. Auto-fetched for market BUY/SELL orders if omitted.
            sl (float, optional): Stop Loss price.
            tp (float, optional): Take Profit price.
            deviation (int, optional): Max allowed slippage in points. Defaults to 20.
            comment (str, optional): Order comment string. Defaults to ''.
            magic (int, optional): Magic number identifier. Defaults to 0.
            type_filling (int, optional): Explicit filling mode.

        Returns:
            dict: Trade execution result dictionary.

        Raises:
            ValueError: If invalid order type or missing price on pending order.
            RuntimeError: If trade request is rejected or fails.
        """
        self.ensure_initialized()
        order_type_str = str(order_type_str).upper()
        order_type = ORDER_TYPE_MAP.get(order_type_str)
        if order_type is None:
            raise ValueError(f"Invalid order type '{order_type_str}'. Valid: {list(ORDER_TYPE_MAP.keys())}")

        mt5.symbol_select(symbol, True)
        if price is None or price <= 0:
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                raise RuntimeError(f"Could not fetch tick for {symbol}")
            if order_type == mt5.ORDER_TYPE_BUY:
                price = tick.ask
            elif order_type == mt5.ORDER_TYPE_SELL:
                price = tick.bid
            else:
                raise ValueError("Price is required for pending orders")

        fill_mode = self._get_filling_mode(symbol, type_filling)
        request = {
            "action": mt5.TRADE_ACTION_DEAL if order_type in (mt5.ORDER_TYPE_BUY, mt5.ORDER_TYPE_SELL) else mt5.TRADE_ACTION_PENDING,
            "symbol": symbol,
            "volume": float(volume),
            "type": order_type,
            "price": float(price),
            "deviation": int(deviation),
            "magic": int(magic),
            "comment": str(comment),
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": fill_mode,
        }

        if sl is not None:
            request["sl"] = float(sl)
        if tp is not None:
            request["tp"] = float(tp)

        res = mt5.order_send(request)
        if res is None:
            raise RuntimeError(f"Order send failed: {mt5.last_error()}")
        res_dict = res._asdict()
        if res.retcode not in (mt5.TRADE_RETCODE_DONE, mt5.TRADE_RETCODE_PLACED):
            raise RuntimeError(f"Order rejected (retcode {res.retcode}): {res.comment}")
        return res_dict

    def close_position(
        self,
        ticket: Union[int, str],
        volume: Optional[float] = None,
        deviation: int = 20,
        comment: str = "API close",
    ) -> Dict[str, Any]:
        """
        High-level helper to close an active open position by ticket ID.

        Args:
            ticket (int or str): Unique position ticket.
            volume (float, optional): Partial volume to close (defaults to full position volume).
            deviation (int, optional): Max allowed slippage in points. Defaults to 20.
            comment (str, optional): Order close comment string. Defaults to 'API close'.

        Returns:
            dict: Trade execution result dictionary.

        Raises:
            ValueError: If position is not found.
            RuntimeError: If close order is rejected.
        """
        self.ensure_initialized()
        positions = mt5.positions_get(ticket=int(ticket))
        if not positions:
            raise ValueError(f"Position {ticket} not found")
        pos = positions[0]
        close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        vol = float(volume) if volume is not None and float(volume) > 0 else float(pos.volume)
        tick = mt5.symbol_info_tick(pos.symbol)
        if tick is None:
            raise RuntimeError(f"Failed to get tick for {pos.symbol}")
        price = tick.bid if close_type == mt5.ORDER_TYPE_SELL else tick.ask

        fill_mode = self._get_filling_mode(pos.symbol)
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": int(ticket),
            "symbol": pos.symbol,
            "volume": vol,
            "type": close_type,
            "price": float(price),
            "deviation": int(deviation),
            "comment": str(comment),
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": fill_mode,
        }
        res = mt5.order_send(request)
        if res is None:
            raise RuntimeError(f"Close failed: {mt5.last_error()}")
        if res.retcode != mt5.TRADE_RETCODE_DONE:
            raise RuntimeError(f"Close rejected (retcode {res.retcode}): {res.comment}")
        return res._asdict()

    def modify_position(
        self,
        ticket: Union[int, str],
        sl: Optional[float] = None,
        tp: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        High-level helper to update Stop Loss and Take Profit levels on an open position.

        Args:
            ticket (int or str): Position ticket ID.
            sl (float, optional): New Stop Loss price.
            tp (float, optional): New Take Profit price.

        Returns:
            dict: Modification trade result dictionary.

        Raises:
            ValueError: If position is not found.
            RuntimeError: If modification fails.
        """
        self.ensure_initialized()
        positions = mt5.positions_get(ticket=int(ticket))
        if not positions:
            raise ValueError(f"Position {ticket} not found")
        pos = positions[0]
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": int(ticket),
            "symbol": pos.symbol,
            "sl": float(sl) if sl is not None else pos.sl,
            "tp": float(tp) if tp is not None else pos.tp,
        }
        res = mt5.order_send(request)
        if res is None:
            raise RuntimeError(f"Modify failed: {mt5.last_error()}")
        if res.retcode not in (mt5.TRADE_RETCODE_DONE, mt5.TRADE_RETCODE_PLACED, mt5.TRADE_RETCODE_NO_CHANGES):
            raise RuntimeError(f"Modify rejected (retcode {res.retcode}): {res.comment}")
        return res._asdict()

    def cancel_order(self, ticket: Union[int, str]) -> Dict[str, Any]:
        """
        Cancel an active pending order by ticket ID.

        Args:
            ticket (int or str): Pending order ticket ID.

        Returns:
            dict: Order cancel trade result dictionary.

        Raises:
            ValueError: If pending order is not found.
            RuntimeError: If cancel is rejected.
        """
        self.ensure_initialized()
        orders = mt5.orders_get(ticket=int(ticket))
        if not orders:
            raise ValueError(f"Order {ticket} not found")
        req = {
            "action": mt5.TRADE_ACTION_REMOVE,
            "order": int(ticket)
        }
        res = mt5.order_send(req)
        if res is None:
            raise RuntimeError(f"Cancel failed: {mt5.last_error()}")
        if res.retcode != mt5.TRADE_RETCODE_DONE:
            raise RuntimeError(f"Cancel rejected (retcode {res.retcode}): {res.comment}")
        return res._asdict()
