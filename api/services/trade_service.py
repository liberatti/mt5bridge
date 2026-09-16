from datetime import datetime, timezone
from services.mt5_gateway import gateway_client as mt5
from services.base_service import BaseService
from utils.parsers import ORDER_TYPE_MAP


class TradeService(BaseService):
    def order_check(self, request_dict):
        self.ensure_initialized()
        res = mt5.order_check(request_dict)
        if res is None:
            raise RuntimeError(f"order_check failed: {mt5.last_error()}")
        return res._asdict()

    def order_send(self, request_dict):
        self.ensure_initialized()
        res = mt5.order_send(request_dict)
        if res is None:
            raise RuntimeError(f"order_send failed: {mt5.last_error()}")
        return res._asdict()

    def order_calc_margin(self, action, symbol, volume, price):
        self.ensure_initialized()
        act = ORDER_TYPE_MAP.get(str(action).upper(), action) if isinstance(action, str) else int(action)
        res = mt5.order_calc_margin(act, symbol, float(volume), float(price))
        if res is None:
            raise RuntimeError(f"order_calc_margin failed: {mt5.last_error()}")
        return {"action": action, "symbol": symbol, "volume": float(volume), "price": float(price), "margin": float(res)}

    def order_calc_profit(self, action, symbol, volume, price_open, price_close):
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

    def orders_total(self):
        self.ensure_initialized()
        return {"total": mt5.orders_total()}

    def orders_get(self, symbol=None, group=None, ticket=None):
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

    def positions_total(self):
        self.ensure_initialized()
        return {"total": mt5.positions_total()}

    def positions_get(self, symbol=None, group=None, ticket=None):
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

    def _get_filling_mode(self, symbol, type_filling=None):
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

    def open_order(self, symbol, order_type_str, volume, price=None, sl=None, tp=None, deviation=20, comment="", magic=0, type_filling=None):
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

    def close_position(self, ticket, volume=None, deviation=20, comment="API close"):
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

    def modify_position(self, ticket, sl=None, tp=None):
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

    def cancel_order(self, ticket):
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
