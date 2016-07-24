#!/usr/bin/python
# -*- coding: utf-8 -*-
# encoding: utf-8
#客户端调用，用于查看API返回结果

from OkcoinSpotAPI import OKCoinSpot
from OkcoinFutureAPI import OKCoinFuture
import json
import stock

#初始化apikey，secretkey,url
apikey = '25b3b6dc-5834-4a9f-aaec-fce834c8db89'
secretkey = 'DBFB0BE60D46ECC3EC907AA8F786E513'
okcoinRESTURL = 'www.okcoin.cn'   #请求注意：国内账号需要 修改为 www.okcoin.cn

#现货API
okcoinSpot = OKCoinSpot(okcoinRESTURL,apikey,secretkey)


#print (u' 现货行情 ')
#print okcoinSpot.kline('btc_cny','1min',1000)

def fetchKline(symbol,type,size,sinceTime):
    data = okcoinSpot.kline(symbol,type,size,sinceTime)
    klines=[]
    for k in data:
        klines.append(stock.KLine(k))
    return klines;

def fetchTrade(symbol):
    data = okcoinSpot.trades()
    klines=[0]*len(data)
    count=0;
    for k in data:
        print k
        dd=stock.Trade(None,xdata=[k["price"],k["amount"],k["date_ms"]])
        if klines[count] == 0:
            klines[count] = stock.KLine(None,trade=dd)
        else:
            xline = klines[count]
            if xline.time == dd.ktime:
                xline.vol = xline.vol + dd.vol
                xline.close = dd.price
                if xline.close > xline.high:
                    xline.high = xline.close;
                if xline.close < xline.low:
                    xline.low = xline.close
            else:
                count = count + 1;
                klines[count] = stock.KLine(None,trade=dd)

    print klines[0:count]
    return klines[0:count]