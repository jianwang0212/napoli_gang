import os
import ccxt
from dataclasses import dataclass
import dataclasses
import typing
import datetime
import numpy as np
from math import floor
import time


@dataclass
class SymbolRisk:
    qty: int
    start_price: int


@dataclass
class RiskTolerance:
    max_risk_per_trade: int
    max_net_risk: typing.Dict[str, int]
    risk_aversion: typing.Dict[str, float]


def initialise_risk_tolerances(pos, price) -> RiskTolerance:
    current_risk = {'ETH': SymbolRisk(
        pos, price)}
    max_risk_per_trade = 100000  # jpy
    max_net_risk = {'ETH': 3000000}
    risk_aversion = {sym: np.log(
        max_risk_per_trade / current_risk[sym].start_price / max_net_risk[sym]) / max_net_risk[sym] for sym in current_risk.keys()}  # -12
    return RiskTolerance(max_risk_per_trade=max_risk_per_trade,
                         max_net_risk=max_net_risk,
                         risk_aversion=risk_aversion)


@dataclass
class RiskServer:
    risk_tolerance: RiskTolerance
    current_risk: typing.Dict[str, SymbolRisk]
    current_fiat: float

    def get_net_risk(self) -> float:
        sym_sum = sum(
            self.current_risk[sym].qty * self.current_risk[sym].start_price for sym in self.current_risk.keys())
        total_sum = self.current_fiat + sym_sum
        return total_sum

    def get_trading_risk(self, sym: str) -> float:
        return self.current_risk[sym].qty * self.current_risk[sym].start_price

    def get_bal_ratio(self, sym: str) -> float:
        return float(self.get_trading_risk(sym) / self.get_net_risk())

    def get_quantity(self, sym: str) -> typing.Tuple[float, float]:
        risk = self.get_trading_risk(sym)  # if pos > 0 , risk < 0

        q_0 = self.risk_tolerance.max_risk_per_trade / \
            self.current_risk[sym].start_price  # base quantiy

        bal_c = sum(
            self.current_risk[sym].qty for sym in self.current_risk.keys())
        bal_f = self.current_fiat / self.current_risk[sym].start_price

        bal_ratio = bal_c / bal_f

        qty_multiply = 0.3
        if bal_ratio >= 1:  # if eth > fiat proportion
            # less than q_0 -> bid less
            bid_qty = qty_multiply * bal_f * \
                np.exp(self.risk_tolerance.risk_aversion[sym] * abs(
                    risk))  # this number is 0.3, the higher the risk, the lower the number
            ask_qty = qty_multiply * bal_c
        else:
            bid_qty = qty_multiply * bal_f
            ask_qty = qty_multiply * bal_c * \
                np.exp(self.risk_tolerance.risk_aversion[sym] * abs(risk))
        return max(bid_qty, 0.01), max(ask_qty, 0.01)


def update_risk_server(session, risk_tolerance: RiskTolerance) -> RiskServer:
    symbols = ['ETH']
    fiat = 'JPY'
    try:
        raw_data = session.fetch_balance()
    except:
        print("race condition")
        time.sleep(0.5)
        raw_data = session.fetch_balance()

    position = {symbol: raw_data['total'][symbol] for symbol in symbols}
    try:
        price = session.fetch_ticker('ETH/JPY')['last']
    except:
        print("price error")
        time.sleep(0.5)
        price = session.fetch_ticker('ETH/JPY')['last']
    current_risk = {'ETH': SymbolRisk(position['ETH'], price)}
    current_fiat = raw_data['total'][fiat]
    return RiskServer(risk_tolerance, current_risk, current_fiat)
