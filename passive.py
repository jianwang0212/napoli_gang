import os
import ccxt
from dataclasses import dataclass
import dataclasses
import typing
import datetime
import numpy as np
from math import floor


def get_bal_ratio_step(bal_ratio: float) -> float:
    # bal = 0.8 means ETH / TOTAL = 0.8 -> bal_ratio = 0.3

    if abs(bal_ratio) < 0.05:
        bal_ratio_step = 0
    elif abs(bal_ratio) < 0.1:
        bal_ratio_step = bal_ratio * 0.2
    elif abs(bal_ratio) < 0.4:  # bal_ratio = 0.3, bal_ratio_step = 0.15
        bal_ratio_step = bal_ratio * 0.5
    else:
        bal_ratio_step = 1
    return bal_ratio_step


def get_risk_adjusted_bid_ask_micro_version(bal_ratio: float, fair_price: float, bid_px: float, ask_px: float) -> float:
    spread = ask_px - bid_px
    bid_micro = fair_price - spread / 2
    ask_micro = fair_price + spread / 2
    bal_ratio_step = get_bal_ratio_step(bal_ratio)

    if bal_ratio >= 0:
        bid_m_risk = bid_micro * (1 - bal_ratio_step * 0.01)
        bid_m_risk = min(bid_px, bid_m_risk)
        ask_m_risk = max(ask_px, ask_micro)
    else:
        ask_m_risk = ask_micro * (1 - bal_ratio_step * 0.01)
        ask_m_risk = max(ask_px, ask_m_risk)
        bid_m_risk = min(bid_px, bid_micro)

    return bid_m_risk, ask_m_risk


def get_risk_adjusted_bid_ask(bal_ratio: float, fair_price: float, bid_px: float, ask_px: float) -> float:
    spread = ask_px - bid_px
    bid_micro = fair_price - spread / 2
    ask_micro = fair_price + spread / 2
    bal_ratio_step = get_bal_ratio_step(bal_ratio)

    if bal_ratio >= 0:
        bid_m_risk = bid_micro * (1 - bal_ratio_step * 0.01)
        bid_m_risk = min(bid_px, bid_m_risk)
        ask_m_risk = ask_px
    else:
        ask_m_risk = ask_micro * (1 - bal_ratio_step * 0.01)
        ask_m_risk = max(ask_px, ask_m_risk)
        bid_m_risk = bid_px

    return bid_m_risk, ask_m_risk


def get_mm_price(sym: str, mkt_snap, risk) -> typing.Tuple[float, float]:
    # micro micro price
    fair_price, bid_px, ask_px = mkt_snap.get_weighted_fair(sym, 3)

    # micro + risk_adjustment
    bal_ratio = risk.get_bal_ratio(sym) - 0.5
    print(f"bal_ratio: {bal_ratio}")

    bid_m_risk, ask_m_risk = get_risk_adjusted_bid_ask_micro_version(
        bal_ratio, fair_price, bid_px, ask_px)

    # fee adjustment

    # Alpha adjustment

    # profit margin adjustment

    return round(bid_m_risk, 2), round(ask_m_risk, 2)


def make_markets(session, mkt_snap, risk, orders) -> dict:
    current_timestamp = int(datetime.datetime.fromisoformat(
        mkt_snap.time_stamp).timestamp() * 1000)

    for sym in orders.keys():
        bid_price_us, ask_price_us = get_mm_price(sym, mkt_snap, risk)
        bid_qty, ask_qty = risk.get_quantity(sym)
        print(f'current touch: {mkt_snap.get_touch(sym)}')
        print(f'target us: {bid_price_us, ask_price_us}')
        print(f"target pos: {bid_qty, ask_qty}")

    if orders[sym]:
        order_info = orders[sym]
        # print(order_info)

        bid_us = session.fetch_order(
            order_info['bids'][0]['id'])  # our current bid
        ask_us = session.fetch_order(
            order_info['asks'][0]['id'])  # our current ask

        bid_status = bid_us['status']
        ask_status = ask_us['status']

        # bid_move = bid_price_us != bid_us['price']
        # ask_move = ask_price_us != ask_us['price']

        # if price move within a range, dont change price
        bid_move = False if float(
            abs(bid_price_us - bid_us['price']) / bid_us['price']) < 0.0005 else True
        ask_move = False if float(
            abs(ask_price_us - ask_us['price']) / ask_us['price']) < 0.0005 else True

        # change the following cur_timestamp
        current_timestamp = int(datetime.datetime.fromisoformat(
            mkt_snap.time_stamp).timestamp() * 1000)

        # if one side executed, wait 5 second before post another order
        safe = current_timestamp - \
            order_info['tick'] > 5 * 1000 or (
                bid_status == 'closed' and ask_status == 'closed')

        if (bid_status == 'open' and bid_move) or (bid_status == 'closed' and safe):

            if bid_status == 'open':
                try:
                    session.cancel_order(order_info['bids'][0]['id'])
                except:
                    print('error cancelling bid')

            order_info['bids'][0] = session.create_order(

                symbol='ETH/JPY',
                type='limit',
                side='buy',
                amount=bid_qty,  # bid_qty,
                price=bid_price_us

            )

        if (ask_status == 'open' and ask_move) or (ask_status == 'closed' and safe):

            if ask_status == 'open':
                try:
                    session.cancel_order(order_info['asks'][0]['id'])
                except:
                    print('error cancelling ask')

            order_info['asks'][0] = session.create_order(

                symbol='ETH/JPY',
                type='limit',
                side='sell',
                amount=ask_qty,  # ask_qty,
                price=ask_price_us

            )

        if safe:
            order_info['tick'] = current_timestamp
        orders[sym] = order_info

    # initial order
    else:
        orders[sym]['bids'] = [session.create_order(

            symbol='ETH/JPY',
            type='limit',
            side='buy',
            amount=bid_qty,  # bid_qty,
            price=bid_price_us

        )]

        orders[sym]['asks'] = [session.create_order(

            symbol='ETH/JPY',
            type='limit',
            side='sell',
            amount=ask_qty,  # ask_qty,
            price=ask_price_us
        )]
        orders[sym]['tick'] = current_timestamp
    return orders
