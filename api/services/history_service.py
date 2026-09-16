from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union
from services.mt5_gateway import gateway_client as mt5
from services.base_service import BaseService
from utils.parsers import parse_date


class HistoryService(BaseService):
    """
    Service for querying historical closed/canceled orders and completed deal executions.
    """

    def history_orders_total(
        self,
        date_from: Optional[Any] = None,
        date_to: Optional[Any] = None,
    ) -> Dict[str, int]:
        """
        Get the total count of orders in trading history within a date range.

        Args:
            date_from (str, int, or datetime, optional): History start datetime. Defaults to 1970-01-01.
            date_to (str, int, or datetime, optional): History end datetime. Defaults to current time.

        Returns:
            dict: {"total": int}
        """
        self.ensure_initialized()
        dt_from = (
            parse_date(date_from)
            if date_from
            else datetime(1970, 1, 1, tzinfo=timezone.utc)
        )
        dt_to = parse_date(date_to) if date_to else datetime.now(tz=timezone.utc)
        return {"total": mt5.history_orders_total(dt_from, dt_to)}

    def history_orders_get(
        self,
        date_from: Optional[Any] = None,
        date_to: Optional[Any] = None,
        group: Optional[str] = None,
        ticket: Optional[Union[int, str]] = None,
        position: Optional[Union[int, str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve historical closed or canceled orders matching filtering criteria.

        Args:
            date_from (str, int, or datetime, optional): History start datetime.
            date_to (str, int, or datetime, optional): History end datetime.
            group (str, optional): Symbol mask filter pattern (e.g. '*EUR*').
            ticket (int or str, optional): Unique order ticket.
            position (int or str, optional): Position identifier associated with the orders.

        Returns:
            list[dict]: Array of historical order dictionaries with ISO timestamps.
        """
        self.ensure_initialized()
        if ticket is not None:
            orders = mt5.history_orders_get(ticket=int(ticket))
        elif position is not None:
            orders = mt5.history_orders_get(position=int(position))
        else:
            dt_from = (
                parse_date(date_from)
                if date_from
                else datetime(1970, 1, 1, tzinfo=timezone.utc)
            )
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
            item["time_setup_iso"] = datetime.fromtimestamp(
                item["time_setup"], tz=timezone.utc
            ).isoformat()
            if item.get("time_done"):
                item["time_done_iso"] = datetime.fromtimestamp(
                    item["time_done"], tz=timezone.utc
                ).isoformat()
            res.append(item)
        return res

    def history_deals_total(
        self,
        date_from: Optional[Any] = None,
        date_to: Optional[Any] = None,
    ) -> Dict[str, int]:
        """
        Get the total count of executed deals in history within a date range.

        Args:
            date_from (str, int, or datetime, optional): History start datetime.
            date_to (str, int, or datetime, optional): History end datetime.

        Returns:
            dict: {"total": int}
        """
        self.ensure_initialized()
        dt_from = (
            parse_date(date_from)
            if date_from
            else datetime(1970, 1, 1, tzinfo=timezone.utc)
        )
        dt_to = parse_date(date_to) if date_to else datetime.now(tz=timezone.utc)
        return {"total": mt5.history_deals_total(dt_from, dt_to)}

    def history_deals_get(
        self,
        date_from: Optional[Any] = None,
        date_to: Optional[Any] = None,
        group: Optional[str] = None,
        ticket: Optional[Union[int, str]] = None,
        position: Optional[Union[int, str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve executed deal trade records matching filtering criteria.

        Args:
            date_from (str, int, or datetime, optional): History start datetime.
            date_to (str, int, or datetime, optional): History end datetime.
            group (str, optional): Symbol mask filter pattern.
            ticket (int or str, optional): Unique deal ticket.
            position (int or str, optional): Position identifier associated with the deals.

        Returns:
            list[dict]: Array of historical deal dictionaries (commission, swap, profit, price, volume, etc.).
        """
        self.ensure_initialized()
        if ticket is not None:
            deals = mt5.history_deals_get(ticket=int(ticket))
        elif position is not None:
            deals = mt5.history_deals_get(position=int(position))
        else:
            dt_from = (
                parse_date(date_from)
                if date_from
                else datetime(1970, 1, 1, tzinfo=timezone.utc)
            )
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
            item["time_iso"] = datetime.fromtimestamp(
                item["time"], tz=timezone.utc
            ).isoformat()
            res.append(item)
        return res
