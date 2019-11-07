#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os, sys, time, pprint, traceback
from contextlib import suppress
from bitshares import BitShares
from bitshares.market import Market
from bitshares.account import Account

# load env
env_dict = os.environ
#print(env_dict)
API_URL = env_dict.get('API_URL')
PRIV_KEY = env_dict.get('PRIV_KEY')
PASSWD = env_dict.get('PASSWD')
#quote:base
MARKET = env_dict.get('MARKET')
BUY_RATE = env_dict.get('BUY_RATE')
SELL_RATE = env_dict.get('SELL_RATE')
BUY_AMOUNT = env_dict.get('BUY_AMOUNT')
SELL_AMOUNT = env_dict.get('SELL_AMOUNT')
QUOTE_MAX = env_dict.get('QUOTE_MAX')
BASE_MAX = env_dict.get('BASE_MAX')
ACCOUNT = env_dict.get('ACCOUNT')
CANCEL_RATE = env_dict.get('CANCEL_RATE')

if CANCEL_RATE == '':
    CANCEL_RATE = 1.0

print('CANCEL_RATE: ')
print(CANCEL_RATE)
print('')

calcPrice = {}
openOrders = []
#quote:base
assets = MARKET.split(':')

bitshares = BitShares(API_URL)
wallet = bitshares.wallet
account = Account(ACCOUNT)


# create wallet
print(bitshares.wallet.getPublicKeys())
if wallet.getPublicKeys() == []:
    wallet.create(PASSWD)
    wallet.addPrivateKey(PRIV_KEY)

#print(wallet.unlocked())
#wallet.unlock(PASSWD)
#print(wallet.unlocked())

print("==="+MARKET+"===")
market = Market(MARKET)

# get balance
def getBalance():
    global account, assets
    quote = account.balance(assets[0])#quote
    base = account.balance(assets[1])#base
    return {'base': base['amount'], 'quote': quote['amount']}

# get price
def getPrice():
    global market, BUY_RATE, SELL_RATE
    ticker = market.ticker()
    #print(ticker)
    sellPrice = ticker['lowestAsk']['price'] * (1 + float(SELL_RATE))
    buyPrice = ticker['highestBid']['price'] * (1 - float(BUY_RATE))
    return {'sellPrice': '%.6f' % sellPrice, 'buyPrice': '%.6f' % buyPrice}

# get open orders
def getOpenOrders():
    global market, ACCOUNT, assets, calcPrice, BUY_RATE, SELL_RATE, PASSWD
    #print(assets, calcPrice)
    openOrders = market.accountopenorders(ACCOUNT)
    #print(openOrders)
    if openOrders == []:
        return {'buy': [], 'sell': []}
    else:
        result = {'buy': [], 'sell': []}
        for order in openOrders:
            order_id = order.get('id')
            order_price = order.get('price')
            #print(order.symbols())
            sym = order.symbols()[0] #base
            if sym == assets[1]:
                # buy order
                order_price = order.get('price')
                order_refer_price = order_price / (1 - float(CANCEL_RATE) * float(BUY_RATE))
                if order_refer_price < float(calcPrice['buyPrice']):
                    if market.bitshares.wallet.unlocked() == False:
                        market.bitshares.wallet.unlock(PASSWD)
                    market.cancel(order_id, account=ACCOUNT)
                    print('------')
                    print('[cancel buy order]', order)
                    print('refer_price:', order_refer_price, 'new_price:', calcPrice['buyPrice'])
                    print('------')
                result['buy'].append(order)
            else:
                # sell order
                order_price = order.invert().get('price')
                order_refer_price = order_price / (1 + float(CANCEL_RATE) * float(SELL_RATE))
                if order_refer_price > float(calcPrice['sellPrice']):
                    if market.bitshares.wallet.unlocked() == False:
                        market.bitshares.wallet.unlock(PASSWD)
                    market.cancel(order_id, account=ACCOUNT)
                    print('------')
                    print('[cancel sell order]', order)
                    print('refer_price:', order_refer_price, 'new_price:', calcPrice['sellPrice'])
                    print('------')
                result['sell'].append(order)
        return result

def main():
    global calcPrice, market, BUY_AMOUNT, SELL_AMOUNT, BASE_MAX, QUOTE_MAX, ACCOUNT, PASSWD
    while True:
        try:
            b = getBalance()
            print(b)
            calcPrice = getPrice()
            print(calcPrice)
            openOrders = getOpenOrders()
            print(openOrders)
            #openOrders = {'buy': [], 'sell': []}
            if openOrders['buy'] == []:
                print('get in buy process')
                if b['quote'] > float(QUOTE_MAX):
                    print('[quote asset too much]')
                else:
                    if float(BUY_AMOUNT) > b['base']:
                        print('[you have not enough base amount to buy]')
                    else:
                        if market.bitshares.wallet.unlocked() == False:
                            market.bitshares.wallet.unlock(PASSWD)
                        quoteAmount = float(BUY_AMOUNT) / float(calcPrice['buyPrice'])
                        market.buy(price=float(calcPrice['buyPrice']), amount=quoteAmount, account=ACCOUNT)
                        print('make buy order success! -->')
                        print(float(calcPrice['buyPrice']))
                        print(quoteAmount)
                        print('<--')
            if openOrders['sell'] == []:
                print('get in sell process')
                if b['base'] > float(BASE_MAX):
                    print('[base asset too much]')
                else:
                    quoteAmount = float(SELL_AMOUNT) / float(calcPrice['sellPrice'])
                    if quoteAmount > b['quote']:
                        print('[you have not enough quote amount to sell]')
                    else:
                        if market.bitshares.wallet.unlocked() == False:
                            market.bitshares.wallet.unlock(PASSWD)
                        market.sell(price=float(calcPrice['sellPrice']), amount=quoteAmount, account=ACCOUNT)
                        print('make sell order success! -->')
                        print(float(calcPrice['sellPrice']))
                        print(quoteAmount)
                        print('<--')
        except Exception as e:
            print('=== ERROR ===')
            print(e)
            traceback.print_exc()
            print('=============')
        time.sleep(5)

if __name__ == '__main__':
    with suppress(KeyboardInterrupt):
        main()
