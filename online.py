import Client
from datetime import datetime
import time
import os
import stock
import sys
import time,os
from datetime import datetime,timedelta
import okcoin_websocket
from stock import stock,KLine
import logging

kline5 = None
kline15 = None

stock1Min = stock("btc_cny",stock.OneMin,500)
stock5Min = stock("btc_cny",stock.FiveMin,500)
stock15Min = stock("btc_cny",stock.FifteenMin,500)

okcoin_websocket.stock1Min = stock1Min
okcoin_websocket.stock5Min = stock5Min
okcoin_websocket.stock15Min = stock15Min

while True:
    try:
        kline1 = Client.fetchKline("btc_cny","1min",100,None)

        kline5 = Client.fetchKline("btc_cny","5min",50,None)

        kline15 = Client.fetchKline("btc_cny","15min",30,None)


        k1 = stock1Min.lastKline()

        if k1==0:
            k1 = kline1[-1]
        elif kline1[-1].time-k1.time<=60:
            k1 = kline1[-1]
        else:
            okcoin_websocket.pricelogging.error("kline 1min b=%s,get=%s" % (k1,kline1[-1]));
            break

        k5 = stock5Min.lastKline()

        if k5==0:
            k5 = kline5[-1]
        elif kline5[-1].time-k5.time<=5*60:
            k5 = kline5[-1]
        else:
            okcoin_websocket.pricelogging.error("kline 5min b=%s,get=%s" % (k5,kline5[-1]));
            break


        k15 = stock15Min.lastKline()
        if k15==0:
            k15 = kline15[-1]
        elif kline15[-1].time-k15.time<=15*60:
            k15 = kline15[-1]
        else:
            okcoin_websocket.pricelogging.error("kline 15min b=%s,get=%s" % (k15,kline15[-1]));
            break

        stock1Min.on_kline(k1)
        stock5Min.on_kline(k5)
        stock15Min.on_kline(k15)
        okcoin_websocket.go8()
        time.sleep(2)
    except Exception as e:
        logging.error(e)
