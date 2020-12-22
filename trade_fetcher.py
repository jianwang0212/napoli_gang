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


# def unix_time_secs(dt):
#     return (dt - epoch).total_seconds()


# def get_unix(dt_str, pattern):
#     dt = datetime.strptime(dt_str, pattern)
#     return (dt - datetime(1970, 1, 1)).total_seconds()


# now = int(time.time())

# now_str = datetime.utcfromtimestamp(now).strftime('%Y-%m-%d %H:%M:%S')

# # print(now_str)

# data = {}
# data['exchange'] = 'liquid_jpy'
# apiInstance = settings.exchanges['liquid_jpy']['init']
# currency = settings.exchanges['liquid_jpy']['currency']
# limit = settings.exchanges['liquid_jpy']['limit']

liquid = ccxt.liquid({
    'apiKey': '1800187',
    'secret': 'XU5Uf9Dc15SNWD4POVhu1rQOGrIuToO/01AI4nXrOKfBOt4bM4827U6E5fYnH08pnGaRVZ13GnSdQajfNrtpFg=='
})

exchange = liquid
since = exchange.milliseconds() - 86400000  # -1 day from now
# alternatively, fetch from a certain starting datetime
# since = exchange.parse8601('2018-01-01T00:00:00Z')


def save_and_get_str():
    # SAVE
    all_orders = []
    since = exchange.milliseconds() - 86400000 * 5  # -1 day from now
    while since < exchange.milliseconds():
        symbol = 'ETH/JPY'  # change for your symbol
        limit = 20  # change for your limit
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
        # print(trades_to_append)
        df.loc[len(df.index)] = trades_to_append.split(",")
    df.to_csv('transaction_liquid.csv')


save_and_get_str()
# if not os.path.isfile('./transaction_liquid.csv'):
#     print('file does not exist - creating!')
#     with open('./transaction_liquid.csv') as csvfile:
#         csvfile.write('utc,time,type,amount,price,fee')
#         save_and_get_str()

# if os.path.isfile('./transaction_' + data['exchange'] + '.csv'):
#     save_and_get_str()
#     reader = csv.reader(
#         open('./transaction_' + data['exchange'] + '.csv'), delimiter=",")
#     next(reader)
#     sortedlist = sorted(reader, key=operator.itemgetter(0), reverse=False)
#     # print(sortedlist)
#     with open('./transaction_' + data['exchange'] + '.csv', "wb") as f:
#         fileWriter = csv.writer(f, delimiter=',')
#         fileWriter.writerow(
#             ['utc', 'time', 'type', 'amount', 'price', 'fee', 'currency'])
#         for row in sortedlist:
#             fileWriter.writerow(row)
