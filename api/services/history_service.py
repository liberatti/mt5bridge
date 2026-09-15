from datetime import datetime, timezone
from services.mt5_gateway import gateway_client as mt5
from services.base_service import BaseService
from utils.parsers import parse_date


class HistoryService(BaseService):
    def history_orders_total(self, date_from=None, date_to=None):
        self.ensure_initialized()
        dt_from = parse_date(date_from) if date_from else datetime(1970, 1, 1, tzinfo=timezone.utc)
        dt_to = parse_date(date_to) if date_to else datetime.now(tz=timezone.utc)
        return {"total": mt5.history_orders_total(dt_from, dt_to)}

    def history_orders_get(self, date_from=None, date_to=None, group=None, ticket=None, position=None):
        self.ensure_initialized()
        if ticket is not None:
            orders = mt5.history_orders_get(ticket=int(ticket))
        elif position is not None:
            orders = mt5.history_orders_get(position=int(position))
        else:
            dt_from = parse_date(date_from) if date_from else datetime(1970, 1, 1, tzinfo=timezone.utc)
            dt_to = parse_date(date_to) if date_to else datetime.now(tz=timezone.utc)
            if group is not None:
                orders = mt5.history_orders_get(dt_from, dt_to, group=group)
            else:
                orders = mt5.history_orders_get(dt_from, dt_to)

        if orders is None:
            return []
        res = []
        for o in orders:
            item = o._asdict()
            item["time_setup_iso"] = datetime.fromtimestamp(item["time_setup"], tz=timezone.utc).isoformat()
            if item.get("time_done"):
                item["time_done_iso"] = datetime.fromtimestamp(item["time_done"], tz=timezone.utc).isoformat()
            res.append(item)
        return res

    def history_deals_total(self, date_from=None, date_to=None):
        self.ensure_initialized()
        dt_from = parse_date(date_from) if date_from else datetime(1970, 1, 1, tzinfo=timezone.utc)
        dt_to = parse_date(date_to) if date_to else datetime.now(tz=timezone.utc)
        return {"total": mt5.history_deals_total(dt_from, dt_to)}

    def history_deals_get(self, date_from=None, date_to=None, group=None, ticket=None, position=None):
        self.ensure_initialized()
        if ticket is not None:
            deals = mt5.history_deals_get(ticket=int(ticket))
        elif position is not None:
            deals = mt5.history_deals_get(position=int(position))
        else:
            dt_from = parse_date(date_from) if date_from else datetime(1970, 1, 1, tzinfo=timezone.utc)
            dt_to = parse_date(date_to) if date_to else datetime.now(tz=timezone.utc)
            if group is not None:
                deals = mt5.history_deals_get(dt_from, dt_to, group=group)
            else:
                deals = mt5.history_deals_get(dt_from, dt_to)

        if deals is None:
            return []
        res = []
        for d in deals:
            item = d._asdict()
            item["time_iso"] = datetime.fromtimestamp(item["time"], tz=timezone.utc).isoformat()
            res.append(item)
        return res
