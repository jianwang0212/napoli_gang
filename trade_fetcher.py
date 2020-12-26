import json
import requests
import ccxt
import time
import os
import pandas as pd
from datetime import datetime, timedelta
import operator
import csv
epoch = datetime.utcfromtimestamp(0)


liquid = ccxt.liquid({
    'apiKey': '1800187',
    'secret': 'XU5Uf9Dc15SNWD4POVhu1rQOGrIuToO/01AI4nXrOKfBOt4bM4827U6E5fYnH08pnGaRVZ13GnSdQajfNrtpFg=='
})

exchange = liquid
since = exchange.milliseconds() - 86400000  # -1 day from now


def save_and_get_str():
    # SAVE
    all_orders = []
    since = exchange.milliseconds() - 86400000 * 5  # -1 day from now
    while since < exchange.milliseconds():
        symbol = 'ETH/JPY'  # change for your symbol
        limit = 100  # change for your limit
        orders = exchange.fetch_my_trades(symbol, since, limit)
        if len(orders) > 1:
            since = orders[len(orders) - 1]['timestamp']
            all_orders += orders
        else:
            break
    df = pd.DataFrame(
        columns=['utc', 'time', 'type', 'amount', 'price', 'fee'])
    for element in all_orders:
        trade = element['info']
        trade_utc = datetime.utcfromtimestamp(
            float(trade['created_at'])).strftime('%Y-%m-%d %H:%M:%S.%f')
        trades_to_append = str(int(float(trade['created_at']) * 1000)) + ',' + str(trade_utc) + ',' + str(trade['my_side']) + ',' + str(abs(
            float(trade['quantity']))) + ',' + str(float(trade['price'])) + ',' + str(element['fee'])
        df.loc[len(df.index)] = trades_to_append.split(",")
    # df.to_csv('transaction_liquid.csv')

    if not os.path.isfile("transaction_liquid.csv"):
        csv_content = df.to_csv(index=False)
    else:
        csv_content = df.to_csv(
            index=False, header=None)

    with open('transaction_liquid.csv', 'a') as csvfile:
        csvfile.write(csv_content)

def sort_csv():

    x = pd.read_csv("transaction_liquid.csv")
    print(x.iloc[0])
    x = x.drop_duplicates().sort_values('time', ascending=False)
    x.to_csv('transaction_liquid.csv', index=False)
    print('sorted')


while True:
    save_and_get_str()
    sort_csv()

    time.sleep(23 * 60)
