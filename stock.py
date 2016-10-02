#!/usr/bin/python
# -*- coding: utf-8 -*-
import Client
import talib
import numpy as np
import json
import time
from datetime import datetime,timedelta
import pandas
import logging

class KLine(object):

    def __init__(self,data,trade=None):
        if trade == None:
            self.time = int(data[0])/1000
            self.open = float(data[1])
            self.high = float(data[2])
            self.low = float(data[3])
            self.close = float(data[4])
            self.vol = float(data[5])
        elif trade == "kline":
            self.time = time.mktime(datetime.strptime(data[4].strip("\r\n"),"%y-%m-%d %H:%M").timetuple())
            self.open = float(data[1])
            self.high = float(data[2])
            self.low = float(data[3])
            self.close = float(data[0])
            self.vol = 0
        elif trade == "copy":
            self.open = data.open
            self.high = data.high
            self.low = data.low
            self.close = data.close
            self.vol = 0
        else:
            self.time = trade.ktime
            self.vol = trade.vol
            self.open = trade.price
            self.high = trade.price
            self.low = trade.price
            self.close = trade.price
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
        return "%s;close=%f;high=%f;low=%s;vol=%s;macd=%f;k=%f;j=%f,boll=%f," \
               "up=%f,dn=%f" %(time.ctime(self.time),self.close,self.high,self.low,self.vol,self.macd,self.k,self.j,self.boll,self.up,self.dn)

    def __unicode__(self):
        return str(self)

    def __repr__(self):
        return str(self)

class Trade(object):

    def __init__(self,data,xdata=None):
        if xdata==None:
            self.price = float(data[1])
            self.vol = float(data[2])
        else:
            self.price = float(xdata[0])
            self.vol = float(xdata[1])
        stime = None
        if xdata==None:
            tm = time.strftime("%y-%m-%d",time.localtime())+" "+data[3]
            stime = datetime.strptime(tm,"%y-%m-%d %H:%M:%S")
            ltime = datetime.now();
            if ltime.hour==24 and stime.hour==0:
                stime = stime + timedelta(days=1)
        else:
            stime = datetime.fromtimestamp(xdata[2]/1000)
        self.time = time.mktime(stime.timetuple())

        if stime.second<15:
            stime = stime.replace(second=0)
        elif stime.second<30:
            stime = stime.replace(second=15)
        elif stime.second<45:
            stime = stime.replace(second=30)
        elif stime.second<=60:
            stime = stime.replace(second=45)

        self.ktime = time.mktime(stime.timetuple())
        if xdata==None:
            self.channel = data[4];
    def __str__(self):
        return "time=%s;price=%s;vol=%s,channel=%s" % (time.ctime(self.time),self.price,self.vol,self.channel)
    def __repr__(self):
        return str(self)


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
    FifteenMin = '15min'
    ThirtyMin = '30min'
    FourHour = '4hour'
    FifteenSec = '15sec'


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
        elif stockType == stock.FifteenMin:
            self._interval = 15*60
        elif stockType == stock.ThirtyMin:
            self._interval = 30*60
        elif stockType == stock.FourHour:
            self._interval = 240*60
        elif stockType == stock.FifteenSec:
            self._interval = 15

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

    def tkine(self,trade):

        if self.baseTime==None or int((trade.time-self.baseTime)/self._interval) >= len(self.stocks):
            self.stocks = self.stocks[500:]
            self.stocks.extend([0]*500)
            if self.stocks[0] == 0 :
                self.baseTime = trade.ktime
            else:
                self.baseTime = self.stocks[0].time


        self.cursor = int((trade.ktime-self.baseTime)/self._interval)
        if self.stocks[self.cursor]==None or self.stocks[self.cursor]==0:
            kline = KLine(None,trade=trade)
            self.stocks[self.cursor] = kline
        else:
            kline = self.stocks[self.cursor]
            kline.vol = kline.vol + trade.vol
            kline.close=trade.price
            if kline.close > kline.high:
                kline.high = kline.close;
            if kline.close < kline.low:
                kline.low = kline.close

        if self.cursor > 30:
            self.kdj(self.cursor-30,self.cursor+1)
            self.boll(self.cursor-30,self.cursor+1)

    def isUp(self):
        if self.stocks[self.cursor].j - self.stocks[self.cursor].k >0:
            return True
        else:
            return False

    def lastKline(self):
        return self.stocks[self.cursor]

    def preLastKline(self):
        return self.stocks[self.cursor-1]

    def pre2LastKline(self):
        return self.stocks[self.cursor-2]

    def preMyLastKline(self,count):
        return self.stocks[self.cursor-count]

    def findLowestkdj(self):
        kline = False
        count=0
        xcount=0
        while True:
            if self.stocks[self.cursor-count].j <20 :
                kline = True
                break
            if xcount>=2:
                kline = False
                break;
            if self.stocks[self.cursor-count].high >= self.stocks[self.cursor-count].up:
                kline = False
                break
            if self.stocks[self.cursor-count].j < self.stocks[self.cursor-count-1].j:
                xcount += 1;

            if self.stocks[self.cursor-count].j > self.stocks[self.cursor-count-1].j:
                xcount = 0;
            count+=1
        return kline

    def on_trade(self,trade):
        if self.baseTime == None:
            return
        index = int((trade.time-self.baseTime)/self._interval)
        if self.trades[index] == 0:
            self.trades[index] = TradePrice(trade.time);
        self.trades[index].update(trade)
        logging.info(trade)

    def fetchKLine(self):
        klines = Client.fetchKline(self._symbol,self._stockType,self._maxLength,None)
        self.stocks=[0]*2*self._maxLength
        self.stocks[0:len(klines)]=klines
        self.trades=[0]*2*self._maxLength
        self.baseTime = klines[0].time
        self.macd(len(klines)-1,len(klines))

    def fetchTradeLine(self):
        klines = Client.fetchTrade(self._symbol)
        self.stocks=[0]*2*self._maxLength
        self.stocks[0:len(klines)]=klines
        self.trades=[0]*2*self._maxLength
        self.baseTime = klines[0].time
        self.macd(len(klines)-1,len(klines))

    def updateKLine(self,kline):
        if (kline.time-self.baseTime)/self._interval >= len(self.stocks):
            self.baseTime = None;
            self.on_kline(kline)
        self.cursor = int((kline.time-self.baseTime)/self._interval)
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

    def touchDown(self):
        flag = False
        for i in range(1,6):
            if int(self.stocks[self.cursor-i].low) <= int(self.stocks[self.cursor-i].dn):
                flag = True

        return flag

    def touchDownRange(self,start,end):
        flag = False
        for i in range(start,end):
            if int(self.stocks[self.cursor-i].low) <= int(self.stocks[self.cursor-i].dn):
                flag = True

        return flag

    def countBigmacd(self):
        count=0
        while True:
            if self.stocks[self.cursor-count].macd<=0:
                break
            count+=1

        return count;


    def downToUp(self):
        flag = False
        count=0
        while True:
            if self.stocks[self.cursor-count].low <=  self.stocks[self.cursor-count].dn:
                flag=True
                break
            if self.stocks[self.cursor-count].high >= self.stocks[self.cursor-count].up:
                flag = False
                break
            count+=1

        return flag

    def findDownKline(self):
        kline = None
        count=0
        while True:
            if self.stocks[self.cursor-count].low <=  self.stocks[self.cursor-count].dn:
                kline=self.stocks[self.cursor-count];
                break
            if self.stocks[self.cursor-count].high >= self.stocks[self.cursor-count].up:
                kline = None
                break
            count+=1

        return kline

    def findLastKDJCrossKlineCount(self,start):
        count=start
        while True:
            if self.stocks[self.cursor-count].j-self.stocks[self.cursor-count].k>0:
                break
            count+=1
        return count

    def findKDJKlineDown(self):
        flag = False
        count=0
        while True:
            if self.stocks[self.cursor-count].j - self.stocks[self.cursor-count].k>=0:
                break
            count+=1
            if self.stocks[self.cursor-count].j > self.stocks[self.cursor-count-1].j:
                flag = True
                break;

        return flag


    def findKDJKline(self):
        kline = None
        count=1
        while True:
            if self.stocks[self.cursor-count].j - self.stocks[self.cursor-count].k<0:
                kline=self.stocks[self.cursor-count];
                break
            count+=1

        return kline

    def findIsKdjUp80(self,indexTime):
        flag = 0
        count=1
        while True:
            if self.stocks[self.cursor-count].time <=  indexTime:
                break
            if self.stocks[self.cursor-count].j>80:
                flag += 1
            count += 1

        return flag


    def findUpKline(self):
        kline = None
        count=0
        while True:
            if self.stocks[self.cursor-count].low <=  self.stocks[self.cursor-count].dn:
                kline = None
                break
            if self.stocks[self.cursor-count].high >= self.stocks[self.cursor-count].up:
                kline=self.stocks[self.cursor-count];
                break
            count+=1

        return kline

    def upmiddle(self,indexTime):
        flag = 0
        count=0
        while True:
            if self.stocks[self.cursor-count].time <=  indexTime:
                break
            if self.stocks[self.cursor-count].high > self.stocks[self.cursor-count].boll:
                flag += 1
            count += 1

        if flag>=1:
            return True
        return False

    def downmiddle(self,indexTime):
        flag = 0
        count=0
        while True:
            if self.stocks[self.cursor-count].time <=  indexTime:
                break
            if self.stocks[self.cursor-count].low < self.stocks[self.cursor-count].boll:
                flag += 1
            count += 1

        if flag>=1:
            return True
        return False

    def kdjUp(self,indexTime):
        flag = 0
        count=1
        while True:
            if self.stocks[self.cursor-count].time <=  indexTime:
                break
            if self.stocks[self.cursor-count].j-self.stocks[self.cursor-count].k > 0 and self.stocks[self.cursor-count-1].j-self.stocks[self.cursor-count-1].k <= 0:
                flag += 1
            count += 1

        if flag==1:
            return True
        return False

    def countTouchUp(self,indexTime):
        findex = 0
        count=1
        ha = {}
        while True:
            if self.stocks[self.cursor-count].time <= indexTime:
                break
            if self.stocks[self.cursor-count].high >self.stocks[self.cursor-count].up and ha.has_key(findex)==False:
                ha[findex] = 1
            if self.stocks[self.cursor-count].j-self.stocks[self.cursor-count].k > 0 and self.stocks[self.cursor-count-1].j-self.stocks[self.cursor-count-1].k <= 0:
                findex += 1
            count += 1
        return len(ha)

    def countCross(self,indexTime):
        findex = 0
        count=1
        print indexTime
        while True:
            if self.stocks[self.cursor-count].time <= indexTime:
                break
            if self.stocks[self.cursor-count].j-self.stocks[self.cursor-count].k > 0 and self.stocks[self.cursor-count-1].j-self.stocks[self.cursor-count-1].k <= 0:
                findex += 1
            count += 1
        return findex

    def countCross2(self,indexTime):
        findex = 0
        count=1
        while True:
            if self.stocks[self.cursor-count].time <= indexTime:
                break
            if self.stocks[self.cursor-count].j-self.stocks[self.cursor-count].k < 0 and self.stocks[self.cursor-count-1].j-self.stocks[self.cursor-count-1].k >= 0:
                findex += 1
            count += 1
        return findex

    def countCrossDiff(self,indexTime,fcount):
        findex = 0
        count=fcount
        while True:
            if self.stocks[self.cursor-count].time <=  indexTime:
                break
            if self.stocks[self.cursor-count].j-self.stocks[self.cursor-count].k > 0 and self.stocks[self.cursor-count-1].j-self.stocks[self.cursor-count-1].k <= 0:
                findex += 1
            count += 1
        return findex

    def kdjUpDontTouchMax(self,indexTime):
        maxc = 0
        count=1
        while True:
            if self.stocks[self.cursor-count].time <= indexTime:
                break
            if self.stocks[self.cursor-count].j-self.stocks[self.cursor-count].k > maxc:
                maxc = self.stocks[self.cursor-count].j-self.stocks[self.cursor-count].k
            count += 1

        if maxc-3>self.stocks[self.cursor].j-self.stocks[self.cursor].k:
            return False
        return True

    def kdjUpDontTouchMaxKline(self):
        maxc = 0
        count=1
        kline = None
        while True:
            if self.stocks[self.cursor-count].j - self.stocks[self.cursor-count].k <=0:
                break
            if self.stocks[self.cursor-count].j> maxc:
                maxc = self.stocks[self.cursor-count].j
                kline = self.stocks[self.cursor-count];
            count += 1
        return kline

    def mayDown(self,indexTime):
        flag = False
        count=1
        while True:
            if self.stocks[self.cursor-count].time <= indexTime:
                break
            if self.stocks[self.cursor-count].j-self.stocks[self.cursor-count].k < self.stocks[self.cursor-count-1].j-self.stocks[self.cursor-count-1].k:
                flag = True
            count += 1
        return flag

    def touchShortDown(self):
        flag = False
        for i in range(1,3):
            if int(self.stocks[self.cursor-i].low) <= int(self.stocks[self.cursor-i].dn):
                flag = True
        return flag

    def touchSimlarDown(self,end):
        flag = False
        for i in range(1,end):
            if i!=1 and self.stocks[self.cursor-i].low-0.5 <= self.stocks[self.cursor-i].dn and self.stocks[self.cursor-i+1].close>self.stocks[self.cursor-i].close:
                flag = True
        return flag

    def middleUp(self):
        flag = False
        if self.stocks[self.cursor].close <= self.stocks[self.cursor].boll:
            flag = True
        return flag

    def middleUpByIndex(self,index):
        flag = False
        if self.stocks[self.cursor-index].close >= self.stocks[self.cursor-index].boll:
            flag = True
        return flag

    def premiddleDown(self):
        flag = False
        if self.stocks[self.cursor-1].close < self.stocks[self.cursor-1].boll and self.stocks[self.cursor-1].close < self.stocks[self.cursor-1].open:
            flag = True
        return flag

    def touchMiddle(self):
        flag = False
        if self.stocks[self.cursor].close < self.stocks[self.cursor].boll:
            flag = True
        return flag

    def touchMiddleLong(self):
        flag = False
        for i in range(1,4):
            if self.stocks[self.cursor-i].close < self.stocks[self.cursor-i].boll:
                flag = True
        return flag

    def touchMyMiddelByLow(self,start,end):
        flag = False
        for i in range(start,end):
            if self.stocks[self.cursor-i].low < self.stocks[self.cursor-i].boll:
                flag = True
        return flag

    def touchMiddleToLowRange(self):
        flag = True
        for i in range(0,2):
            if not (self.stocks[self.cursor-i].open < self.stocks[self.cursor-i].boll and self.stocks[self.cursor-i].close < self.stocks[self.cursor-i].boll):
                flag=False
        return flag

    def touchHighBetweenMiddleRange(self):
        count=1
        while True:
            if self.stocks[self.cursor-count].j-self.stocks[self.cursor-count].k>0:
                break;
            if self.stocks[self.cursor-count].high>self.stocks[self.cursor-count].up:
                break;
            count += 1
        if count>=3:
            return True
        return False




    def touchUp(self):
        flag = False
        for i in range(1,6):
            if int(self.stocks[self.cursor-i].high) >= int(self.stocks[self.cursor-i].up):
                flag = True

        return flag

    def touchUpShort(self):
        flag = False
        for i in range(1,3):
            if int(self.stocks[self.cursor-i].high) >= int(self.stocks[self.cursor-i].up):
                flag = True

        return flag

    def touchUpMyShort(self):
        flag = False
        for i in range(0,3):
            if int(self.stocks[self.cursor-i].high) >= int(self.stocks[self.cursor-i].up):
                flag = True

        return flag

    def touchUpSell(self):
        pk = self.stocks[self.cursor-1].high - self.stocks[self.cursor-1].up
        pk2 = self.stocks[self.cursor-2].high - self.stocks[self.cursor-2].up
        kdjdiff = self.stocks[self.cursor-1].j - self.stocks[self.cursor-1].k
        kdj2diff = self.stocks[self.cursor-2].j - self.stocks[self.cursor-2].k
        if pk>0 and kdjdiff<=0:
            return True
        if pk<0 and pk2>=0 and kdjdiff < kdj2diff:
            return True
        return False

    def touchMiddleSell(self):
        pk = self.stocks[self.cursor-1].high - self.stocks[self.cursor-1].boll
        pk2 = self.stocks[self.cursor-2].high - self.stocks[self.cursor-2].boll
        kdjdiff = self.stocks[self.cursor-1].j - self.stocks[self.cursor-1].k
        kdj2diff = self.stocks[self.cursor-2].j - self.stocks[self.cursor-2].k
        if pk>0 and kdjdiff<=0:
            return True
        if pk<0 and pk2>=0 and kdjdiff < kdj2diff:
            return True



    def touchUpMy(self):
        flag = False
        if int(self.stocks[self.cursor].high) >= int(self.stocks[self.cursor].up):
            flag = True
        return flag

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

    def lowhighprice(self,start,stop):
        close=[]
        high =[]
        low =[]
        for i in range(start,stop):
            close.append(self.stocks[i].close)
            high.append(self.stocks[i].high)
            low.append(self.stocks[i].low)

        lowest = pandas.rolling_min(pandas.Series(low),9)
        highest = pandas.rolling_max(pandas.Series(high),9)
        return lowest[len(lowest)-1],highest[len(highest)-1]

    '''
        return 当前K线的支撑价,转换价,下个K线同趋势的价位的预测
    '''
    def forecastClose(self):
        pre = self.stocks[self.cursor-1]
        last = self.stocks[self.cursor]
        lowest,highest = self.lowhighprice(self.cursor-30,self.cursor+1)

        diff = pre.j - pre.k
        currentzhicheng = (9*diff - 8*pre.k+12 * pre.d)*(highest-lowest)/400.0 + lowest

        diff = 0
        fanzhuanprice = (9*diff - 8*pre.k+12 * pre.d)*(highest-lowest)/400.0 + lowest

        diff = last.j - last.k
        nextprice = (9*diff - 8*last.k+12 * last.d)*(highest-lowest)/400.0 + lowest

        return currentzhicheng,fanzhuanprice,nextprice

    def forecastMacd(self):
        close=[]
        start = self.cursor-300
        stop = self.cursor
        for i in range(start,stop):
            close.append(self.stocks[i].close)
        closedp = pandas.Series(close)

        closedp[0]=0
        e12 = pandas.ewma(closedp,com=11/2,adjust=False)
        e26 = pandas.ewma(closedp,com=25/2,adjust=False)

        dif = e12 - e26
        dea = pandas.ewma(dif,com=4,adjust=False)

        def cx(x):
            (x*5*13*27-e12[-1]*11*27*8+e26[-1]*25*13*8+dea[-1]*8*13*27)/822

        return cx(self.stocks[self.cursor-1].macd),cx(0)

    def forecastKDJ(self):
        last = self.stocks[self.cursor]
        lowest,highest = self.lowhighprice(self.cursor-30,self.cursor+1)

        rsv = ((last.close-lowest)/(highest - lowest))*100
        k = 2/3.0*last.k + 1/3.0*rsv
        d  = 2/3.0*last.d + 1/3.0*k
        j = 3*k -2*d
        diff = j - k;
        if diff > last.j- last.k :
            return True;
        else:
            return False


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


