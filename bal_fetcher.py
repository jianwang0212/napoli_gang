import json
import requests
import ccxt
import time
import os
import pandas as pd
from datetime import datetime, timedelta
import operator
import csv

import cfg

liquid = ccxt.liquid(cfg.liquid_misc_credential)

exchange = liquid
symbols = ['JPY', 'ETH']


def get_fx(currency_f):
    fx = requests.get(
        'https://apilayer.net/api/live?access_key=a1d6d82a3df7cf7882c9dd2b35146d6e&source=USD&format=1').json()
    return fx['quotes']['USD' + currency_f.upper()]


def write_csv():
    now = datetime.utcnow()
    raw_data = exchange.fetch_balance()
    position = {symbol: raw_data['total'][symbol] for symbol in symbols}
    price = exchange.fetch_ticker('ETH/JPY')['last']
    position['total'] = position['JPY'] + position['ETH'] * price
    position['total_USD'] = round(position['total'] / get_fx('JPY'), 1)
    position['price_jpy'] = price
    position['price_usd'] = round(price / get_fx('JPY'), 1)
    position['time'] = now.strftime("%y-%m-%d %H:%M:%S")
    position['utc'] = datetime.timestamp(now)

    print(position)

    if not os.path.isfile("bal.csv"):
        csv_content = pd.DataFrame(position, index=[0]).to_csv(index=False)
    else:
        csv_content = pd.DataFrame(position, index=[0]).to_csv(
            index=False, header=None)

    with open('bal.csv', 'a') as csvfile:
        csvfile.write(csv_content)


def sort_csv():

    x = pd.read_csv("bal.csv")

    x = x.drop_duplicates().sort_values('time', ascending=False)
    x.to_csv('bal.csv', index=False)
    print('sorted')


while True:
    write_csv()
    sort_csv()
    time.sleep(5 * 60)
