import os
import ccxt
from dataclasses import dataclass
import dataclasses
import typing
import datetime
import numpy as np
from math import floor


@dataclass
class Book:
    sym: str
    raw_data: dict


@dataclass
class Level:
    price: float
    qrt: float


@dataclass
class Market:
    raw_data: dict
    time_stamp: str = dataclasses.field(
        default_factory=lambda: datetime.datetime.now().isoformat())
    books: typing.Dict[str, Book] = dataclasses.field(init=False, hash=False)

    def __post_init__(self):
        object.__setattr__(self, 'books', {sym: Book(
            sym, self.raw_data[sym]) for sym in self.raw_data.keys()})

    def get_touch(self, sym: str) -> typing.Tuple[Level, Level]:
        return self.books[sym].raw_data['bids'][0], self.books[sym].raw_data['asks'][0]

    def get_weighted_fair(self, sym: str, num_levels: int):
        bids = self.books[sym].raw_data['bids'][:num_levels]
        asks = self.books[sym].raw_data['asks'][:num_levels]
        fair_values = []
        for i in range(num_levels):
            bid, ask = bids[i], asks[i]
            fair = ((bid[0] * ask[1] + bid[1] * ask[0])) / (bid[1] + ask[1])
            fair_values.append(fair)
        final_fair = np.mean(fair_values)
        # return the fair (in the middle), BB,BO
        return max(min(final_fair, asks[0][0]), bids[0][0]), bids[0][0], asks[0][0]


def get_market_snap(session, symbols) -> Market:
    raw_data = {sym: session.fetch_order_book(sym + '/JPY') for sym in symbols}
    return Market(raw_data)


def cancel_all(session):
    open_orders = session.fetch_open_orders()
    for open_order in open_orders:
        try:
            session.cancel_order(open_order['id'])
        except:
            print('error cancelling all orders')


# ccxt.base.errors.OrderNotFound: liquid order closed already: {"id": 3679092174, "order_type": "limit", "quantity": "0.16141821", "disc_quantity": "0.0", "iceberg_total_quantity": "0.0", "side": "buy", "filled_quantity": "0.16141821", "price": 63546.0, "created_at": 1608920427, "updated_at": 1608920461, "status": "filled", "leverage_level": 1, "source_exchange": "QUOINE", "product_id": 29, "margin_type": null, "take_profit": null, "stop_loss": null, "trading_type": "spot", "product_code": "CASH", "funding_currency": "JPY", "crypto_account_id": null, "currency_pair_code": "ETHJPY", "average_price": 63546.0, "target": "spot", "order_fee": 0.0, "source_action": "manual", "unwound_trade_id": null, "trade_id": null, "client_order_id": null}
