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
        session.cancel_order(open_order['id'])
