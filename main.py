import os
import ccxt
from dataclasses import dataclass
import dataclasses
import typing
import datetime
import numpy as np
from math import floor
import time

import book_server
import risk_server
import passive
from passive import make_markets

import cfg

liquid = ccxt.liquid(cfg.liquid_credential)


riskTolerance = risk_server.initialise_risk_tolerances(liquid.fetch_balance(
)['total']['ETH'], liquid.fetch_ticker('ETH/JPY')['last'])


# risk.get_net_risk()

symbols = ['ETH']
# mkt_snap = book_server.get_market_snap(liquid, symbols)

# get_mm_price('ETH', mkt_snap, risk)
passive_orders = {'ETH': {}}

prev_mkt_snap = None

book_server.cancel_all(liquid)
while True:
    mkt_snaps = []
    mkt_snaps.append(book_server.get_market_snap(liquid, symbols))
    risk = risk_server.update_risk_server(liquid, riskTolerance)
    cur_mkt_snap = mkt_snaps[-1]
    if cur_mkt_snap != prev_mkt_snap:
        print('trade')
    prev_mkt_snap = cur_mkt_snap

    passive_orders = make_markets(liquid, cur_mkt_snap, risk, passive_orders)
    # print(passive_orders)
    time.sleep(2)


# print(mkt_snaps)
    # passive_orders = make_markets(liquid, mkt_snap, risk, passive_orders)
