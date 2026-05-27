from __future__ import annotations
from collections import OrderedDict
from dataclasses import dataclass
from enum import Enum


class OrderType(Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"


class Side(Enum):
    BID = "BID"
    ASK = "ASK"


@dataclass
class Order:
    order_id: int
    quantity: int
    side: Side
    order_type: OrderType
    price: int | None = None  # only limit orders have price


@dataclass
class Fill:
    maker_order_id: int
    taker_order_id: int
    price: int
    qty: int


class PriceLevel:
    CAN_CHANGE_INCREASE_QUANTITY = False

    def __init__(self, price: int):
        self.price = price
        self._queue: "OrderedDict[int,Order]" = OrderedDict()
        self._volume = 0

    @property
    def volume(self) -> int:
        return self._volume

    @property
    def is_empty(self) -> bool:
        return len(self._queue) == 0

    def add(self, order: Order):
        """Add order to the end of the queue"""
        self._queue[order.order_id] = order
        self._volume += order.quantity

    def remove(self, order_id: int) -> Order | None:
        """Remove order from the queue and return it. None if order not found"""
        val = self._queue.pop(order_id, None)
        if val is not None:
            self._volume -= val.quantity
        return val

    def change(self, order_id: int, new_quantity: int):
        """Change quantity but keep the same order id and position in the queue"""
        if order_id in self._queue:
            if (
                not self.CAN_CHANGE_INCREASE_QUANTITY
                and new_quantity > self._queue[order_id].quantity
            ):
                raise ValueError("Increasing quantity is not allowed")
            old_quantity = self._queue[order_id].quantity
            self._queue[order_id].quantity = new_quantity
            self._volume += new_quantity - old_quantity

    def peek(self) -> Order | None:
        """Return the first order in the queue without removing it. None if empty"""
        if self._queue:
            return next(iter(self._queue.values()))
        return None


class LimitOrderBook:
    def __init__(self):
        self.bids: "OrderedDict[int,PriceLevel]" = OrderedDict()
        self.asks: "OrderedDict[int,PriceLevel]" = OrderedDict()
        self._order_id_to_price_level: dict[int, PriceLevel] = {}

    def _add_order(self, order: Order):
        """Add order to the book"""
        book = self.bids if order.side == Side.BID else self.asks
        if order.price not in book:
            book[order.price] = PriceLevel(order.price)
        book[order.price].add(order)
        self._order_id_to_price_level[order.order_id] = book[order.price]

    def _remove_order(self, order_id: int) -> Order | None:
        """Remove order from the book and return it. None if order not found"""
        price_level = self._order_id_to_price_level.pop(order_id, None)
        if price_level is not None:
            val = price_level.remove(order_id)
            if price_level.is_empty:
                # remove the price level if it's empty
                book = self.bids if val.side == Side.BID else self.asks
                del book[price_level.price]
            return val
        return None

    def _change_order(self, order_id: int, new_quantity: int):
        """Change quantity of an order. Does nothing if order not found"""
        price_level = self._order_id_to_price_level.get(order_id)
        if price_level is not None:
            price_level.change(order_id, new_quantity)

    def _replace_order(
        self,
        order_id: int,
        new_quantity: int,
        new_price: int,
        new_order_id: int | None = None,
    ):
        """Replace an order."""
        old_order = self._remove_order(order_id)
        if old_order is not None:
            new_order = Order(
                order_id=new_order_id or order_id,
                quantity=new_quantity,
                side=old_order.side,
                order_type=old_order.order_type,
                price=new_price,
            )
            self._add_order(new_order)

    def _best_opposite_price(self, incoming_order: Order) -> int | None:
        # Check opposite
        if incoming_order.side == Side.BID:
            # incoming order wants to buy
            # so existing price needs to be <= incoming price
            if not self.asks:
                return None
            best_price = min(self.asks.keys())
            if (
                incoming_order.order_type == OrderType.MARKET
                or best_price <= incoming_order.price
            ):
                return best_price
        # asks need to be <= incoming price
        else:
            # incoming order wants to sell
            # so existing price needs to be >= incoming price
            if not self.bids:
                return None
            best_price = max(self.bids.keys())
            if (
                incoming_order.order_type == OrderType.MARKET
                or best_price >= incoming_order.price
            ):
                return best_price
        return None

    def _match_and_rest(self, incoming_order: Order) -> list[Fill]:
        fills = []
        opposite_book = self.asks if incoming_order.side == Side.BID else self.bids
        while incoming_order.quantity > 0:
            best_price = self._best_opposite_price(incoming_order)
            if best_price is None:
                # no more matches possible
                # if market -> stop otherwise add to book
                if incoming_order.order_type == OrderType.LIMIT:
                    self._add_order(incoming_order)
                break
            order = opposite_book[best_price].peek()
            if order.quantity <= incoming_order.quantity:
                # full fill
                fills.append(
                    Fill(
                        maker_order_id=order.order_id,
                        taker_order_id=incoming_order.order_id,
                        price=best_price,
                        qty=order.quantity,
                    )
                )
                incoming_order.quantity -= order.quantity
                self._remove_order(order.order_id)
            else:
                # partial fill
                fills.append(
                    Fill(
                        maker_order_id=order.order_id,
                        taker_order_id=incoming_order.order_id,
                        price=best_price,
                        qty=incoming_order.quantity,
                    )
                )
                self._change_order(
                    order.order_id, order.quantity - incoming_order.quantity
                )
                incoming_order.quantity = 0
        return fills

    @property
    def best_bid(self) -> int | None:
        return max(self.bids) if self.bids else None

    @property
    def best_ask(self) -> int | None:
        return min(self.asks) if self.asks else None

    @property
    def best_bid_volume(self) -> int | None:
        best = self.best_bid
        return self.bids[best].volume if best is not None else None

    @property
    def best_ask_volume(self) -> int | None:
        best = self.best_ask
        return self.asks[best].volume if best is not None else None

    @property
    def quoted_spread(self) -> int | None:
        bid = self.best_bid
        ask = self.best_ask
        if bid is not None and ask is not None:
            return ask - bid
        return None

    @property
    def midprice(self) -> float | None:
        bid = self.best_bid
        ask = self.best_ask
        if bid is not None and ask is not None:
            return (ask + bid) / 2
        return None

    @property
    def microprice(self) -> float | None:
        bid = self.best_bid
        ask = self.best_ask
        if bid is not None and ask is not None:
            bid_vol = self.best_bid_volume or 0
            ask_vol = self.best_ask_volume or 0
            total_vol = bid_vol + ask_vol
            if total_vol > 0:
                return (ask_vol / total_vol) * bid + (bid_vol / total_vol) * ask
        return None

    def submit_limit_order(
        self, order_id: int, quantity: int, side: Side, price: int
    ) -> list[Fill]:
        order = Order(
            order_id=order_id,
            quantity=quantity,
            side=side,
            order_type=OrderType.LIMIT,
            price=price,
        )
        return self._match_and_rest(order)

    def submit_market_order(
        self, order_id: int, quantity: int, side: Side
    ) -> list[Fill]:
        order = Order(
            order_id=order_id, quantity=quantity, side=side, order_type=OrderType.MARKET
        )
        return self._match_and_rest(order)

    def cancel_order(self, order_id: int) -> Order | None:
        return self._remove_order(order_id)

    def display(self) -> str:
        # start with asks in descending order, then bids in descending order
        result = ["Order Book:"]
        result += ["=" * 20]
        for price in sorted(self.asks.keys(), reverse=True):
            result.append(f"Ask: {price} x {self.asks[price].volume}")
        result += ["-" * 20]
        for price in sorted(self.bids.keys(), reverse=True):
            result.append(f"Bid: {price} x {self.bids[price].volume}")
        result += ["=" * 20]
        return "\n".join(result)


def scenario_abc_limit():
    print("Scenario: limit buy 12 @ 103 against A(10)@102, B(5)@102, C(20)@103")
    b = LimitOrderBook()
    b.submit_limit_order(1, 10, Side.ASK, 102)  # A
    b.submit_limit_order(2, 5, Side.ASK, 102)  # B
    b.submit_limit_order(3, 20, Side.ASK, 103)  # C
    print(b.display())
    fills = b.submit_limit_order(99, 12, Side.BID, 103)
    print("Executed Fills:")
    for fill in fills:
        print(fill)
    print(b.display())


def scenario_market():
    print("Scenario: market buy 8 takes from best ask first")
    b = LimitOrderBook()
    b.submit_limit_order(1, 10, Side.ASK, 102)
    b.submit_limit_order(3, 20, Side.ASK, 103)
    print(b.display())
    fills = b.submit_market_order(50, 8, Side.BID)
    print("Executed Fills:")
    for fill in fills:
        print(fill)
    print(b.display())


def scenario_sweep_and_rest():
    print(
        "Scenario: limit buy 20 @ 103 sweeps 102 then 103, rests the remainder at 103"
    )
    b = LimitOrderBook()
    b.submit_limit_order(1, 5, Side.ASK, 102)
    b.submit_limit_order(2, 5, Side.ASK, 103)
    print(b.display())
    fills = b.submit_limit_order(77, 20, Side.BID, 103)
    print("Executed Fills:")
    for fill in fills:
        print(fill)
    print(b.display())

def scenario_two_sided_book():
    print("Scenario: build a two-sided book, then run several orders against it")
    b = LimitOrderBook()
    # --- resting bids (buyers) ---
    b.submit_limit_order(1, 10, Side.BID, 99)
    b.submit_limit_order(2, 15, Side.BID, 98)
    b.submit_limit_order(3, 20, Side.BID, 97)
    # --- resting asks (sellers) ---
    b.submit_limit_order(4, 12, Side.ASK, 101)
    b.submit_limit_order(5, 8, Side.ASK, 102)
    b.submit_limit_order(6, 25, Side.ASK, 103)
    print("Initial book (spread 99 / 101):")
    print(b.display())
    print()
 
    # 1) marketable limit buy: 18 @ 102 -> takes all 12 @101, then 6 @102
    print("Order 1: limit BUY 18 @ 102")
    for f in b.submit_limit_order(100, 18, Side.BID, 102):
        print(" ", f)
    print(b.display())
    print()
 
    # 2) market sell 22 -> hits 99 (10), 98 (12 of 15)
    print("Order 2: market SELL 22")
    for f in b.submit_market_order(101, 22, Side.ASK):
        print(" ", f)
    print(b.display())
    print()
 
    # 3) passive limit buy that does NOT cross: 5 @ 96 -> just rests
    print("Order 3: limit BUY 5 @ 96 (passive, rests)")
    fills = b.submit_limit_order(102, 5, Side.BID, 96)
    print("  fills:", fills)
    print(b.display())
    print()
 
    # 4) cancel a resting order (id 6, the 103 ask)
    print("Order 4: cancel id 6 (ask 25 @ 103)")
    cancelled = b.cancel_order(6)
    print("  cancelled:", cancelled)
    print(b.display())

if __name__ == "__main__":
    scenario_abc_limit()
    scenario_market()
    scenario_sweep_and_rest()
    scenario_two_sided_book()
