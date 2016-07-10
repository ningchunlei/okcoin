#!/usr/bin/python
# -*- coding: utf-8 -*-
import Client
import talib
import numpy as np
import json
import time
import pandas

class KLine(object):

    def __init__(self,data):
        self.time = int(data[0])/1000
        self.open = float(data[1])
        self.high = float(data[2])
        self.low = float(data[3])
        self.close = float(data[4])
        self.vol = float(data[5])
        self.dif = 0
        self.dea = 0
        self.macd = 0
        self.k = 0;
        self.d = 0;
        self.j = 0;
        self.boll = 0;
        self.up = 0;
        self.dn = 0;

    def __str__(self):
        return "%s;close=%f;macd=%f;k=%f;j=%f,boll=%f," \
               "up=%f,dn=%f" %(time.ctime(self.time),self.close,self.macd,self.k,self.j,self.boll,self.up,self.dn)

    def __unicode__(self):
        return str(self)

    def __repr__(self):
        return str(self)

class Trade(object):

    def __init__(self,data):

        self.price = float(data[1])
        self.vol = float(data[2])
        tm = time.strftime("%y-%m-%d",time.localtime())+" "+data[3][0:-3]
        stime = time.strptime(tm,"%y-%m-%d %H:%M")
        self.time = time.mktime(stime)
        self.channel = data[4];

class TradePrice(object):

    def __init__(self,time):
        self.buy = 0;
        self.sell = 0;
        self.time = time;
        self.buyavg=0;
        self.sellavg=0;

    def update(self,trade):
        if trade.channel == "ask":
            self.sellavg = (self.sellavg * self.sell + trade.vol * trade.price)/(trade.vol + self.sell)
            self.sell += trade.vol
        elif trade.channel == "bid":
            self.buyavg = (self.buyavg * self.buy + trade.vol * trade.price)/(trade.vol + self.buy)
            self.buy += trade.vol


    def __str__(self):
        return "%s;b %f-s %f" % (time.ctime(self.time),self.buy,self.sell)

    def __repr__(self):
        return str(self)


class stock(object):
    OneMin = '1min'
    FiveMin = '5min'
    ThirtyMin = '30min'
    FourHour = '4hour'


    def __init__(self,symbol,stockType,maxLength):
        self._stockType=stockType;
        self._maxLength=maxLength
        self.stocks = [0]*2*maxLength;
        self.trades=[0]*2*maxLength;
        self._symbol = symbol;
        self.baseTime = None
        self.cursor = 0;
        if stockType == stock.OneMin:
            self._interval = 1*60
        elif stockType == stock.FiveMin:
            self._interval = 5*60
        elif stockType == stock.ThirtyMin:
            self._interval = 30*60
        elif stockType == stock.FourHour:
            self._interval = 240*60

    def on_kline(self,kline):
        if self.baseTime == None:
            self.fetchKLine()

        self.updateKLine(kline)
        #print self.cursor
        kd = self.stocks[self.cursor-20:self.cursor+1]
        kd.reverse()
        '''
        if kd[0]<0 and kd[0] > kd[1] :
            print "buy:"+str(kd[0].close)

        if kd[0]>0 and kd[0] < kd[1]:
            print "sell"+str(kd[0].close)
        '''
        #print kd
        #tp = self.trades[self.cursor-20:self.cursor+1]
        #tp.reverse()
        #print  tp

    def isUp(self):
        if self.stocks[self.cursor].j - self.stocks[self.cursor].k >0:
            return True
        else:
            return False

    def lastKline(self):
        return self.stocks[self.cursor]

    def on_trade(self,trade):
        if self.baseTime == None:
            return
        index = int((trade.time-self.baseTime)/self._interval)
        if self.trades[index] == 0:
            self.trades[index] = TradePrice(trade.time);
        self.trades[index].update(trade)
        tp = self.trades[self.cursor-20:self.cursor+1]
        tp.reverse()
        print  tp

    def fetchKLine(self):
        klines = Client.fetchKline(self._symbol,self._stockType,self._maxLength,None)
        self.stocks=[0]*2*self._maxLength
        self.stocks[0:len(klines)]=klines
        self.trades=[0]*2*self._maxLength
        self.baseTime = klines[0].time
        self.macd(len(klines)-1,len(klines))


    def updateKLine(self,kline):
        if (kline.time-self.baseTime)/self._interval >= len(self.stocks):
            self.baseTime = None;
            self.on_kline(kline)

        self.cursor = (kline.time-self.baseTime)/self._interval
        self.stocks[self.cursor] = kline;
        self.macd(self.cursor,60)
        self.kdj(self.cursor-300,self.cursor+1)
        self.boll(self.cursor-300,self.cursor+1)

    def canBuy(self):
        direction = self.stocks[self.cursor-1].j - self.stocks[self.cursor-1].k
        direction2 = self.stocks[self.cursor-2].j - self.stocks[self.cursor-2].k

        flagBuy=False

        print "%s-%s" % (direction,direction2)

        if direction>0 and direction2<=0:
            flagBuy = True
        elif direction<0 and direction2>=0:
            flagBuy = False
        else:
            flagBuy = None

        flag = False
        for i in range(1,6):
            if int(self.stocks[self.cursor-i].low) <= int(self.stocks[self.cursor-i].dn):
                flag = True

        return flagBuy,flag

    def kdj(self,start,stop):
        close=[]
        high =[]
        low =[]
        for i in range(start,stop):
            close.append(self.stocks[i].close)
            high.append(self.stocks[i].high)
            low.append(self.stocks[i].low)

        lowest = pandas.rolling_min(pandas.Series(low),9)
        highest = pandas.rolling_max(pandas.Series(high),9)
        closedp = pandas.Series(close)

        rsv = ((closedp-lowest)/(highest - lowest))*100
        rsv[0]=50

        k = pandas.ewma(rsv,com=2,adjust=False)
        k[0] = 50
        d = pandas.ewma(k,com=2,adjust=False)
        j = 3 * k - 2 * d

        for i in range(start,stop):
            self.stocks[i].k = k[i-start]
            self.stocks[i].d = d[i-start]
            self.stocks[i].j = j[i-start]

    def boll(self,start,stop):
        close=[]
        for i in range(start,stop):
            close.append(self.stocks[i].close)

        closepd = pandas.Series(close)
        ma = pandas.rolling_sum(closepd,20)/20
        md = pandas.rolling_std(closepd,20)
        up = ma + 2*md
        dn = ma - 2*md

        for i in range(start,stop):
            self.stocks[i].boll = ma[i-start]
            self.stocks[i].up = up[i-start]
            self.stocks[i].dn = dn[i-start]


    def macd(self,start,length):
        close =[]
        for i in range(length):
            close.append(self.stocks[start-i].close)
        close.reverse()
        DIF, DEA, MACD = talib.MACD(np.array(close), fastperiod=12, slowperiod=26, signalperiod=9)
        '''
        tmp = []
        for i in range(10):
            if(MACD[-1]<0):
                close[-1]=close[-1]+0.2;
            else:
                close[-1]=close[-1] -0.2;

            xDIF, xDEA, xMACD = talib.MACD(np.array(close), fastperiod=12, slowperiod=26, signalperiod=9)
            tmp.append((close[-1],xMACD[-1]))
            if(xMACD[-1]<0 and MACD[-1]>0) :
                print (close[-1],xMACD[-1])
            elif(xMACD[-1]>0 and MACD[-1]<0):
                print  (close[-1],xMACD[-1])

        #print tmp;
        '''
        for i in range(length):
            self.stocks[start-i].dif=DIF[length-i-1]
            self.stocks[start-i].dea = DEA[length-i-1]
            self.stocks[start-i].macd = MACD[length-i-1]*2


