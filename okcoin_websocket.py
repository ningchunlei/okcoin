# -*- coding:utf-8 -*-
import websocket
import time
import sys
import json
import hashlib
import zlib
import base64
import threading
from datetime import datetime
from stock import stock,KLine,Trade
import logging
import ply

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S'
                    )
pricelogging = logging.getLogger("price")
pricelogging.addHandler(logging.FileHandler("price.log"))

tradelogging = logging.getLogger("trade")
tradelogging.addHandler(logging.FileHandler("trade.log"))



api_key='25b3b6dc-5834-4a9f-aaec-fce834c8db89'
secret_key = "DBFB0BE60D46ECC3EC907AA8F786E513"

last_time=0;
ws=None
tradeIndex={}
tradeLastTime = None
bidsList=[]
asksList=[]


stock1Min = stock("btc_cny",stock.OneMin,500)
stock5Min = stock("btc_cny",stock.FiveMin,500)
stock15Sec = stock("btc_cny",stock.FifteenSec,500)
stock15Min = stock("btc_cny",stock.FifteenMin,500)

buyPrice = None
buyPrice1 = None
buyPrice2 = None
buy1Time = None
buy2Time = None
buyTriggerTime = None
buyPrice3=None
downToUp = None
upToDown = None
middleToUp = None
spec =None
xspec = None
sellSpec = None
xbuy = None
xkdj = None
up15 = None
up5 = None
kk1pos = None
kk5pos = None
kk15pos = None
m5data=None
lastbuyTime=None
fenx1 = None
fenx5 = None
buttomDown = None
buttomDownKline = None


up5Copy = None
buyTriggerTimeCopy = None
specCopy = None


#business
def buildMySign(params,secretKey):
    sign = ''
    for key in sorted(params.keys()):
        sign += key + '=' + str(params[key]) +'&'
    return  hashlib.md5((sign+'secret_key='+secretKey).encode("utf-8")).hexdigest().upper()

def on_open(self):
    #subscribe okcoin.com spot ticker
    #self.send("{'event':'addChannel','channel':'ok_sub_spotcny_btc_ticker','binary':'true'}")
    self.send("{'event':'addChannel','channel':'ok_sub_spotcny_btc_trades','binary':'true'}")
    self.send("{'event':'addChannel','channel':'ok_sub_spotcny_btc_depth_60','binary':'true'}")
    stock1Min = stock("btc_cny",stock.OneMin,500)
    stock5Min = stock("btc_cny",stock.FiveMin,500)
    stock15Sec = stock("btc_cny",stock.FifteenSec,500)
    stock15Min = stock("btc_cny",stock.FifteenMin,500)

    self.send("{'event':'addChannel','channel':'ok_sub_spotcny_btc_kline_1min','binary':'true'}")
    self.send("{'event':'addChannel','channel':'ok_sub_spotcny_btc_kline_5min','binary':'true'}")
    #self.send("{'event':'addChannel','channel':'ok_sub_spotcny_btc_kline_15min','binary':'true'}")


def go():
    global buyPrice1,buyPrice2,bidsList,asksList,buy1Time,buy2Time,buyTriggerTime,buyPrice3,downToUp,upToDown,middleToUp,spec,xspec,sellSpec,xbuy,xkdj,up15
    m5up,m5down,m5next = stock5Min.forecastClose()
    m1up,m1down,m1next = stock1Min.forecastClose()
    lastM5 = stock5Min.lastKline()
    prelastM5 = stock5Min.preLastKline()
    pre2lastM5 = stock5Min.pre2LastKline()
    current = stock1Min.lastKline()
    lastm1 = stock1Min.preLastKline()
    prelastm1 = stock1Min.pre2LastKline()
    lastM15 = stock15Min.lastKline()

    lastM15 = stock15Min.lastKline()
    prelastM15 = stock15Min.preLastKline()
    pre2lastM15 = stock15Min.pre2LastKline()

    #if len(bidsList)<=1:
    #    return

    #m1upSellSupport = findTotalSupportWithAsks(m1up,asksList[0])
    #m1upBuySupport = findTotalSupportWithBids(m1up,bidsList[0])

    #m5upSellSupport = findTotalSupportWithAsks(m5up,asksList[0])
    #m5upBuySupport = findTotalSupportWithBids(m5up,bidsList[0])

    if current.time-lastM5.time>=5*60:
        return

    #pricelogging.info("time=%s,msup=%s,ssup=%s,price=%s,M5 up=%s,down=%s,next=%s,%s,boll=%s,m5close=%s" % (time.ctime(current.time),m5upBuySupport,m5upSellSupport,current.close,m5up,m5down,m5next,stock5Min.forecastKDJ(),lastM5.boll,lastM5.close))
    #pricelogging.info("time=%s,msup=%s,ssup=%s,price=%s,M1 up=%s,down=%s,next=%s,%s" % (time.ctime(current.time),m1upBuySupport,m1upSellSupport,current.close,m1up,m1down,m1next,stock1Min.forecastKDJ()))

    pricelogging.info("time=%s,price=%s,touchShortDown=%s,buyprice=%s,1jkd=%s,pre1kdj=%s,buy1time=%s,cukdj=%s" % (time.ctime(current.time),current.close,stock1Min.touchShortDown(),buyPrice1,lastm1.j-lastm1.k,prelastm1.j-prelastm1.k,buy1Time,current.j-current.k))


    prelast5diff = prelastM5.j-prelastM5.k
    pre2last5diff = pre2lastM5.j - pre2lastM5.k

    prelast1diff = lastm1.j-lastm1.k
    pre2last1diff = prelastm1.j - prelastm1.k

    prelast15diff = prelastM15.j - prelastM15.k
    pre2last15diff = pre2lastM15.j - pre2lastM15.k

    pricelogging.info("spec=%s,5down=%s,pre2kdj=%s,prekdj=%s,curkdj=%s,up15=%s" % (spec,stock5Min.touchDownRange(0,4),pre2last5diff,prelast5diff,lastM5.j-lastM5.k,up15))

    pricelogging.info("15downToUP=%s,kline=%s,prelast=%s,pre2last=%s" % (stock15Min.downToUp(),stock15Min.findDownKline(),prelast15diff,pre2last15diff))

    if up15 == None and stock15Min.downToUp() and stock15Min.findDownKline()!=None and stock15Min.countCross(stock15Min.findDownKline().time)<=1:
        if pre2last15diff>0 and prelast15diff>0 and prelast15diff > pre2last15diff:
            up15 = True

    if stock15Min.downToUp()==False or prelast15diff<0:
        up15 = None

    if spec == None:
        '''
        if buy1Time==None and stock5Min.touchDownRange(0,4)==True \
                                and pre2last5diff<-5 and prelast5diff>0 and prelastM5.close > pre2lastM5.close and prelast5diff>pre2last5diff:
            buy1Time = current.time
            buy2Time = lastM5.time
            xkdj = prelast1diff
            xbuy="11"
            spec = 1
            pricelogging.info("xbuy11-%s,%s,time=%s,b2time=%s" % (xbuy,stock1Min.lastKline().close,time.ctime(buy1Time),time.ctime(buy2Time)))
        '''

        if buy1Time==None and stock5Min.touchDownRange(0,4)==True \
                and pre2last5diff>0 and prelast5diff>0 and prelastM5.close > pre2lastM5.close and prelast5diff>pre2last5diff:
            buy1Time = current.time
            buy2Time = lastM5.time
            xkdj = prelast1diff
            xbuy="12"
            spec = 1
            pricelogging.info("xbuy12-%s,%s,time=%s,b2time=%s" % (xbuy,stock1Min.lastKline().close,time.ctime(buy1Time),time.ctime(buy2Time)))

        #touch down to up
        if buy1Time==None and stock5Min.touchDownRange(0,4)==True and \
                                stock5Min.preMyLastKline(3).j- stock5Min.preMyLastKline(3).k < 0 and pre2last5diff<-5 and prelast5diff>-5 and prelastM5.close > pre2lastM5.close and  prelast5diff>pre2last5diff:
            buy1Time = current.time
            buy2Time = lastM5.time
            xkdj = prelast1diff
            xbuy="1"
            spec = 1
            pricelogging.info("xbuy1-%s,%s,time=%s,b2time=%s" % (xbuy,stock1Min.lastKline().close,time.ctime(buy1Time),time.ctime(buy2Time)))



        if up15==True and pre2last5diff<0 and prelast5diff>pre2last5diff:
            buy1Time = current.time
            buy2Time = lastM5.time
            xkdj = prelast1diff
            xbuy="51"
            spec = 1
            pricelogging.info("xbuy51-%s,%s,time=%s,b2time=%s" % (xbuy,stock1Min.lastKline().close,time.ctime(buy1Time),time.ctime(buy2Time)))


        if buy1Time==None and stock5Min.downToUp()==False and \
                                stock5Min.preMyLastKline(3).j- stock5Min.preMyLastKline(3).k < 0 and pre2last5diff<-5 and prelast5diff>-5 and prelastM5.close > pre2lastM5.close and  prelast5diff>pre2last5diff:
            buy1Time = current.time
            buy2Time = lastM5.time
            xkdj = prelast1diff
            xbuy="81"
            spec = 1
            pricelogging.info("xbuy81-%s,%s,time=%s,b2time=%s" % (xbuy,stock1Min.lastKline().close,time.ctime(buy1Time),time.ctime(buy2Time)))



    if buy2Time!=None and lastM5.time - buy2Time == 5*60 and (prelast5diff<pre2last5diff or prelast5diff<0):
        if buyPrice1 > current.close:
            return
        if buyPrice1!=None:
            pricelogging.info("tbuy4-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))

        pricelogging.info("disable-%s-%s,time=%s,deciderTime=%s" % (xbuy,stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time)))
        buy1Time = None
        buy2Time = None
        xbuy=None
        buyPrice1 = None
        xkdj = None
        spec = None

    if buy2Time!=None and stock5Min.countCross(buy2Time)>=2:
        if buyPrice1 > current.close:
            return
        if buyPrice1!=None:
            pricelogging.info("tbuy43-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))

        pricelogging.info("disable43-%s-%s,time=%s,deciderTime=%s" % (xbuy,stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time)))
        buy1Time = None
        buy2Time = None
        xbuy=None
        buyPrice1 = None
        xkdj = None
        spec = None


    if buy1Time!=None and buyPrice1==None and xbuy!=None and spec==1:
        if stock1Min.downToUp() and xkdj<0:
            if (pre2last1diff<0 and prelast1diff>0) or (pre2last1diff>=0 and prelast1diff>pre2last1diff):
                pricelogging.info("tbuy12-%s,time=%s,deciderTime=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time)))
                buyPrice1 = current.close
                xkdj = None
                spec = 2
            return

        if stock1Min.downToUp() and stock1Min.countCross(buy1Time)==0 and stock1Min.kdjUpDontTouchMax(buy1Time) and lastM5.j-lastM5.k>prelast5diff:
            pricelogging.info("tbuy10-%s,time=%s,deciderTime=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time)))
            buyPrice1 = current.close
            xkdj = None
            spec = 2
            return

        if stock1Min.downToUp() and stock1Min.kdjUp(buy1Time) and stock1Min.kdjUpDontTouchMax(buy1Time) and lastM5.j-lastM5.k>prelast5diff:
            pricelogging.info("tbuy1-%s,time=%s,deciderTime=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time)))
            buyPrice1 = current.close
            xkdj = None
            spec = 2
            return
        if stock1Min.downToUp()==False and prelast1diff<0 and current.close<current.boll and lastM5.j-lastM5.k>prelast5diff:
            pricelogging.info("tbuy2-%s,time=%s,deciderTime=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time)))
            buyPrice1 = current.close
            xkdj = None
            spec = 2
            return

        if stock1Min.downToUp()==False and pre2last1diff<0 and prelast1diff>pre2last1diff and current.close>current.boll and lastM5.j-lastM5.k>prelast5diff:
            pricelogging.info("tbuy21-%s,time=%s,deciderTime=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time)))
            buyPrice1 = current.close
            xkdj = None
            spec = 2
            return

        if stock1Min.downToUp() and stock1Min.kdjUp(buy1Time) and stock1Min.kdjUpDontTouchMax(buy1Time)==False and prelast1diff>pre2last1diff and lastM5.j-lastM5.k>prelast5diff:
            pricelogging.info("tbuy3-%s,time=%s,deciderTime=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time)))
            buyPrice1 = current.close
            xkdj = None
            spec = 2
            return



    if buy2Time!=None and  lastM5.time - buy2Time > 5*60 and lastM5.j-lastM5.k<=0:
        if buyPrice1 > current.close:
            return
        if buyPrice1!=None:
            pricelogging.info("tbuy5-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
        pricelogging.info("disable2-%s-%s,time=%s,deciderTime=%s" % (xbuy,stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time)))
        buy1Time = None
        buy2Time = None
        xbuy=None
        buyPrice1 = None
        xkdj = None
        spec=None


    if buyPrice1!=None and spec==2 and (current.time-buy2Time<=4*60 and current.time-buy2Time>2*60) and stock1Min.touchDown() and current.j-current.k<prelast1diff:
        pricelogging.info("tbuy61-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
        buy1Time = None
        buy2Time = None
        xbuy=None
        buyPrice1 = None
        xkdj = None
        spec=None

    if buyPrice1!=None and spec==2 and ((stock1Min.countTouchUp(buy1Time)>=1 and stock1Min.countCross(buy1Time)>2) or stock1Min.countTouchUp(buy1Time)==1)and stock1Min.touchUpSell():
        if stock1Min.lastKline().close > buyPrice1:
            pricelogging.info("tbuy6-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buy1Time = None
            xbuy=None
            buyPrice1 = None
            xkdj = None
            spec = 3


    if buyPrice1!=None and spec==3 and prelast1diff < pre2last1diff and stock1Min.touchUpMyShort():
        if stock1Min.lastKline().close > buyPrice1:
            pricelogging.info("tbuy7-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buy1Time = None
            xbuy=None
            buyPrice1 = None
            xkdj = None

    if buyPrice1==None and spec==3 and buy2Time!=None and prelast1diff > pre2last1diff and  pre2last1diff<0 and prelast1diff>0 and prelast5diff>0 and lastM5.j-lastM5.k>10 and current.close > current.open:
        pricelogging.info("tbuy8-%s,time=%s,deciderTime=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time)))
        buyPrice1=current.close
        buy1Time = current.time

    '''
    if buyPrice1==None and prelast5diff<0 and pre2last5diff<0 and  prelast5diff>pre2last5diff and prelast5diff>-5 and stock5Min.touchShortDown() \
        and stock1Min.touchDown() and stock1Min.downToUp():
        if pre2last1diff<0 and prelast1diff>=0 :
            pricelogging.info("tbuy-%s,time=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = current.close
            buy1Time = current.time
            spec = True
        if pre2last1diff>=0 and prelast1diff > pre2last1diff:
            pricelogging.info("tbuy1-%s,time=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = current.close
            buy1Time = current.time
            spec = True

    if buyPrice1==None and prelast5diff<0 and pre2last5diff<0 and  prelast5diff>pre2last5diff and prelast5diff>-5 and stock5Min.touchSimlarDown(4) \
            and stock1Min.touchDown() and stock1Min.downToUp():
        if pre2last1diff<0 and prelast1diff>=0 :
            pricelogging.info("tbuy21-%s,time=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = current.close
            buy1Time = current.time
            spec = True
        if pre2last1diff>=0 and prelast1diff > pre2last1diff:
            pricelogging.info("tbuy22-%s,time=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = current.close
            buy1Time = current.time
            spec = True


    if buyPrice1!=None and spec==True and prelast5diff>0:
        spec = None

    if buyPrice1!=None and spec==True and buy1Time!=current.time and prelast1diff < pre2last1diff and stock1Min.touchMiddleLong()==False and buy1Time-lastM5.time<5*60:
        pricelogging.info("tbuy2-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = None
        buy1Time = None
        spec = None
        xbuy = None

    if buyPrice1!=None and spec==None and buy1Time!=current.time and stock1Min.touchUpSell():
        pricelogging.info("tbuy4-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = None
        buy1Time = None
        spec = None
        xbuy = None

    if (xbuy=="6" or xbuy=="9") and  buyPrice1!=None and spec==None and buy1Time!=current.time and prelast1diff<0 and prelast1diff<pre2last1diff and not (stock5Min.middleUpByIndex(0) and lastM5.j - lastM5.k> 0):
        pricelogging.info("tbuy5-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = None
        buy1Time = None
        spec = None
        xbuy = None


    if (xbuy=="7" or xbuy=="8") and  buyPrice1!=None and spec==None and buy1Time!=current.time and buy1Time-lastM5.time<0 and prelast1diff<0 and prelast1diff<pre2last1diff and not (stock5Min.middleUpByIndex(0) and lastM5.j - lastM5.k> 0):
        pricelogging.info("tbuy5-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = None
        buy1Time = None
        spec = None
        xbuy = None

    if buyPrice1==None and spec==None and stock1Min.touchDown() and prelast5diff>0 and lastM5.j - lastM5.k>5 and lastM5.j-lastM5.k > prelast5diff and lastm1.j - lastm1.k>=0 and prelastm1.j-prelastm1.k<0:
        pricelogging.info("tbuy6-%s,time=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = current.close
        buy1Time = current.time
        xbuy = "6"

    if buyPrice1==None and spec==None and stock5Min.middleUpByIndex(1) and stock5Min.middleUpByIndex(0) and lastM5.j - lastM5.k> 5 and stock1Min.downToUp()==False and stock5Min.downToUp()==True:
        if stock1Min.touchMiddle():
            pricelogging.info("tbuy7-%s,time=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = current.close
            buy1Time = current.time
            xbuy="7"
        elif prelast1diff>0 and pre2last1diff<0:
            pricelogging.info("tbuy8-%s,time=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = current.close
            buy1Time = current.time
            xbuy="8"
    if buyPrice1==None and spec==None and prelast1diff>0 and prelast1diff> pre2last1diff and current.j-current.k > prelast1diff and stock1Min.forecastKDJ()==True and lastM5.j-lastM5.k>5 and prelast5diff>0 and lastM5.j-lastM5.k > prelast5diff and stock5Min.downToUp() and stock1Min.downToUp():
        pricelogging.info("tbuy9-%s,time=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = current.close
        buy1Time = current.time
        xbuy = "9"

    '''

    '''
    if sellSpec and ((current.time == buy1Time and current.close>buyPrice1) or (current.time!=buy1Time)):
        pricelogging.info("tbuy21-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = None
        buy1Time = None
        downToUp = None
        upToDown = None
        middleToUp = None
        spec = None
        xspec = None
        sellSpec = None

    if buyPrice1==None and stock1Min.touchShortDown() and lastm1.j - lastm1.k>=0 and prelastm1.j-prelastm1.k<0:
        pricelogging.info("tbuy-%s,time=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = current.close
        buy1Time = current.time
        downToUp=True
        upToDown=None
        middleToUp = None
        spec = None
        xspec = None

    fn = lambda: lastm1.j-lastm1.k<0 and current.j - current.k>0 and current.close > m1down \
                 and current.close > m1up and current.close > m1next and m1upBuySupport>40 and not stock5Min.touchDown()

    if buyPrice1==None and stock1Min.touchShortDown() and fn():
        pricelogging.info("tbuy8-%s,time=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = current.close
        buy1Time = current.time
        downToUp=True
        upToDown=None
        middleToUp = None
        spec = None
        xspec = True


    if buyPrice1==None and stock5Min.downToUp() and fn() and (stock1Min.downToUp() or stock1Min.touchMiddleLong()):
        pricelogging.info("tbuy9-%s,time=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = current.close
        buy1Time = current.time
        downToUp=True
        upToDown=None
        middleToUp = None
        spec = True
        xspec = None

    if (xspec or spec) and buyPrice1!=None and buy1Time==current.time and current.close<buyPrice1:
        sellSpec = True


    if buyPrice1!=None and buy1Time!=current.time and lastm1.j-lastm1.k<=0 and current.j-current.k<0 and downToUp==True and (not stock1Min.touchUp()):
        if prelastM5.close>prelastM5.open and prelastM5.close > pre2lastM5.close:
            return
        else:
            pricelogging.info("tbuy1-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = None
            buy1Time = None
            downToUp = None
            upToDown = None
            middleToUp = None
            spec = None
            xspec = None

    if buy1Time!=current.time and buyPrice1!=None and lastm1.j-lastm1.k<=0 and downToUp==True and stock1Min.touchUp() or (buy1Time!=current.time and buyPrice1!=None and lastm1.close<lastm1.open and middleToUp==True and stock1Min.touchUp()):
        pricelogging.info("tbuy2-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = None
        buy1Time = None
        downToUp = None
        upToDown = True
        middleToUp = None
        spec = None
        xspec = None


    if buyPrice1==None and stock5Min.middleUpByIndex(0) and  lastM5.j - lastM5.k> 0 and stock1Min.downToUp()==False and \
            (stock1Min.touchMiddle() or lastm1.j-lastm1.k > 0):
        pricelogging.info("tbuy3-%s,time=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = current.close
        buy1Time = current.time
        middleToUp=True
        upToDown = None
        downToUp = None
        spec = None
        xspec = None


    if buyPrice1!=None and middleToUp and stock1Min.touchShortDown() and not (stock5Min.touchDown() and prelastM5.j-prelastM5.k>0):
        pricelogging.info("tbuy4-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = None
        buy1Time = None
        downToUp = None
        upToDown = None
        middleToUp = None
        spec = None
        xspec = None


    fndown = lambda: lastm1.j-lastm1.k>0 and current.j - current.k<0 and current.close < m1down \
                 and current.close < m1up and current.close < m1next and m1upSellSupport>30

    if buyPrice1!=None and spec and buy1Time!=current.time and fndown():
        pricelogging.info("tbuy7-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = None
        buy1Time = None
        downToUp = None
        upToDown = None
        middleToUp = None
        spec = None
        xspec = None

    if buyPrice1!=None and xspec and buy1Time!=current.time and  current.time - buy1Time <= 60*3 and stock1Min.mayDown():
        pricelogging.info("tbuy12-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = None
        buy1Time = None
        downToUp = None
        upToDown = None
        middleToUp = None
        spec = None
        xspec = None


    if buyPrice1 != None and buy1Time!=current.time and buyPrice1 > current.close + 5:
        pricelogging.info("tbuy5-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = None
        buy1Time = None
        downToUp = None
        upToDown = None
        middleToUp = None
        spec = None
        xspec = None



    '''
    '''
    if lastm1.j-lastm1.k <0 and isbuy==True and current.close > m1up and buyPrice1==None:
        pricelogging.info("tbuy-%s,time=%s" % (stock1Min.lastKline().close,stock1Min.lastKline().time))
        buyPrice1 = current.close

    if buyPrice1!=None and issell==True and current.close < m1up:
        pricelogging.info("tbuy-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),stock1Min.lastKline().time))
        buyPrice1 = None
    '''


    '''
    kdj,touchBoll = stock1Min.canBuy()

    pricelogging.info("5j-5k=%s,%s,5m=%s,%s,%s,%s,%s,%s,%s,%s" % (lastM5.j-lastM5.k,(prelastM5.j-prelastM5.k<0 and lastM5.j-lastM5.k<5),stock5Min.premiddleDown(),lastm1.j-lastm1.k>prelastm1.j-prelastm1.k,
                                                            touchBoll,lastm1.close> prelastm1.close,current.close>lastm1.close,current.close > m1up,current.close > m1next,buyTriggerTime) )

    if ((lastM5.j-lastM5.k<0 and prelastM5.j-prelastM5.k<-5) or (prelastM5.j-prelastM5.k<0 and lastM5.j-lastM5.k<5) )  and stock5Min.premiddleDown() and lastm1.j-lastm1.k>prelastm1.j-prelastm1.k \
            and touchBoll==True and lastm1.close> prelastm1.close and current.close>lastm1.close and current.close > m1up and current.close > m1next \
        and buyPrice1==None and buyTriggerTime==None:
        buyTriggerTime = current.time
        pricelogging.info("tbuy-trigger,time=%s,price=%s" % (time.ctime(current.time),current.close))

    if buyPrice1 == None:
        if buyTriggerTime != None and current.time - buyTriggerTime == 120:
            if current.j- current.k >= lastm1.j-lastm1.k and not (prelastM5.j-prelastM5.k>=0 and lastM5.j - lastM5.k<=0):
                pricelogging.info("tbuy-%s,time=%s,t=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),buyTriggerTime))
                buyPrice1 = current.close
                buyPrice3 = current.close
                buy1Time = lastM5.time
                buyTriggerTime = None
            else:
                pricelogging.info("tbuy-destory-trigger,time=%s,price=%s,triggerTime=%s" % (time.ctime(current.time),current.close,buyTriggerTime))
                buyTriggerTime = None
        elif buyTriggerTime != None and current.time - buyTriggerTime > 120:
            pricelogging.info("tbuy-destory-trigger,time=%s,price=%s,triggerTime=%s" % (time.ctime(current.time),current.close,buyTriggerTime))
            buyTriggerTime = None

    if buyPrice1 != None and buyPrice1 > current.close + 5:
        if not (prelastM5.j-prelastM5.k>-2 and lastM5.j-lastM5.k>0) or buyPrice1 > current.close + 10:
            pricelogging.info("tbuy1-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),stock1Min.lastKline().time))
            buyPrice1 = None
            buy1Time = None
            buy2Time = None


    touchUp = stock1Min.touchUp();
    if buyPrice1!=None and touchUp == True and lastM5.j - lastM5.k<=0:
        pricelogging.info("tbuy2-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),stock1Min.lastKline().time))
        buyPrice1 = None
        buy1Time = None
        buy2Time = None
        if buyPrice3!=None:
            pricelogging.info("tbuy8-%s,sell-%s,diff=%s,time=%s" % (buyPrice3,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice3),stock1Min.lastKline().time))
            buyPrice3 = None

    if buyPrice1!=None:
        pricelogging.info("txtime=%s,%s,%s" % (buyPrice1,buy2Time,prelastM5.j-prelastM5.k))
        pricelogging.info("txtime2=%s,%s,%s" % (buyPrice1,buy2Time,lastM5.j - lastM5.k))

    if buyPrice1!=None and buy2Time==None and prelastM5.j-prelastM5.k>=0:
        buy2Time = lastM5.time

    if buyPrice1!=None and buy2Time!=None and lastM5.j - lastM5.k<=0:
        pricelogging.info("tbuy3-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),stock1Min.lastKline().time))
        buyPrice1 = None
        buy1Time = None
        buy2Time = None

        if buyPrice3!=None:
            pricelogging.info("tbuy6-%s,sell-%s,diff=%s,time=%s" % (buyPrice3,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice3),stock1Min.lastKline().time))
            buyPrice3 = None

    if buyPrice3!=None and stock1Min.touchUpShort() and lastm1.open > lastm1.close and current.close > buyPrice3:
        pricelogging.info("tbuy5-%s,sell-%s,diff=%s,time=%s" % (buyPrice3,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice3),stock1Min.lastKline().time))
        buyPrice3 = None
        if stock5Min.touchUpMyShort()==True and buyPrice1!=None:
            pricelogging.info("tbuy9-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),stock1Min.lastKline().time))
            buyPrice1 = None
            buy1Time = None
            buy2Time = None
            downToUp = True



    if buyPrice1!=None and buyPrice3==None and stock1Min.touchMiddle()==True and lastM5.j-lastM5.k>10:
        buyPrice3 = current.close
        pricelogging.info("tbuy7-%s,time=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time)))

    if downToUp == True and buyPrice3==None and stock1Min.touchDown() and lastM5.j-lastM5.k>10:
        buyPrice3 = current.close
        pricelogging.info("tbuy11-%s,time=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time)))


    if downToUp == True and buyPrice3!=None and (lastM5.j-lastM5.k<=0 or (stock1Min.touchUpShort() and lastm1.open > lastm1.close and current.close > buyPrice3)):
        pricelogging.info("tbuy12-%s,sell-%s,diff=%s,time=%s" % (buyPrice3,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice3),stock1Min.lastKline().time))
        buyPrice3 = None

    if downToUp==True and buyPrice3==None and lastM5.j-lastM5.k <=0:
        downToUp = False
    '''

    '''
    if buy1Time!=None and buyPrice1!=None:
        if lastM5.time - buy1Time <= 5*60:
            if lastm1.j-lastm1.k<0 and current.close<m1up :
                pricelogging.info("tbuy1-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),stock1Min.lastKline().time))
                buyPrice1 = None
                buy1Time = None
            if lastm1.j-lastm1.k>0 and current.close<m1up:
                if int(current.close)>=int(m5up):
                    return
                pricelogging.info("tbuy2-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),stock1Min.lastKline().time))
                buyPrice1 = None
                buy1Time = None
        else:
            buy1Time = None
    '''
    '''
        if current.close<m5up and lastM5.j-lastM5.k>0 and buy2Time==None:
            buy2Time = lastM5.time
        elif buy2Time!=None and current.time-buy2Time>3 and current.close<m5up and lastm1.j-lastm1.k<prelastm1.j-prelastm1.k:
            pricelogging.info("tbuy3-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),stock1Min.lastKline().time))
            buyPrice1 = None
            buy2Time = None
        elif buy2Time!=None and current.time-buy2Time>4 and prelastM5.j-pre2lastM5.k > pre2lastM5.j-pre2lastM5.k:
            buy2Time = None
        elif buy2Time!=None and current.time-buy2Time>4 and prelastM5.j-pre2lastM5.k < pre2lastM5.j-pre2lastM5.k:
            pricelogging.info("tbuy4-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),stock1Min.lastKline().time))
            buyPrice1 = None
            buy2Time = None
        '''

    '''
    kdj,touchBoll = stock1Min.canBuy()
    if buyPrice2!=None and kdj==False:
        pricelogging.info("buy2-%s,sell-%s,diff=%s" % (buyPrice2,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice2)))
        buyPrice2 = None
    if buyPrice2==None and kdj==True and stock5Min.forecastKDJ()==True:
        buyPrice2=stock1Min.lastKline().close
        pricelogging.info("buy2-%s,time=%s" % (stock1Min.lastKline().close,stock1Min.lastKline().time))
    '''


def go2():
    global buyPrice1,buyPrice2,bidsList,asksList,buy1Time,buy2Time,buyTriggerTime,buyPrice3,downToUp,upToDown,middleToUp,spec,xspec,sellSpec,xbuy,xkdj,up15
    m5up,m5down,m5next = stock5Min.forecastClose()
    m1up,m1down,m1next = stock1Min.forecastClose()
    lastM5 = stock5Min.lastKline()
    prelastM5 = stock5Min.preLastKline()
    pre2lastM5 = stock5Min.pre2LastKline()
    current = stock1Min.lastKline()
    lastm1 = stock1Min.preLastKline()
    prelastm1 = stock1Min.pre2LastKline()
    lastM15 = stock15Min.lastKline()

    lastM15 = stock15Min.lastKline()
    prelastM15 = stock15Min.preLastKline()
    pre2lastM15 = stock15Min.pre2LastKline()


    if current.time-lastM5.time>=5*60:
        return

    prelast5diff = prelastM5.j-prelastM5.k
    pre2last5diff = pre2lastM5.j - pre2lastM5.k

    prelast1diff = lastm1.j-lastm1.k
    pre2last1diff = prelastm1.j - prelastm1.k

    prelast15diff = prelastM15.j - prelastM15.k
    pre2last15diff = pre2lastM15.j - pre2lastM15.k


    pricelogging.info("time=%s,price=%s,preM1=%s,pre2M1=%s,preM5=%s,pre2M=%s,preM15=%s,pre2M15=%s" % (time.ctime(current.time),current.price,prelast1diff,pre2last1diff,prelast5diff,pre2last5diff,prelast15diff,pre2last15diff))

    pricelogging.info("spec=%s,5down=%s,pre2kdj=%s,prekdj=%s,curkdj=%s,up15=%s" % (spec,stock5Min.touchDownRange(0,4),pre2last5diff,prelast5diff,lastM5.j-lastM5.k,up15))

    pricelogging.info("15downToUP=%s,kline=%s,prelast=%s,pre2last=%s" % (stock15Min.downToUp(),stock15Min.findDownKline(),prelast15diff,pre2last15diff))



    if up15 == None and stock15Min.downToUp() and stock15Min.findDownKline()!=None and stock15Min.countCross(stock15Min.findDownKline().time)<=1:
        if pre2last15diff>0 and prelast15diff>0 and prelast15diff > pre2last15diff:
            up15 = True

    if stock15Min.downToUp()==False or prelast15diff<0:
        up15 = None

    if spec == None:
        '''
        if buy1Time==None and stock5Min.touchDownRange(0,4)==True \
                                and pre2last5diff<-5 and prelast5diff>0 and prelastM5.close > pre2lastM5.close and prelast5diff>pre2last5diff:
            buy1Time = current.time
            buy2Time = lastM5.time
            xkdj = prelast1diff
            xbuy="11"
            spec = 1
            pricelogging.info("xbuy11-%s,%s,time=%s,b2time=%s" % (xbuy,stock1Min.lastKline().close,time.ctime(buy1Time),time.ctime(buy2Time)))
        '''

        if buy1Time==None and stock5Min.touchDownRange(0,4)==True \
                and pre2last5diff>0 and prelast5diff>0 and prelastM5.close > pre2lastM5.close and prelast5diff>pre2last5diff:
            buy1Time = current.time
            buy2Time = lastM5.time
            xkdj = prelast1diff
            xbuy="12"
            spec = 1
            pricelogging.info("xbuy12-%s,%s,time=%s,b2time=%s" % (xbuy,stock1Min.lastKline().close,time.ctime(buy1Time),time.ctime(buy2Time)))

        #touch down to up
        if buy1Time==None and stock5Min.touchDownRange(0,4)==True and \
                                stock5Min.preMyLastKline(3).j- stock5Min.preMyLastKline(3).k < 0 and pre2last5diff<-5 and prelast5diff>-5 and prelastM5.close > pre2lastM5.close and  prelast5diff>pre2last5diff:
            buy1Time = current.time
            buy2Time = lastM5.time
            xkdj = prelast1diff
            xbuy="1"
            spec = 1
            pricelogging.info("xbuy1-%s,%s,time=%s,b2time=%s" % (xbuy,stock1Min.lastKline().close,time.ctime(buy1Time),time.ctime(buy2Time)))



        if buy1Time==None and up15==True and pre2last5diff<0 and prelast5diff>pre2last5diff:
            buy1Time = current.time
            buy2Time = lastM5.time
            xkdj = prelast1diff
            xbuy="51"
            spec = 1
            pricelogging.info("xbuy51-%s,%s,time=%s,b2time=%s" % (xbuy,stock1Min.lastKline().close,time.ctime(buy1Time),time.ctime(buy2Time)))


        if buy1Time==None and stock5Min.downToUp()==False and \
                                stock5Min.preMyLastKline(3).j- stock5Min.preMyLastKline(3).k < 0 and pre2last5diff<-5 and prelast5diff>-5 and prelastM5.close > pre2lastM5.close and  prelast5diff>pre2last5diff:
            buy1Time = current.time
            buy2Time = lastM5.time
            xkdj = prelast1diff
            xbuy="81"
            spec = 1
            pricelogging.info("xbuy81-%s,%s,time=%s,b2time=%s" % (xbuy,stock1Min.lastKline().close,time.ctime(buy1Time),time.ctime(buy2Time)))



    if buy2Time!=None and lastM5.time - buy2Time == 5*60 and (prelast5diff<pre2last5diff or prelast5diff<0) and xbuy!="51":
        pricelogging.info("xdisable-%s-%s,time=%s,deciderTime=%s" % (xbuy,stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time)))
        if buyPrice1 > current.close:
            return
        if buyPrice1!=None:
            pricelogging.info("tbuy4-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))

        pricelogging.info("disable-%s-%s,time=%s,deciderTime=%s" % (xbuy,stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time)))
        buy1Time = None
        buy2Time = None
        xbuy=None
        buyPrice1 = None
        xkdj = None
        spec = None

    """
    if buy2Time!=None and stock5Min.countCross(buy2Time)>=2:
        if buyPrice1 > current.close:
            return
        if buyPrice1!=None:
            pricelogging.info("tbuy43-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))

        pricelogging.info("disable43-%s-%s,time=%s,deciderTime=%s" % (xbuy,stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time)))
        buy1Time = None
        buy2Time = None
        xbuy=None
        buyPrice1 = None
        xkdj = None
        spec = None
    """

    if buy1Time!=None and buyPrice1==None and xbuy!=None and spec==1:
        if stock1Min.downToUp() and xkdj<0:
            if (pre2last1diff<0 and prelast1diff>0) or (pre2last1diff>=0 and prelast1diff>pre2last1diff):
                pricelogging.info("tbuy12-%s,time=%s,deciderTime=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time)))
                buyPrice1 = current.close
                xkdj = None
                spec = 2
            return

        if stock1Min.downToUp() and stock1Min.countCross(buy1Time)==0 and stock1Min.kdjUpDontTouchMax(buy1Time) and lastM5.j-lastM5.k>prelast5diff:
            pricelogging.info("tbuy10-%s,time=%s,deciderTime=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time)))
            buyPrice1 = current.close
            xkdj = None
            spec = 2
            return

        if stock1Min.downToUp() and stock1Min.kdjUp(buy1Time) and stock1Min.kdjUpDontTouchMax(buy1Time) and lastM5.j-lastM5.k>prelast5diff:
            pricelogging.info("tbuy1-%s,time=%s,deciderTime=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time)))
            buyPrice1 = current.close
            xkdj = None
            spec = 2
            return
        if stock1Min.downToUp()==False and prelast1diff<0 and current.close<current.boll and lastM5.j-lastM5.k>prelast5diff:
            pricelogging.info("tbuy2-%s,time=%s,deciderTime=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time)))
            buyPrice1 = current.close
            xkdj = None
            spec = 2
            return

        if stock1Min.downToUp()==False and pre2last1diff<0 and prelast1diff>pre2last1diff and current.close>current.boll and lastM5.j-lastM5.k>prelast5diff:
            pricelogging.info("tbuy21-%s,time=%s,deciderTime=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time)))
            buyPrice1 = current.close
            xkdj = None
            spec = 2
            return

        if stock1Min.downToUp() and stock1Min.kdjUp(buy1Time) and stock1Min.kdjUpDontTouchMax(buy1Time)==False and prelast1diff>pre2last1diff and lastM5.j-lastM5.k>prelast5diff:
            pricelogging.info("tbuy3-%s,time=%s,deciderTime=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time)))
            buyPrice1 = current.close
            xkdj = None
            spec = 2
            return

    if buy2Time!=None and  lastM5.time - buy2Time > 5*60 and stock5Min.countCross(buy2Time)>=2 and current.close>lastM5.up:
        if buyPrice1!=None:
            pricelogging.info("tbuy5-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
        pricelogging.info("disable2-%s-%s,time=%s,deciderTime=%s" % (xbuy,stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time)))
        buy1Time = None
        buy2Time = None
        xbuy=None
        buyPrice1 = None
        xkdj = None
        spec=None

    if buy2Time!=None and  lastM5.time - buy2Time > 5*60 and lastM5.j-lastM5.k<=0:
        if buyPrice1 > current.close:
            return
        if buyPrice1!=None:
            pricelogging.info("tbuy5-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
        pricelogging.info("disable2-%s-%s,time=%s,deciderTime=%s" % (xbuy,stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time)))
        buy1Time = None
        buy2Time = None
        xbuy=None
        buyPrice1 = None
        xkdj = None
        spec=None


    if buyPrice1!=None and spec==2 and (current.time-buy2Time<=4*60 and current.time-buy2Time>2*60) and stock1Min.touchDown() and current.j-current.k<prelast1diff:
        pricelogging.info("tbuy61-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
        buy1Time = None
        buy2Time = None
        xbuy=None
        buyPrice1 = None
        xkdj = None
        spec=None

    if buyPrice1!=None and spec==2 and ((stock1Min.countTouchUp(buy1Time)>=1 and stock1Min.countCross(buy1Time)>2) or stock1Min.countTouchUp(buy1Time)==1)and stock1Min.touchUpSell():
        if stock1Min.lastKline().close > buyPrice1:
            pricelogging.info("tbuy6-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buy1Time = None
            xbuy=None
            buyPrice1 = None
            xkdj = None
            spec = 3


    if buyPrice1!=None and spec==3 and prelast1diff < pre2last1diff and stock1Min.touchUpMyShort():
        if stock1Min.lastKline().close > buyPrice1:
            pricelogging.info("tbuy7-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buy1Time = None
            xbuy=None
            buyPrice1 = None
            xkdj = None

    if buyPrice1==None and spec==3 and buy2Time!=None and prelast1diff > pre2last1diff and  pre2last1diff<0 and prelast1diff>0 and prelast5diff>0 and lastM5.j-lastM5.k>10 and current.close > current.open:
        pricelogging.info("tbuy8-%s,time=%s,deciderTime=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time)))
        buyPrice1=current.close
        buy1Time = current.time

    '''
    if buyPrice1==None and prelast5diff<0 and pre2last5diff<0 and  prelast5diff>pre2last5diff and prelast5diff>-5 and stock5Min.touchShortDown() \
        and stock1Min.touchDown() and stock1Min.downToUp():
        if pre2last1diff<0 and prelast1diff>=0 :
            pricelogging.info("tbuy-%s,time=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = current.close
            buy1Time = current.time
            spec = True
        if pre2last1diff>=0 and prelast1diff > pre2last1diff:
            pricelogging.info("tbuy1-%s,time=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = current.close
            buy1Time = current.time
            spec = True

    if buyPrice1==None and prelast5diff<0 and pre2last5diff<0 and  prelast5diff>pre2last5diff and prelast5diff>-5 and stock5Min.touchSimlarDown(4) \
            and stock1Min.touchDown() and stock1Min.downToUp():
        if pre2last1diff<0 and prelast1diff>=0 :
            pricelogging.info("tbuy21-%s,time=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = current.close
            buy1Time = current.time
            spec = True
        if pre2last1diff>=0 and prelast1diff > pre2last1diff:
            pricelogging.info("tbuy22-%s,time=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = current.close
            buy1Time = current.time
            spec = True


    if buyPrice1!=None and spec==True and prelast5diff>0:
        spec = None

    if buyPrice1!=None and spec==True and buy1Time!=current.time and prelast1diff < pre2last1diff and stock1Min.touchMiddleLong()==False and buy1Time-lastM5.time<5*60:
        pricelogging.info("tbuy2-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = None
        buy1Time = None
        spec = None
        xbuy = None

    if buyPrice1!=None and spec==None and buy1Time!=current.time and stock1Min.touchUpSell():
        pricelogging.info("tbuy4-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = None
        buy1Time = None
        spec = None
        xbuy = None

    if (xbuy=="6" or xbuy=="9") and  buyPrice1!=None and spec==None and buy1Time!=current.time and prelast1diff<0 and prelast1diff<pre2last1diff and not (stock5Min.middleUpByIndex(0) and lastM5.j - lastM5.k> 0):
        pricelogging.info("tbuy5-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = None
        buy1Time = None
        spec = None
        xbuy = None


    if (xbuy=="7" or xbuy=="8") and  buyPrice1!=None and spec==None and buy1Time!=current.time and buy1Time-lastM5.time<0 and prelast1diff<0 and prelast1diff<pre2last1diff and not (stock5Min.middleUpByIndex(0) and lastM5.j - lastM5.k> 0):
        pricelogging.info("tbuy5-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = None
        buy1Time = None
        spec = None
        xbuy = None

    if buyPrice1==None and spec==None and stock1Min.touchDown() and prelast5diff>0 and lastM5.j - lastM5.k>5 and lastM5.j-lastM5.k > prelast5diff and lastm1.j - lastm1.k>=0 and prelastm1.j-prelastm1.k<0:
        pricelogging.info("tbuy6-%s,time=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = current.close
        buy1Time = current.time
        xbuy = "6"

    if buyPrice1==None and spec==None and stock5Min.middleUpByIndex(1) and stock5Min.middleUpByIndex(0) and lastM5.j - lastM5.k> 5 and stock1Min.downToUp()==False and stock5Min.downToUp()==True:
        if stock1Min.touchMiddle():
            pricelogging.info("tbuy7-%s,time=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = current.close
            buy1Time = current.time
            xbuy="7"
        elif prelast1diff>0 and pre2last1diff<0:
            pricelogging.info("tbuy8-%s,time=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = current.close
            buy1Time = current.time
            xbuy="8"
    if buyPrice1==None and spec==None and prelast1diff>0 and prelast1diff> pre2last1diff and current.j-current.k > prelast1diff and stock1Min.forecastKDJ()==True and lastM5.j-lastM5.k>5 and prelast5diff>0 and lastM5.j-lastM5.k > prelast5diff and stock5Min.downToUp() and stock1Min.downToUp():
        pricelogging.info("tbuy9-%s,time=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = current.close
        buy1Time = current.time
        xbuy = "9"

    '''

    '''
    if sellSpec and ((current.time == buy1Time and current.close>buyPrice1) or (current.time!=buy1Time)):
        pricelogging.info("tbuy21-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = None
        buy1Time = None
        downToUp = None
        upToDown = None
        middleToUp = None
        spec = None
        xspec = None
        sellSpec = None

    if buyPrice1==None and stock1Min.touchShortDown() and lastm1.j - lastm1.k>=0 and prelastm1.j-prelastm1.k<0:
        pricelogging.info("tbuy-%s,time=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = current.close
        buy1Time = current.time
        downToUp=True
        upToDown=None
        middleToUp = None
        spec = None
        xspec = None

    fn = lambda: lastm1.j-lastm1.k<0 and current.j - current.k>0 and current.close > m1down \
                 and current.close > m1up and current.close > m1next and m1upBuySupport>40 and not stock5Min.touchDown()

    if buyPrice1==None and stock1Min.touchShortDown() and fn():
        pricelogging.info("tbuy8-%s,time=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = current.close
        buy1Time = current.time
        downToUp=True
        upToDown=None
        middleToUp = None
        spec = None
        xspec = True


    if buyPrice1==None and stock5Min.downToUp() and fn() and (stock1Min.downToUp() or stock1Min.touchMiddleLong()):
        pricelogging.info("tbuy9-%s,time=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = current.close
        buy1Time = current.time
        downToUp=True
        upToDown=None
        middleToUp = None
        spec = True
        xspec = None

    if (xspec or spec) and buyPrice1!=None and buy1Time==current.time and current.close<buyPrice1:
        sellSpec = True


    if buyPrice1!=None and buy1Time!=current.time and lastm1.j-lastm1.k<=0 and current.j-current.k<0 and downToUp==True and (not stock1Min.touchUp()):
        if prelastM5.close>prelastM5.open and prelastM5.close > pre2lastM5.close:
            return
        else:
            pricelogging.info("tbuy1-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = None
            buy1Time = None
            downToUp = None
            upToDown = None
            middleToUp = None
            spec = None
            xspec = None

    if buy1Time!=current.time and buyPrice1!=None and lastm1.j-lastm1.k<=0 and downToUp==True and stock1Min.touchUp() or (buy1Time!=current.time and buyPrice1!=None and lastm1.close<lastm1.open and middleToUp==True and stock1Min.touchUp()):
        pricelogging.info("tbuy2-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = None
        buy1Time = None
        downToUp = None
        upToDown = True
        middleToUp = None
        spec = None
        xspec = None


    if buyPrice1==None and stock5Min.middleUpByIndex(0) and  lastM5.j - lastM5.k> 0 and stock1Min.downToUp()==False and \
            (stock1Min.touchMiddle() or lastm1.j-lastm1.k > 0):
        pricelogging.info("tbuy3-%s,time=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = current.close
        buy1Time = current.time
        middleToUp=True
        upToDown = None
        downToUp = None
        spec = None
        xspec = None


    if buyPrice1!=None and middleToUp and stock1Min.touchShortDown() and not (stock5Min.touchDown() and prelastM5.j-prelastM5.k>0):
        pricelogging.info("tbuy4-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = None
        buy1Time = None
        downToUp = None
        upToDown = None
        middleToUp = None
        spec = None
        xspec = None


    fndown = lambda: lastm1.j-lastm1.k>0 and current.j - current.k<0 and current.close < m1down \
                 and current.close < m1up and current.close < m1next and m1upSellSupport>30

    if buyPrice1!=None and spec and buy1Time!=current.time and fndown():
        pricelogging.info("tbuy7-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = None
        buy1Time = None
        downToUp = None
        upToDown = None
        middleToUp = None
        spec = None
        xspec = None

    if buyPrice1!=None and xspec and buy1Time!=current.time and  current.time - buy1Time <= 60*3 and stock1Min.mayDown():
        pricelogging.info("tbuy12-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = None
        buy1Time = None
        downToUp = None
        upToDown = None
        middleToUp = None
        spec = None
        xspec = None


    if buyPrice1 != None and buy1Time!=current.time and buyPrice1 > current.close + 5:
        pricelogging.info("tbuy5-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = None
        buy1Time = None
        downToUp = None
        upToDown = None
        middleToUp = None
        spec = None
        xspec = None



    '''
    '''
    if lastm1.j-lastm1.k <0 and isbuy==True and current.close > m1up and buyPrice1==None:
        pricelogging.info("tbuy-%s,time=%s" % (stock1Min.lastKline().close,stock1Min.lastKline().time))
        buyPrice1 = current.close

    if buyPrice1!=None and issell==True and current.close < m1up:
        pricelogging.info("tbuy-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),stock1Min.lastKline().time))
        buyPrice1 = None
    '''


    '''
    kdj,touchBoll = stock1Min.canBuy()

    pricelogging.info("5j-5k=%s,%s,5m=%s,%s,%s,%s,%s,%s,%s,%s" % (lastM5.j-lastM5.k,(prelastM5.j-prelastM5.k<0 and lastM5.j-lastM5.k<5),stock5Min.premiddleDown(),lastm1.j-lastm1.k>prelastm1.j-prelastm1.k,
                                                            touchBoll,lastm1.close> prelastm1.close,current.close>lastm1.close,current.close > m1up,current.close > m1next,buyTriggerTime) )

    if ((lastM5.j-lastM5.k<0 and prelastM5.j-prelastM5.k<-5) or (prelastM5.j-prelastM5.k<0 and lastM5.j-lastM5.k<5) )  and stock5Min.premiddleDown() and lastm1.j-lastm1.k>prelastm1.j-prelastm1.k \
            and touchBoll==True and lastm1.close> prelastm1.close and current.close>lastm1.close and current.close > m1up and current.close > m1next \
        and buyPrice1==None and buyTriggerTime==None:
        buyTriggerTime = current.time
        pricelogging.info("tbuy-trigger,time=%s,price=%s" % (time.ctime(current.time),current.close))

    if buyPrice1 == None:
        if buyTriggerTime != None and current.time - buyTriggerTime == 120:
            if current.j- current.k >= lastm1.j-lastm1.k and not (prelastM5.j-prelastM5.k>=0 and lastM5.j - lastM5.k<=0):
                pricelogging.info("tbuy-%s,time=%s,t=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),buyTriggerTime))
                buyPrice1 = current.close
                buyPrice3 = current.close
                buy1Time = lastM5.time
                buyTriggerTime = None
            else:
                pricelogging.info("tbuy-destory-trigger,time=%s,price=%s,triggerTime=%s" % (time.ctime(current.time),current.close,buyTriggerTime))
                buyTriggerTime = None
        elif buyTriggerTime != None and current.time - buyTriggerTime > 120:
            pricelogging.info("tbuy-destory-trigger,time=%s,price=%s,triggerTime=%s" % (time.ctime(current.time),current.close,buyTriggerTime))
            buyTriggerTime = None

    if buyPrice1 != None and buyPrice1 > current.close + 5:
        if not (prelastM5.j-prelastM5.k>-2 and lastM5.j-lastM5.k>0) or buyPrice1 > current.close + 10:
            pricelogging.info("tbuy1-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),stock1Min.lastKline().time))
            buyPrice1 = None
            buy1Time = None
            buy2Time = None


    touchUp = stock1Min.touchUp();
    if buyPrice1!=None and touchUp == True and lastM5.j - lastM5.k<=0:
        pricelogging.info("tbuy2-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),stock1Min.lastKline().time))
        buyPrice1 = None
        buy1Time = None
        buy2Time = None
        if buyPrice3!=None:
            pricelogging.info("tbuy8-%s,sell-%s,diff=%s,time=%s" % (buyPrice3,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice3),stock1Min.lastKline().time))
            buyPrice3 = None

    if buyPrice1!=None:
        pricelogging.info("txtime=%s,%s,%s" % (buyPrice1,buy2Time,prelastM5.j-prelastM5.k))
        pricelogging.info("txtime2=%s,%s,%s" % (buyPrice1,buy2Time,lastM5.j - lastM5.k))

    if buyPrice1!=None and buy2Time==None and prelastM5.j-prelastM5.k>=0:
        buy2Time = lastM5.time

    if buyPrice1!=None and buy2Time!=None and lastM5.j - lastM5.k<=0:
        pricelogging.info("tbuy3-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),stock1Min.lastKline().time))
        buyPrice1 = None
        buy1Time = None
        buy2Time = None

        if buyPrice3!=None:
            pricelogging.info("tbuy6-%s,sell-%s,diff=%s,time=%s" % (buyPrice3,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice3),stock1Min.lastKline().time))
            buyPrice3 = None

    if buyPrice3!=None and stock1Min.touchUpShort() and lastm1.open > lastm1.close and current.close > buyPrice3:
        pricelogging.info("tbuy5-%s,sell-%s,diff=%s,time=%s" % (buyPrice3,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice3),stock1Min.lastKline().time))
        buyPrice3 = None
        if stock5Min.touchUpMyShort()==True and buyPrice1!=None:
            pricelogging.info("tbuy9-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),stock1Min.lastKline().time))
            buyPrice1 = None
            buy1Time = None
            buy2Time = None
            downToUp = True



    if buyPrice1!=None and buyPrice3==None and stock1Min.touchMiddle()==True and lastM5.j-lastM5.k>10:
        buyPrice3 = current.close
        pricelogging.info("tbuy7-%s,time=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time)))

    if downToUp == True and buyPrice3==None and stock1Min.touchDown() and lastM5.j-lastM5.k>10:
        buyPrice3 = current.close
        pricelogging.info("tbuy11-%s,time=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time)))


    if downToUp == True and buyPrice3!=None and (lastM5.j-lastM5.k<=0 or (stock1Min.touchUpShort() and lastm1.open > lastm1.close and current.close > buyPrice3)):
        pricelogging.info("tbuy12-%s,sell-%s,diff=%s,time=%s" % (buyPrice3,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice3),stock1Min.lastKline().time))
        buyPrice3 = None

    if downToUp==True and buyPrice3==None and lastM5.j-lastM5.k <=0:
        downToUp = False
    '''

    '''
    if buy1Time!=None and buyPrice1!=None:
        if lastM5.time - buy1Time <= 5*60:
            if lastm1.j-lastm1.k<0 and current.close<m1up :
                pricelogging.info("tbuy1-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),stock1Min.lastKline().time))
                buyPrice1 = None
                buy1Time = None
            if lastm1.j-lastm1.k>0 and current.close<m1up:
                if int(current.close)>=int(m5up):
                    return
                pricelogging.info("tbuy2-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),stock1Min.lastKline().time))
                buyPrice1 = None
                buy1Time = None
        else:
            buy1Time = None
    '''
    '''
        if current.close<m5up and lastM5.j-lastM5.k>0 and buy2Time==None:
            buy2Time = lastM5.time
        elif buy2Time!=None and current.time-buy2Time>3 and current.close<m5up and lastm1.j-lastm1.k<prelastm1.j-prelastm1.k:
            pricelogging.info("tbuy3-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),stock1Min.lastKline().time))
            buyPrice1 = None
            buy2Time = None
        elif buy2Time!=None and current.time-buy2Time>4 and prelastM5.j-pre2lastM5.k > pre2lastM5.j-pre2lastM5.k:
            buy2Time = None
        elif buy2Time!=None and current.time-buy2Time>4 and prelastM5.j-pre2lastM5.k < pre2lastM5.j-pre2lastM5.k:
            pricelogging.info("tbuy4-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),stock1Min.lastKline().time))
            buyPrice1 = None
            buy2Time = None
        '''

    '''
    kdj,touchBoll = stock1Min.canBuy()
    if buyPrice2!=None and kdj==False:
        pricelogging.info("buy2-%s,sell-%s,diff=%s" % (buyPrice2,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice2)))
        buyPrice2 = None
    if buyPrice2==None and kdj==True and stock5Min.forecastKDJ()==True:
        buyPrice2=stock1Min.lastKline().close
        pricelogging.info("buy2-%s,time=%s" % (stock1Min.lastKline().close,stock1Min.lastKline().time))
    '''

def go3():
    global buyPrice1,buyPrice2,bidsList,asksList,buy1Time,buy2Time,buyTriggerTime,buyPrice3,downToUp,upToDown,middleToUp,spec,xspec,sellSpec,xbuy,xkdj,up15,up5
    m5up,m5down,m5next = stock5Min.forecastClose()
    m1up,m1down,m1next = stock1Min.forecastClose()
    lastM5 = stock5Min.lastKline()
    prelastM5 = stock5Min.preLastKline()
    pre2lastM5 = stock5Min.pre2LastKline()
    current = stock1Min.lastKline()
    lastm1 = stock1Min.preLastKline()
    prelastm1 = stock1Min.pre2LastKline()
    lastM15 = stock15Min.lastKline()

    lastM15 = stock15Min.lastKline()
    prelastM15 = stock15Min.preLastKline()
    pre2lastM15 = stock15Min.pre2LastKline()


    if current.time-lastM5.time>=5*60:
        return

    prelast5diff = prelastM5.j-prelastM5.k
    pre2last5diff = pre2lastM5.j - pre2lastM5.k

    prelast1diff = lastm1.j-lastm1.k
    pre2last1diff = prelastm1.j - prelastm1.k

    prelast15diff = prelastM15.j - prelastM15.k
    pre2last15diff = pre2lastM15.j - pre2lastM15.k


    pricelogging.info("time=%s,price=%s,preM1=%s,pre2M1=%s,preM5=%s,pre2M=%s,preM15=%s,pre2M15=%s" % (time.ctime(current.time),current.close,prelast1diff,pre2last1diff,prelast5diff,pre2last5diff,prelast15diff,pre2last15diff))

    pricelogging.info("spec=%s,5down=%s,pre2kdj=%s,prekdj=%s,curkdj=%s,up15=%s,up5=%s" % (spec,stock5Min.touchDownRange(0,4),pre2last5diff,prelast5diff,lastM5.j-lastM5.k,up15,up5))

    pricelogging.info("15downToUP=%s,kline=%s,prelast=%s,pre2last=%s" % (stock15Min.downToUp(),stock15Min.findDownKline(),prelast15diff,pre2last15diff))


    if up15 == None and stock15Min.downToUp() and stock15Min.findDownKline()!=None and stock15Min.countCross(stock15Min.findDownKline().time)<=1:
        if pre2last15diff>0 and prelast15diff>0:
            up15 = True

    if stock15Min.downToUp()==False or prelast15diff<0:
        up15 = None

    if up5 == None:
        if buy1Time==None and stock5Min.touchDownRange(0,4)==True \
                and pre2last5diff>0 and prelast5diff>0 and prelastM5.close > pre2lastM5.close and prelast5diff>pre2last5diff:
            buy1Time = current.time
            buy2Time = lastM5.time
            xkdj = prelast1diff
            xbuy="12"
            up5 = 1
            pricelogging.info("xbuy12-%s,%s,time=%s,b2time=%s" % (xbuy,stock1Min.lastKline().close,time.ctime(buy1Time),time.ctime(buy2Time)))

        #touch down to up
        if buy1Time==None and stock5Min.touchDownRange(0,4)==True and \
                                stock5Min.preMyLastKline(3).j- stock5Min.preMyLastKline(3).k < 0 and pre2last5diff<-5 and prelast5diff>-5 and prelastM5.close > pre2lastM5.close and  prelast5diff>pre2last5diff:
            buy1Time = current.time
            buy2Time = lastM5.time
            xkdj = prelast1diff
            xbuy="1"
            up5 = 1
            pricelogging.info("xbuy1-%s,%s,time=%s,b2time=%s" % (xbuy,stock1Min.lastKline().close,time.ctime(buy1Time),time.ctime(buy2Time)))

        if buy1Time==None and stock5Min.downToUp()==False and \
                                stock5Min.preMyLastKline(3).j- stock5Min.preMyLastKline(3).k < 0 and pre2last5diff<-5 and prelast5diff>-5 and prelastM5.close > pre2lastM5.close and  prelast5diff>pre2last5diff:
            buy1Time = current.time
            buy2Time = lastM5.time
            xkdj = prelast1diff
            xbuy="81"
            up5 = 1
            pricelogging.info("xbuy81-%s,%s,time=%s,b2time=%s" % (xbuy,stock1Min.lastKline().close,time.ctime(buy1Time),time.ctime(buy2Time)))


    if buy2Time!=None and lastM5.time - buy2Time == 5*60 and (prelast5diff<pre2last5diff or prelast5diff<0):
        up5 = None
        buy1Time = None
        buy2Time = None
        xbuy=None
        xkdj = None

    if buy2Time!=None and  lastM5.time - buy2Time > 5*60 and lastM5.j-lastM5.k<=0:
        up5 = None
        buy1Time = None
        buy2Time = None
        xbuy=None
        xkdj = None


    if buy1Time!=None and buyPrice1==None and xbuy!=None and up5==1:
        if stock1Min.downToUp() and xkdj<0:
            if (pre2last1diff<0 and prelast1diff>0) or (pre2last1diff>=0 and prelast1diff>pre2last1diff):
                buy1Time = current.time
                buyPrice1 = current.close
                xkdj = None
                up5 =2
                pricelogging.info("tbuy12-%s,time=%s,deciderTime=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time)))
            return

        if stock1Min.downToUp() and stock1Min.countCross(buy1Time)==0 and stock1Min.kdjUpDontTouchMax(buy1Time) and lastM5.j-lastM5.k>prelast5diff:
            buy1Time = current.time
            buyPrice1 = current.close
            xkdj = None
            up5 = 2
            pricelogging.info("tbuy10-%s,time=%s,deciderTime=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time)))
            return

        if stock1Min.downToUp() and stock1Min.kdjUp(buy1Time) and stock1Min.kdjUpDontTouchMax(buy1Time) and lastM5.j-lastM5.k>prelast5diff:
            buy1Time = current.time
            buyPrice1 = current.close
            xkdj = None
            up5 = 2
            pricelogging.info("tbuy1-%s,time=%s,deciderTime=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time)))
            return
        if stock1Min.downToUp()==False and prelast1diff<0 and current.close<current.boll and lastM5.j-lastM5.k>prelast5diff:
            buy1Time = current.time
            buyPrice1 = current.close
            xkdj = None
            up5 = 2
            pricelogging.info("tbuy2-%s,time=%s,deciderTime=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time)))
            return

        if stock1Min.downToUp()==False and pre2last1diff<0 and prelast1diff>pre2last1diff and current.close>current.boll and lastM5.j-lastM5.k>prelast5diff:
            buy1Time = current.time
            buyPrice1 = current.close
            xkdj = None
            up5 = 2
            pricelogging.info("tbuy21-%s,time=%s,deciderTime=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time)))
            return

        if stock1Min.downToUp() and stock1Min.kdjUp(buy1Time) and stock1Min.kdjUpDontTouchMax(buy1Time)==False and prelast1diff>pre2last1diff and lastM5.j-lastM5.k>prelast5diff:
            buy1Time = current.time
            buyPrice1 = current.close
            xkdj = None
            up5 = 2
            pricelogging.info("tbuy3-%s,time=%s,deciderTime=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time)))
            return


    if buyPrice1!=None and (stock1Min.touchUpSell() or current.j-current.k<0):
        if buyPrice1 > current.close-1:
            return
        if buyPrice1!=None:
            pricelogging.info("tbuy5-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
        pricelogging.info("disable2-%s-%s,time=%s,deciderTime=%s" % (xbuy,stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time)))
        buy1Time = None
        buyPrice1 = None


    if up5!=None and up5>=2 and stock5Min.downToUp() and buyPrice1==None and  prelast1diff > pre2last1diff and pre2last1diff<0 and prelastm1.close<lastm1.close:
        buy1Time = current.time
        buyPrice1 = current.close
        up5 += 1
        pricelogging.info("tbuy31-%s,time=%s,deciderTime=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time)))


    if up5!=None and up5>=2 and stock5Min.downToUp()==False and buyPrice1==None and  prelast1diff > pre2last1diff and pre2last1diff<0 and prelast1diff>0 and prelastm1.close<lastm1.close:
        buy1Time = current.time
        buyPrice1 = current.close
        up5 += 1
        pricelogging.info("tbuy32-%s,time=%s,deciderTime=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time)))


    if up15 and prelast5diff > pre2last5diff and prelast5diff<0 and buyPrice1==None and prelast1diff > pre2last1diff and pre2last1diff<0 and prelast1diff>0 and prelastm1.close<lastm1.close:
        buy1Time = current.time
        buyPrice1 = current.close
        pricelogging.info("tbuy33-%s,time=%s,deciderTime=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time)))

def go4():
    global buyPrice1,buyPrice2,bidsList,asksList,buy1Time,buy2Time,buyTriggerTime,buyPrice3,downToUp,upToDown,middleToUp,spec,xspec,sellSpec,xbuy,xkdj,up15,up5,kk1pos,kk5pos,kk15pos
    m5up,m5down,m5next = stock5Min.forecastClose()
    m1up,m1down,m1next = stock1Min.forecastClose()
    lastM5 = stock5Min.lastKline()
    prelastM5 = stock5Min.preLastKline()
    pre2lastM5 = stock5Min.pre2LastKline()
    current = stock1Min.lastKline()
    lastm1 = stock1Min.preLastKline()
    prelastm1 = stock1Min.pre2LastKline()
    lastM15 = stock15Min.lastKline()

    lastM15 = stock15Min.lastKline()
    prelastM15 = stock15Min.preLastKline()
    pre2lastM15 = stock15Min.pre2LastKline()


    if current.time-lastM5.time>=5*60:
        return

    prelast5diff = prelastM5.j-prelastM5.k
    pre2last5diff = pre2lastM5.j - pre2lastM5.k

    prelast1diff = lastm1.j-lastm1.k
    pre2last1diff = prelastm1.j - prelastm1.k

    prelast15diff = prelastM15.j - prelastM15.k
    pre2last15diff = pre2lastM15.j - pre2lastM15.k


    pricelogging.info("time=%s,price=%s,preM1=%s,pre2M1=%s,preM5=%s,pre2M=%s,preM15=%s,pre2M15=%s" % (time.ctime(current.time),current.close,prelast1diff,pre2last1diff,prelast5diff,pre2last5diff,prelast15diff,pre2last15diff))

    pricelogging.info("spec=%s,5down=%s,pre2kdj=%s,prekdj=%s,curkdj=%s,up15=%s,up5=%s" % (spec,stock5Min.touchDownRange(0,4),pre2last5diff,prelast5diff,lastM5.j-lastM5.k,up15,up5))

    pricelogging.info("15downToUP=%s,kline=%s,prelast=%s,pre2last=%s" % (stock15Min.downToUp(),stock15Min.findDownKline(),prelast15diff,pre2last15diff))


    def pos(kk):
        if kk.downToUp() and kk.upmiddle(kk.findDownKline().time)==True:
            return 2
        elif kk.downToUp() and kk.upmiddle(kk.findDownKline().time)==False:
            return 1
        elif kk.downToUp()==False and kk.downmiddle(kk.findUpKline().time)==False:
            return 3
        elif kk.downToUp()==False and kk.downmiddle(kk.findUpKline().time)==True:
            return 4

    k1pos = pos(stock1Min)
    k5pos = pos(stock5Min)
    k15pos = pos(stock15Min)

    pricelogging.info("bpri=%s,time=%s,price=%s,preM1=%s,pre2M1=%s,preM5=%s,pre2M=%s,preM15=%s,pre2M15=%s,k1=%s,k5=%s,k15=%s" % (buyPrice1,time.ctime(current.time),current.close,prelast1diff,pre2last1diff,prelast5diff,pre2last5diff,prelast15diff,pre2last15diff,k1pos,k5pos,k15pos))

    if buyPrice1==None:
        if (k5pos == 1  or k5pos == 4) and prelast5diff<0 and prelast5diff > pre2last5diff and prelastM5.close>pre2lastM5.close:
            if ((prelast1diff>0 and pre2last1diff<0) or (prelast1diff>0 and prelast1diff>pre2last1diff)) and (k1pos==1 or k1pos==4):
                buy1Time = current.time
                buy2Time = lastM5.time
                buyPrice1 = current.close
                kk1pos = k1pos
                kk5pos = k5pos
                kk15pos = k15pos
                spec = 1
                pricelogging.info("tbuy1-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
        elif k5pos==1 and (prelast5diff>0 and pre2last5diff>0):
            if ((prelast1diff>0 and pre2last1diff<0) or (prelast1diff>0 and prelast1diff>pre2last1diff)) and (k1pos==1 or k1pos==4) and stock1Min.findLastKDJCrossKlineCount(2)>3:
                buy1Time = current.time
                buy2Time = lastM5.time
                buyPrice1 = current.close
                kk1pos = k1pos
                kk5pos = k5pos
                kk15pos = k15pos
                spec = 32
                pricelogging.info("tbuy32-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
        elif k5pos==1 and (prelast5diff>0 and pre2last5diff<0):
            if ((prelast1diff>0 and pre2last1diff<0) or (prelast1diff>0 and prelast1diff>pre2last1diff)) and stock1Min.findLastKDJCrossKlineCount(2)>3:
                buy1Time = current.time
                buy2Time = lastM5.time
                buyPrice1 = current.close
                kk1pos = k1pos
                kk5pos = k5pos
                kk15pos = k15pos
                spec = 34
                pricelogging.info("tbuy34-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
        elif (k5pos == 1  or k5pos == 4) and prelast5diff>0 and prelast5diff > pre2last5diff and prelastM5.close>pre2lastM5.close:
            if ((prelast1diff>0 and pre2last1diff<0) or (prelast1diff>0 and prelast1diff>pre2last1diff)) and (k1pos==1 or k1pos==4):
                buy1Time = current.time
                buy2Time = lastM5.time
                buyPrice1 = current.close
                kk1pos = k1pos
                kk5pos = k5pos
                kk15pos = k15pos
                spec = 21
                pricelogging.info("tbuy21-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
        elif k5pos ==2 and prelast5diff>0 and pre2last5diff > 0:
            if prelast1diff>0 and pre2last1diff<0 and (k1pos==1 or k1pos==4):
                buy1Time = current.time
                buy2Time = lastM5.time
                buyPrice1 = current.close
                kk1pos = k1pos
                kk5pos = k5pos
                kk15pos = k15pos
                spec = 22
                pricelogging.info("tbuy22-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
        elif k5pos == 3 and (k15pos == 2 or k15pos==1) and lastM15.j-lastM15.k>0 and prelast5diff > pre2last5diff:
            if prelast1diff>0 and pre2last1diff<0 and (k1pos==1 or k1pos==4):
                buy1Time = current.time
                buy2Time = lastM5.time
                buyPrice1 = current.close
                kk1pos = k1pos
                kk5pos = k5pos
                kk15pos = k15pos
                spec = 24
                pricelogging.info("tbuy24-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
        elif k5pos==1 and ((pre2last5diff<0 and prelast5diff>0 and prelastM5.close > pre2lastM5.close)):
            buy1Time = current.time
            buy2Time = lastM5.time
            buyPrice1 = current.close
            kk1pos = k1pos
            kk5pos = k5pos
            kk15pos = k15pos
            spec = 25
            pricelogging.info("tbuy25-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
    if buyPrice1!=None:
        if lastM5.time-buy2Time==5*60 and prelast5diff<pre2last5diff and (spec==1):
            pricelogging.info("tbuy2-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buy1Time = None
            buy2Time = None
            buyPrice1 = None
            kk1pos = None
            kk5pos = None
            kk15pos = None
            spec = None
        elif stock1Min.touchMiddleSell() and spec==1:
            if stock5Min.downToUp() and prelast5diff>pre2last5diff:
                return

            pricelogging.info("tbuy38-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buy1Time = None
            buy2Time = None
            buyPrice1 = None
            kk1pos = None
            kk5pos = None
            kk15pos = None
            spec = None
        elif stock1Min.touchUpSell():
            if current.time - buy1Time<4:
                pass
            elif buyPrice1 > current.close:
                return

            if stock5Min.downToUp() and prelast5diff>pre2last5diff:
                return

            pricelogging.info("tbuy3-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buy1Time = None
            buy2Time = None
            buyPrice1 = None
            kk1pos = None
            kk5pos = None
            kk15pos = None
            spec = None

        elif current.j-current.k<0:
            if spec ==1 and kk5pos==4 and (kk15pos==3 or kk15pos==4) :
                pass
            else:
                if buyPrice1 > current.close:
                    return

            if stock5Min.downToUp() and prelast5diff>pre2last5diff:
                return

            pricelogging.info("tbuy4-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buy1Time = None
            buy2Time = None
            buyPrice1 = None
            kk1pos = None
            kk5pos = None
            kk15pos = None
            spec = None
        elif lastM5.j-lastM5.k<0 and stock5Min.countCross2(buy2Time)==1:
            pricelogging.info("tbuy41-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buy1Time = None
            buy2Time = None
            buyPrice1 = None
            kk1pos = None
            kk5pos = None
            kk15pos = None
            spec = None


def go5():
    global buyPrice1,buyPrice2,bidsList,asksList,buy1Time,buy2Time,buyTriggerTime,buyPrice3,downToUp,upToDown,middleToUp,spec,xspec,sellSpec,xbuy,xkdj,up15,up5,kk1pos,kk5pos,kk15pos
    m5up,m5down,m5next = stock5Min.forecastClose()
    m1up,m1down,m1next = stock1Min.forecastClose()
    lastM5 = stock5Min.lastKline()
    prelastM5 = stock5Min.preLastKline()
    pre2lastM5 = stock5Min.pre2LastKline()
    current = stock1Min.lastKline()
    lastm1 = stock1Min.preLastKline()
    prelastm1 = stock1Min.pre2LastKline()
    lastM15 = stock15Min.lastKline()

    lastM15 = stock15Min.lastKline()
    prelastM15 = stock15Min.preLastKline()
    pre2lastM15 = stock15Min.pre2LastKline()


    if current.time-lastM5.time>=5*60:
        return

    prelast5diff = prelastM5.j-prelastM5.k
    pre2last5diff = pre2lastM5.j - pre2lastM5.k

    prelast1diff = lastm1.j-lastm1.k
    pre2last1diff = prelastm1.j - prelastm1.k

    prelast15diff = prelastM15.j - prelastM15.k
    pre2last15diff = pre2lastM15.j - pre2lastM15.k

    pricelogging.info("time=%s,price=%s,preM1=%s,pre2M1=%s,preM5=%s,pre2M=%s,preM15=%s,pre2M15=%s,m5up=%s,m1up=%s,m5zero=%s,m1zero=%s" % \
                      (time.ctime(current.time),current.close,prelast1diff,pre2last1diff,prelast5diff,pre2last5diff,prelast15diff,pre2last15diff,m5up,m1up,m5down,m1down))

    def pos(kk):
        if kk.downToUp() and kk.upmiddle(kk.findDownKline().time)==True:
            return 2
        elif kk.downToUp() and kk.upmiddle(kk.findDownKline().time)==False:
            return 1
        elif kk.downToUp()==False and kk.downmiddle(kk.findUpKline().time)==False:
            return 3
        elif kk.downToUp()==False and kk.downmiddle(kk.findUpKline().time)==True:
            return 4

    k1pos = pos(stock1Min)
    k5pos = pos(stock5Min)
    k15pos = pos(stock15Min)

    pricelogging.info("bpri=%s,time=%s,price=%s,preM1=%s,pre2M1=%s,preM5=%s,pre2M=%s,preM15=%s,pre2M15=%s,k1=%s,k5=%s,k15=%s" % (buyPrice1,time.ctime(current.time),current.close,prelast1diff,pre2last1diff,prelast5diff,pre2last5diff,prelast15diff,pre2last15diff,k1pos,k5pos,k15pos))

    if buyPrice1==None and prelast1diff > pre2last1diff and  pre2last1diff<0 and lastm1.macd > prelastm1.macd :
        #chaomai

        #if lastM5.j > 80:
        #    pricelogging.info("disable tbuy 5Min %s " % time.ctime(current.time))
        #    return

        if k5pos==3 and stock5Min.findIsKdjUp80(stock5Min.findKDJKline().time)>0 and prelast5diff>0 and pre2last5diff>0 and pre2last5diff>prelast5diff:
            pricelogging.info("disable tbuy 5kdj-1 %s ,-kdj=%s,-kdjcount=%s" % (time.ctime(current.time),time.ctime(stock5Min.findKDJKline().time),stock5Min.findIsKdjUp80(stock5Min.findKDJKline().time)))
            return

        if prelast5diff<0 and pre2last5diff>0 :
            if not ((prelastM5.macd<0 and pre2lastM5.macd <0 and prelastM5.macd > pre2lastM5.macd and lastM15.macd>0) or \
                            (prelastM5.macd>0 and pre2lastM5.macd>0 and pre2lastM5.macd<prelastM5.macd and lastM5.macd>0) ):
                pricelogging.info("disable tbuy 5kdj-2 %s" % time.ctime(current.time))
                return

        if prelast5diff>0 and pre2last5diff>0 and pre2last5diff>prelast5diff and prelast5diff<8:
            if not ((prelastM5.macd<0 and pre2lastM5.macd <0 and prelastM5.macd > pre2lastM5.macd and lastM15.macd>0) or \
                            (prelastM5.macd>0 and pre2lastM5.macd>0 and pre2lastM5.macd<prelastM5.macd and lastM5.macd>0) ):
                pricelogging.info("disable tbuy 5kdj-3 %s " % time.ctime(current.time))
                return

        if prelast5diff>0 and pre2last5diff>0 and lastM5.j - lastM5.k<8:
            if not ((prelastM5.macd<0 and pre2lastM5.macd <0 and prelastM5.macd > pre2lastM5.macd and lastM15.macd>0) or \
                            (prelastM5.macd>0 and pre2lastM5.macd>0 and pre2lastM5.macd<prelastM5.macd and lastM5.macd>0) ):
                pricelogging.info("disable tbuy 5kdj-4 %s " % time.ctime(current.time))
                return

        if prelastM5.macd<0 and  pre2lastM5.macd>0:
            pricelogging.info("disable tbuy 5macd %s " % time.ctime(current.time))
            return

        if prelastM5.macd<0 and pre2lastM5.macd<0 and prelastM5.macd<pre2lastM5.macd:
            pricelogging.info("disable tbuy down 5macd1 %s " % time.ctime(current.time))
            return

        if stock1Min.touchDown():
            pricelogging.info("touchDown tbuy 1Min")

        if current.macd < lastm1.macd:
            pricelogging.info("disable macd 1Min")
            return

        buy1Time = current.time
        buy2Time = lastM5.time
        buyPrice1 = current.open
        kk1pos = k1pos
        kk5pos = k5pos
        kk15pos = k15pos
        spec = 1
        pricelogging.info("tbuyb1-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (stock1Min.lastKline().open,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))

    if buyPrice1!=None and prelast1diff+4 < pre2last1diff and pre2last1diff>0 and lastm1.macd <= prelastm1.macd:
        if stock1Min.downToUp()==False and stock1Min.lastKline().open-buyPrice1>0:
            if stock5Min.downToUp()==True and ( (lastM5.macd > prelastM5.macd) or lastM5.j-lastM5.k>prelast5diff) and lastM5.j<80 and stock1Min.lastKline().open-buyPrice1<(lastm1.up - stock1Min.lastKline().open)/2:
                pricelogging.info("disable tbuy101 sell %s " % time.ctime(current.time))
                return
            if lastM5.macd>0 and stock1Min.lastKline().open-buyPrice1<1:
                return

            pricelogging.info("tbuyb48-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().open,(stock1Min.lastKline().open-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = None
            return

        if current.j>80 or (stock1Min.findIsKdjUp80(stock1Min.findKDJKline().time)>0 and prelast1diff>0):
            if stock5Min.downToUp()==True and ( (lastM5.macd > prelastM5.macd) or lastM5.j-lastM5.k>prelast5diff) and lastM5.j<80 and stock1Min.lastKline().open-buyPrice1<(lastm1.up - stock1Min.lastKline().open)/2:
                return
            if lastM5.macd>0 and stock1Min.lastKline().open-buyPrice1<1:
                return
            pricelogging.info("tbuyb28-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().open,(stock1Min.lastKline().open-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = None
            return

        if lastM5.macd <0 and prelastM5.macd > 0:
            pricelogging.info("tbuyb18-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().open,(stock1Min.lastKline().open-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = None
            return

        if lastM5.macd<0 and stock1Min.touchMiddle() and current.j-current.k < prelast1diff:
            if stock5Min.downToUp()==True and ( (lastM5.macd > prelastM5.macd) or lastM5.j-lastM5.k>prelast5diff) and lastM5.j<80 and stock1Min.lastKline().open-buyPrice1<(lastm1.up - stock1Min.lastKline().open)/2:
                pricelogging.info("disable tbuy100 sell %s " % time.ctime(current.time))
                return
            pricelogging.info("tbuyb18-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().open,(stock1Min.lastKline().open-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = None
            return

        if stock1Min.lastKline().open-buyPrice1 < 1:
            if lastm1.macd>0:
                pricelogging.info("disable tbuy sell %s " % time.ctime(current.time))
                return

        if current.macd > lastm1.macd:
            pricelogging.info("disable macd sell 1Min")
            return

        pricelogging.info("tbuyb38-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().open,(stock1Min.lastKline().open-buyPrice1),time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = None


def go6():
    global buyPrice1,buyPrice2,bidsList,asksList,buy1Time,buy2Time,buyTriggerTime,buyPrice3,downToUp,upToDown,middleToUp,spec,xspec,sellSpec,xbuy,xkdj,up15,up5,kk1pos,kk5pos,kk15pos
    m5up,m5down,m5next = stock5Min.forecastClose()
    m1up,m1down,m1next = stock1Min.forecastClose()
    lastM5 = stock5Min.lastKline()
    prelastM5 = stock5Min.preLastKline()
    pre2lastM5 = stock5Min.pre2LastKline()
    current = stock1Min.lastKline()
    lastm1 = stock1Min.preLastKline()
    prelastm1 = stock1Min.pre2LastKline()
    lastM15 = stock15Min.lastKline()

    lastM15 = stock15Min.lastKline()
    prelastM15 = stock15Min.preLastKline()
    pre2lastM15 = stock15Min.pre2LastKline()


    if current.time-lastM5.time>=5*60:
        return

    prelast5diff = prelastM5.j-prelastM5.k
    pre2last5diff = pre2lastM5.j - pre2lastM5.k

    prelast1diff = lastm1.j-lastm1.k
    pre2last1diff = prelastm1.j - prelastm1.k

    prelast15diff = prelastM15.j - prelastM15.k
    pre2last15diff = pre2lastM15.j - pre2lastM15.k

    pricelogging.info("time=%s,price=%s,1j=%s,1k=%s,5j=%s,5k=%s,15j=%s,15k=%s,1macd=%s,5macd=%s,15macd=%s" % \
                      (time.ctime(current.time),current.close,lastm1.j,lastm1.k,prelastM5.j,prelastM5.k,prelastM15.j,prelastM15.k,lastm1.macd,prelastM5.macd,prelastM15.macd))

    def pos(kk):
        if kk.downToUp() and kk.upmiddle(kk.findDownKline().time)==True:
            return 2
        elif kk.downToUp() and kk.upmiddle(kk.findDownKline().time)==False:
            return 1
        elif kk.downToUp()==False and kk.downmiddle(kk.findUpKline().time)==False:
            return 3
        elif kk.downToUp()==False and kk.downmiddle(kk.findUpKline().time)==True:
            return 4

    k1pos = pos(stock1Min)
    k5pos = pos(stock5Min)
    k15pos = pos(stock15Min)

    pricelogging.info("bpri=%s,time=%s,price=%s,preM1=%s,pre2M1=%s,preM5=%s,pre2M=%s,preM15=%s,pre2M15=%s,k1=%s,k5=%s,k15=%s" % (buyPrice1,time.ctime(current.time),current.close,prelast1diff,pre2last1diff,prelast5diff,pre2last5diff,prelast15diff,pre2last15diff,k1pos,k5pos,k15pos))


    if buyPrice1==None and (prelast1diff > pre2last1diff and pre2last1diff<5) and lastm1.j>prelastm1.j and abs(lastm1.j-prelastm1.j)>5 and lastm1.macd > prelastm1.macd and abs(lastm1.macd-prelastm1.macd)>0.03:
        #chaomai
        if lastM5.macd<prelastM5.macd and prelast5diff < pre2last5diff and lastM5.j < prelastM5.j:
            pricelogging.info("disable tbuyi900 %s",time.ctime(current.time))
            return

        if abs(current.close - lastm1.close)>10 and lastM15.j<prelastM15.j:
            pricelogging.info("disable tbuyi901 %s",time.ctime(current.time))
            return

        #if lastM5.j > 80:
        #    pricelogging.info("disable tbuy 5Min %s " % time.ctime(current.time))
        #    return
        if stock5Min.findIsKdjUp80(stock5Min.findKDJKline().time)<=0 and stock1Min.findIsKdjUp80(stock1Min.findKDJKline().time)<=0 and current.j<80 and prelastM5.macd>pre2lastM5.macd and lastM5.j>prelastM5.j and lastM5.j<80 and stock5Min.touchDown():
            buy1Time = current.time
            buy2Time = lastM5.time
            buyPrice1 = current.open
            kk1pos = k1pos
            kk5pos = k5pos
            kk15pos = k15pos
            spec = 2
            pricelogging.info("tbuyb2-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (stock1Min.lastKline().open,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
            return

        if abs(prelastm1.j-lastm1.j)<5 and (stock1Min.touchMiddle() or (current.close<current.boll and current.boll-current.close>current.close-current.bn)):
            pricelogging.info("disable tbuy 1min kdj.j %s" % (time.ctime(current.time)))
            return

        if stock5Min.findIsKdjUp80(stock5Min.findKDJKline().time)>0 and prelast5diff>0 and pre2last5diff>0 and pre2last5diff>prelast5diff:
            pricelogging.info("disable tbuy 5kdj-1 %s ,-kdj=%s,-kdjcount=%s" % (time.ctime(current.time),time.ctime(stock5Min.findKDJKline().time),stock5Min.findIsKdjUp80(stock5Min.findKDJKline().time)))
            return

        if prelast5diff<0 and pre2last5diff>0 :
            if not ((prelastM5.macd<0 and pre2lastM5.macd <0 and prelastM5.macd > pre2lastM5.macd and lastM15.macd>0) or \
                            (prelastM5.macd>0 and pre2lastM5.macd>0 and pre2lastM5.macd<prelastM5.macd and lastM5.macd>0) ):
                pricelogging.info("disable tbuy 5kdj-2 %s" % time.ctime(current.time))
                return

        if prelast5diff>0 and pre2last5diff>0 and pre2last5diff>prelast5diff and prelast5diff<8:
            if not ((prelastM5.macd<0 and pre2lastM5.macd <0 and prelastM5.macd > pre2lastM5.macd and lastM15.macd>0) or \
                            (prelastM5.macd>0 and pre2lastM5.macd>0 and pre2lastM5.macd<prelastM5.macd and lastM5.macd>0) ):
                pricelogging.info("disable tbuy 5kdj-3 %s " % time.ctime(current.time))
                return

        if prelast5diff>0 and pre2last5diff>0 and lastM5.j - lastM5.k<8:
            if not ((prelastM5.macd<0 and pre2lastM5.macd <0 and prelastM5.macd > pre2lastM5.macd and lastM15.macd>0) or \
                            (prelastM5.macd>0 and pre2lastM5.macd>0 and pre2lastM5.macd<prelastM5.macd and lastM5.macd>0) ):
                pricelogging.info("disable tbuy 5kdj-4 %s " % time.ctime(current.time))
                return

        if prelastM5.macd<0 and  pre2lastM5.macd>0:
            pricelogging.info("disable tbuy 5macd %s " % time.ctime(current.time))
            return

        if prelastM5.macd<0 and pre2lastM5.macd<0 and prelastM5.macd<pre2lastM5.macd:
            if not (stock1Min.touchDown() and stock5Min.touchDown() and (prelastM5.j<20 or pre2lastM5.j<20) and lastM5.j>prelastM5.j):
                pricelogging.info("disable tbuy down 5macd1 %s " % time.ctime(current.time))
                return

        if stock1Min.touchDown():
            pricelogging.info("touchDown tbuy 1Min")

        if current.macd < lastm1.macd:
            pricelogging.info("disable macd 1Min")
            return

        buy1Time = current.time
        buy2Time = lastM5.time
        buyPrice1 = current.open
        kk1pos = k1pos
        kk5pos = k5pos
        kk15pos = k15pos
        spec = 1
        pricelogging.info("tbuyb1-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (stock1Min.lastKline().open,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))


    if buyPrice1!=None:

        if current.up-current.dn<3.5 and (stock5Min.findIsKdjUp80(stock5Min.findKDJKline().time)<=0 or (stock5Min.findIsKdjUp80(stock5Min.findKDJKline().time)>0 and lastM5.j>prelastM5.j)) and lastM5.j-lastM5.k>0 and lastM15.j-lastM15.k>5 and stock15Min.countCross(buy2Time)<=1 and stock5Min.countCross(buy2Time)<=1:
            pricelogging.info("disable tbuy153 sell up5 %s " % time.ctime(current.time))
            return

        if lastM5.macd > prelastM5.macd and spec==2:
            pricelogging.info("disable tbuy103 sell %s " % time.ctime(current.time))
            return

        if stock1Min.findIsKdjUp80(stock1Min.findKDJKline().time)>0 and abs(current.j-lastm1.j)<5 and lastm1.macd < prelastm1.macd and abs(lastm1.macd-prelastm1.macd)>0.03:
            pricelogging.info("tbuyb148-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().open,(stock1Min.lastKline().open-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = None
            return
        if stock1Min.findIsKdjUp80(stock1Min.findKDJKline().time)>0 and stock1Min.touchUp() and current.j < lastm1.j and (lastm1.macd <= prelastm1.macd or abs(lastm1.macd-prelastm1.macd)<=0.03 ):
            pricelogging.info("tbuyb149-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().open,(stock1Min.lastKline().open-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = None
            return

    if buyPrice1!=None and prelast1diff < pre2last1diff and lastm1.macd <= prelastm1.macd and abs(lastm1.macd-prelastm1.macd)>0.03:

        if stock1Min.downToUp()==False and stock1Min.lastKline().open-buyPrice1>0:
            if stock5Min.downToUp()==True and ( (lastM5.macd > prelastM5.macd) or lastM5.j-lastM5.k>prelast5diff) and lastM5.j<80 and stock1Min.lastKline().open-buyPrice1<(lastm1.up - stock1Min.lastKline().open)/2:
                pricelogging.info("disable tbuy101 sell %s " % time.ctime(current.time))
                return
            if lastM5.macd>0 and stock1Min.lastKline().open-buyPrice1<1:
                return

            pricelogging.info("tbuyb48-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().open,(stock1Min.lastKline().open-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = None
            return

        if current.j>80 or (stock1Min.findIsKdjUp80(stock1Min.findKDJKline().time)>0 and prelast1diff>0):
            if stock5Min.downToUp()==True and ( (lastM5.macd > prelastM5.macd) or lastM5.j-lastM5.k>prelast5diff) and lastM5.j<80 and stock1Min.lastKline().open-buyPrice1<(lastm1.up - stock1Min.lastKline().open)/2:
                return
            if lastM5.macd>0 and stock1Min.lastKline().open-buyPrice1<1:
                return
            pricelogging.info("tbuyb28-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().open,(stock1Min.lastKline().open-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = None
            return

        if lastM5.macd <0 and prelastM5.macd > 0:
            pricelogging.info("tbuyb18-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().open,(stock1Min.lastKline().open-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = None
            return

        if lastM5.macd<0 and stock1Min.touchMiddle() and (current.j-current.k < prelast1diff or (current.j-prelastm1.j<6 and current.close < current.open)):
            if stock5Min.downToUp()==True and ( (lastM5.macd > prelastM5.macd) or lastM5.j-lastM5.k>prelast5diff) and lastM5.j<80 and stock1Min.lastKline().open-buyPrice1<(lastm1.up - stock1Min.lastKline().open)/2:
                pricelogging.info("disable tbuy100 sell %s " % time.ctime(current.time))
                return
            pricelogging.info("tbuyb18-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().open,(stock1Min.lastKline().open-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = None
            return

        if stock1Min.lastKline().open-buyPrice1 < 1:
            if lastm1.macd>0:
                pricelogging.info("disable tbuy sell %s " % time.ctime(current.time))
                return

        if current.macd > lastm1.macd:
            pricelogging.info("disable macd sell 1Min")
            return

        pricelogging.info("tbuyb38-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().open,(stock1Min.lastKline().open-buyPrice1),time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = None
        return
    if buy2Time!=None:
        pricelogging.info("last5Time=%s,buy2Time=%s,diff = %s" %  (time.ctime(lastM5.time),time.ctime(buy2Time),current.time-buy2Time))
    if buyPrice1!=None and current.time-buy2Time == 5*60 and lastM5.j<prelastM5.j and lastM5.j-lastM5.k<0:
        pricelogging.info("tbuybi538-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().open,(stock1Min.lastKline().open-buyPrice1),time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = None
        return


def go7():
    global buyPrice1,buyPrice2,bidsList,asksList,buy1Time,buy2Time,buyTriggerTime,buyPrice3,downToUp,upToDown,middleToUp,spec,xspec,sellSpec,xbuy,xkdj,up15,up5,kk1pos,kk5pos,kk15pos
    m5up,m5down,m5next = stock5Min.forecastClose()
    m1up,m1down,m1next = stock1Min.forecastClose()
    lastM5 = stock5Min.lastKline()
    prelastM5 = stock5Min.preLastKline()
    pre2lastM5 = stock5Min.pre2LastKline()
    current = stock1Min.lastKline()
    lastm1 = stock1Min.preLastKline()
    prelastm1 = stock1Min.pre2LastKline()
    lastM15 = stock15Min.lastKline()

    lastM15 = stock15Min.lastKline()
    prelastM15 = stock15Min.preLastKline()
    pre2lastM15 = stock15Min.pre2LastKline()


    if current.time-lastM5.time>=5*60:
        return

    prelast5diff = prelastM5.j-prelastM5.k
    pre2last5diff = pre2lastM5.j - pre2lastM5.k

    prelast1diff = lastm1.j-lastm1.k
    pre2last1diff = prelastm1.j - prelastm1.k

    prelast15diff = prelastM15.j - prelastM15.k
    pre2last15diff = pre2lastM15.j - pre2lastM15.k

    pricelogging.info("time=%s,price=%s,1j=%s,1k=%s,5j=%s,5k=%s,15j=%s,15k=%s,1macd=%s,5macd=%s,15macd=%s" % \
                      (time.ctime(current.time),current.close,lastm1.j,lastm1.k,prelastM5.j,prelastM5.k,prelastM15.j,prelastM15.k,lastm1.macd,prelastM5.macd,prelastM15.macd))

    def pos(kk):
        if kk.downToUp() and kk.upmiddle(kk.findDownKline().time)==True:
            return 2
        elif kk.downToUp() and kk.upmiddle(kk.findDownKline().time)==False:
            return 1
        elif kk.downToUp()==False and kk.downmiddle(kk.findUpKline().time)==False:
            return 3
        elif kk.downToUp()==False and kk.downmiddle(kk.findUpKline().time)==True:
            return 4

    k1pos = pos(stock1Min)
    k5pos = pos(stock5Min)
    k15pos = pos(stock15Min)

    pricelogging.info("bpri=%s,time=%s,price=%s,preM1=%s,pre2M1=%s,preM5=%s,pre2M=%s,preM15=%s,pre2M15=%s,k1=%s,k5=%s,k15=%s" % (buyPrice1,time.ctime(current.time),current.close,prelast1diff,pre2last1diff,prelast5diff,pre2last5diff,prelast15diff,pre2last15diff,k1pos,k5pos,k15pos))

    if buyPrice1==None:
        if lastM5.j<prelastM5.j and lastM5.j-lastM5.k<0 and lastM5.j>40 and stock5Min.downToUp()==False:
            pricelogging.info("disable tbuy sell %s " % time.ctime(current.time))
            return
        if lastM5.j-lastM5.k>0 and stock5Min.kdjUpDontTouchMaxKline()!=None and stock5Min.kdjUpDontTouchMaxKline().low<lastM5.boll and stock5Min.kdjUpDontTouchMaxKline().high < lastM5.up and stock5Min.downToUp()==False and \
                        lastM5.j<prelastM5.j:
            pricelogging.info("disable tbuy sell12 %s " % time.ctime(current.time))
            return

        if prelastm1.j<20 and lastm1.j > prelastm1.j and abs(lastm1.j-prelastm1.j) > 19:
            buy1Time = current.time
            buy2Time = lastM5.time
            buyPrice1 = current.open
            kk1pos = k1pos
            kk5pos = k5pos
            kk15pos = k15pos
            spec=1
            pricelogging.info("tbuyb2-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (stock1Min.lastKline().open,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
            return

        if prelastm1.j<20 and lastm1.j > prelastm1.j and lastm1.j-lastm1.k>0:
            buy1Time = current.time
            buy2Time = lastM5.time
            buyPrice1 = current.open
            kk1pos = k1pos
            kk5pos = k5pos
            kk15pos = k15pos
            spec=1
            pricelogging.info("tbuyb4-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (stock1Min.lastKline().open,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
            return

        if stock1Min.preMyLastKline(3).j<20 and prelastm1.j>stock1Min.preMyLastKline(3).j and lastm1.j > prelastm1.j:
            buy1Time = current.time
            buy2Time = lastM5.time
            buyPrice1 = current.open
            kk1pos = k1pos
            kk5pos = k5pos
            kk15pos = k15pos
            spec=1
            pricelogging.info("tbuyb3-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (stock1Min.lastKline().open,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
            return



    if buyPrice1!=None:
        if stock1Min.lastKline().open - buyPrice1 < -15:
            pricelogging.info("tbuybi548-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().open,(stock1Min.lastKline().open-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = None
            return

        if spec==2:
            if lastM5.j<prelastM5.j:
                pricelogging.info("tbuybi558-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().open,(stock1Min.lastKline().open-buyPrice1),time.ctime(stock1Min.lastKline().time)))
                buyPrice1 = None
                return

        if spec!=2 and prelastm1.j>80 and lastm1.j < prelastm1.j:
            if stock1Min.lastKline().open - buyPrice1<0 and ((lastM5.j-lastM5.k>0) or lastM5.j>prelastM5.j):
                spec = 2
                return
            pricelogging.info("tbuybi538-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().open,(stock1Min.lastKline().open-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = None
            if lastM5.j>prelastM5.j:
                spec=2
            return

    if buyPrice1==None and spec==2:
        if lastm1.j > prelastm1.j and lastM5.j>prelastM5.j and lastM5.j<80:
            buy1Time = current.time
            buy2Time = lastM5.time
            buyPrice1 = current.open
            kk1pos = k1pos
            kk5pos = k5pos
            kk15pos = k15pos
            spec=2
            pricelogging.info("tbuyb31-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (stock1Min.lastKline().open,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
            return


def go8():
    global buyPrice1,buyPrice2,bidsList,asksList,buy1Time,buy2Time,buyTriggerTime,buyPrice3,downToUp,upToDown,middleToUp,spec,xspec,sellSpec,xbuy,xkdj,up15,up5,kk1pos,kk5pos,kk15pos
    m5up,m5down,m5next = stock5Min.forecastClose()
    m1up,m1down,m1next = stock1Min.forecastClose()
    lastM5 = stock5Min.lastKline()
    prelastM5 = stock5Min.preLastKline()
    pre2lastM5 = stock5Min.pre2LastKline()
    current = stock1Min.lastKline()
    lastm1 = stock1Min.preLastKline()
    prelastm1 = stock1Min.pre2LastKline()
    lastM15 = stock15Min.lastKline()

    lastM15 = stock15Min.lastKline()
    prelastM15 = stock15Min.preLastKline()
    pre2lastM15 = stock15Min.pre2LastKline()

    if current.time-lastM5.time>=5*60:
        return

    prelast5diff = prelastM5.j-prelastM5.k
    pre2last5diff = pre2lastM5.j - pre2lastM5.k

    prelast1diff = lastm1.j-lastm1.k
    pre2last1diff = prelastm1.j - prelastm1.k

    prelast15diff = prelastM15.j - prelastM15.k
    pre2last15diff = pre2lastM15.j - pre2lastM15.k

    pricelogging.info("time=%s,price=%s,1j=%s,1k=%s,5j=%s,5k=%s,15j=%s,15k=%s,1macd=%s,5macd=%s,15macd=%s" % \
                      (time.ctime(current.time),current.close,lastm1.j,lastm1.k,prelastM5.j,prelastM5.k,prelastM15.j,prelastM15.k,lastm1.macd,prelastM5.macd,prelastM15.macd))

    def pos(kk):
        if kk.downToUp() and kk.upmiddle(kk.findDownKline().time)==True:
            return 2
        elif kk.downToUp() and kk.upmiddle(kk.findDownKline().time)==False:
            return 1
        elif kk.downToUp()==False and kk.downmiddle(kk.findUpKline().time)==False:
            return 3
        elif kk.downToUp()==False and kk.downmiddle(kk.findUpKline().time)==True:
            return 4

    k1pos = pos(stock1Min)
    k5pos = pos(stock5Min)
    k15pos = pos(stock15Min)

    pricelogging.info("bpri=%s,time=%s,price=%s,preM1=%s,pre2M1=%s,preM5=%s,pre2M=%s,preM15=%s,pre2M15=%s,k1=%s,k5=%s,k15=%s" % (buyPrice1,time.ctime(current.time),current.close,prelast1diff,pre2last1diff,prelast5diff,pre2last5diff,prelast15diff,pre2last15diff,k1pos,k5pos,k15pos))

    if buyTriggerTime==None:
        buyTriggerTime = current.time
    elif buyTriggerTime==current.time:
        return
    else:
        buyTriggerTime = current.time

    if buyPrice1==None:
        if lastM5.j<prelastM5.j and lastM5.j-lastM5.k<0 and lastM5.j>40 and stock5Min.downToUp()==False:
            pricelogging.info("disable tbuy sell %s " % time.ctime(current.time))
            return
        if lastM5.j-lastM5.k>0 and stock5Min.kdjUpDontTouchMaxKline()!=None and stock5Min.kdjUpDontTouchMaxKline().low<lastM5.boll and stock5Min.kdjUpDontTouchMaxKline().high < lastM5.up and stock5Min.downToUp()==False and \
                        lastM5.j<prelastM5.j:
            pricelogging.info("disable tbuy sell12 %s " % time.ctime(current.time))
            return

        if prelastm1.j<20 and lastm1.j > prelastm1.j and abs(lastm1.j-prelastm1.j) > 19:
            buy1Time = current.time
            buy2Time = lastM5.time
            buyPrice1 = current.close
            kk1pos = k1pos
            kk5pos = k5pos
            kk15pos = k15pos
            spec=1
            pricelogging.info("tbuyb2-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (buyPrice1,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
            return

        if prelastm1.j<20 and lastm1.j > prelastm1.j and lastm1.j-lastm1.k>0:
            buy1Time = current.time
            buy2Time = lastM5.time
            buyPrice1 = current.close
            kk1pos = k1pos
            kk5pos = k5pos
            kk15pos = k15pos
            spec=1
            pricelogging.info("tbuyb4-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (buyPrice1,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
            return

        if stock1Min.preMyLastKline(3).j<20 and prelastm1.j>stock1Min.preMyLastKline(3).j and lastm1.j > prelastm1.j:
            buy1Time = current.time
            buy2Time = lastM5.time
            buyPrice1 = current.close
            kk1pos = k1pos
            kk5pos = k5pos
            kk15pos = k15pos
            spec=1
            pricelogging.info("tbuyb3-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (buyPrice1,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
            return



    if buyPrice1!=None:
        if stock1Min.lastKline().open - buyPrice1 < -15:
            pricelogging.info("tbuybi548-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = None
            spec = None
            return

        if spec==2:
            if lastM5.j<prelastM5.j:
                pricelogging.info("tbuybi558-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
                buyPrice1 = None
                spec = None
                return

        if spec!=2 and prelastm1.j>80 and lastm1.j < prelastm1.j:
            if stock1Min.lastKline().open - buyPrice1<0 and ((lastM5.j-lastM5.k>0) or lastM5.j>prelastM5.j):
                spec = 2
                return
            pricelogging.info("tbuybi538-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = None
            if lastM5.j>prelastM5.j:
                spec=2
            return

    if buyPrice1==None and spec==2:
        if lastm1.j > prelastm1.j and lastM5.j>prelastM5.j and lastM5.j<80:
            buy1Time = current.time
            buy2Time = lastM5.time
            buyPrice1 = current.close
            kk1pos = k1pos
            kk5pos = k5pos
            kk15pos = k15pos
            spec=2
            pricelogging.info("tbuyb31-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
            return

def go9():
    global buyPrice1,buyPrice2,bidsList,asksList,buy1Time,buy2Time,buyTriggerTime,buyPrice3,downToUp,upToDown,middleToUp,spec,xspec,sellSpec,xbuy,xkdj,up15,up5,kk1pos,kk5pos,kk15pos
    m5up,m5down,m5next = stock5Min.forecastClose()
    m1up,m1down,m1next = stock1Min.forecastClose()
    lastM5 = stock5Min.lastKline()
    prelastM5 = stock5Min.preLastKline()
    pre2lastM5 = stock5Min.pre2LastKline()
    current = stock1Min.lastKline()
    lastm1 = stock1Min.preLastKline()
    prelastm1 = stock1Min.pre2LastKline()
    lastM15 = stock15Min.lastKline()

    lastM15 = stock15Min.lastKline()
    prelastM15 = stock15Min.preLastKline()
    pre2lastM15 = stock15Min.pre2LastKline()


    if current.time-lastM5.time>=5*60:
        return

    prelast5diff = prelastM5.j-prelastM5.k
    pre2last5diff = pre2lastM5.j - pre2lastM5.k

    prelast1diff = lastm1.j-lastm1.k
    pre2last1diff = prelastm1.j - prelastm1.k

    prelast15diff = prelastM15.j - prelastM15.k
    pre2last15diff = pre2lastM15.j - pre2lastM15.k

    pricelogging.info("time=%s,price=%s,1j=%s,1k=%s,5j=%s,5k=%s,15j=%s,15k=%s,1macd=%s,5macd=%s,15macd=%s" % \
                      (time.ctime(current.time),current.close,lastm1.j,lastm1.k,prelastM5.j,prelastM5.k,prelastM15.j,prelastM15.k,lastm1.macd,prelastM5.macd,prelastM15.macd))

    def pos(kk):
        if kk.downToUp() and kk.upmiddle(kk.findDownKline().time)==True:
            return 2
        elif kk.downToUp() and kk.upmiddle(kk.findDownKline().time)==False:
            return 1
        elif kk.downToUp()==False and kk.downmiddle(kk.findUpKline().time)==False:
            return 3
        elif kk.downToUp()==False and kk.downmiddle(kk.findUpKline().time)==True:
            return 4

    k1pos = pos(stock1Min)
    k5pos = pos(stock5Min)
    k15pos = pos(stock15Min)

    pricelogging.info("bpri=%s,time=%s,price=%s,preM1=%s,pre2M1=%s,preM5=%s,pre2M=%s,preM15=%s,pre2M15=%s,k1=%s,k5=%s,k15=%s" % (buyPrice1,time.ctime(current.time),current.close,prelast1diff,pre2last1diff,prelast5diff,pre2last5diff,prelast15diff,pre2last15diff,k1pos,k5pos,k15pos))

    if buyPrice1==None:
        if lastM15.j<prelastM15.j and lastM15.j-lastM15.k<0 and lastM15.j>40 and stock15Min.downToUp()==False:
            pricelogging.info("disable tbuy sell %s " % time.ctime(current.time))
            return
        if lastM15.j-lastM15.k>0 and stock15Min.kdjUpDontTouchMaxKline()!=None and stock15Min.kdjUpDontTouchMaxKline().low<lastM15.boll and stock15Min.kdjUpDontTouchMaxKline().high < lastM15.up and stock15Min.downToUp()==False and \
                        lastM15.j<prelastM15.j:
            pricelogging.info("disable tbuy sell12 %s " % time.ctime(current.time))
            return

        if pre2lastM5.j<20 and prelastM5.j > pre2lastM5.j and abs(prelastM5.j-pre2lastM5.j) > 19:
            buy1Time = current.time
            buy2Time = lastM5.time
            buyPrice1 = current.open
            kk1pos = k1pos
            kk5pos = k5pos
            kk15pos = k15pos
            spec=1
            pricelogging.info("tbuyb2-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (stock1Min.lastKline().open,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
            return

        if pre2lastM5.j<20 and prelastM5.j > pre2lastM5.j and prelastM5.j-prelastM5.k>0:
            buy1Time = current.time
            buy2Time = lastM5.time
            buyPrice1 = current.open
            kk1pos = k1pos
            kk5pos = k5pos
            kk15pos = k15pos
            spec=1
            pricelogging.info("tbuyb4-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (stock1Min.lastKline().open,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
            return

        if stock5Min.preMyLastKline(3).j<20 and pre2lastM5.j>stock5Min.preMyLastKline(3).j and prelastM5.j > pre2lastM5.j:
            buy1Time = current.time
            buy2Time = lastM5.time
            buyPrice1 = current.open
            kk1pos = k1pos
            kk5pos = k5pos
            kk15pos = k15pos
            spec=1
            pricelogging.info("tbuyb3-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (stock1Min.lastKline().open,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
            return



    if buyPrice1!=None:
        if stock1Min.lastKline().open - buyPrice1 < -15:
            pricelogging.info("tbuybi548-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().open,(stock1Min.lastKline().open-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = None
            return

        if spec==2:
            if lastM15.j<prelastM15.j:
                pricelogging.info("tbuybi558-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().open,(stock1Min.lastKline().open-buyPrice1),time.ctime(stock1Min.lastKline().time)))
                buyPrice1 = None
                return

        if spec!=2 and pre2lastM5.j>80 and prelastM5.j < pre2lastM5.j:
            if stock5Min.lastKline().open - buyPrice1<0 and ((lastM15.j-lastM15.k>0) or lastM15.j>prelastM15.j):
                spec = 2
                return
            pricelogging.info("tbuybi538-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().open,(stock1Min.lastKline().open-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = None
            if lastM15.j>prelastM15.j:
                spec=2
            return

    if buyPrice1==None and spec==2:
        if prelastM5.j > pre2lastM5.j and lastM15.j>prelastM15.j and lastM15.j<80:
            buy1Time = current.time
            buy2Time = lastM5.time
            buyPrice1 = current.open
            kk1pos = k1pos
            kk5pos = k5pos
            kk15pos = k15pos
            spec=2
            pricelogging.info("tbuyb31-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (stock1Min.lastKline().open,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
            return


def go10():
    global buyPrice1,buyPrice2,bidsList,asksList,buy1Time,buy2Time,buyTriggerTime,buyPrice3,downToUp,upToDown,middleToUp,spec,xspec,sellSpec,xbuy,xkdj,up15,up5,kk1pos,kk5pos,kk15pos
    m5up,m5down,m5next = stock5Min.forecastClose()
    m1up,m1down,m1next = stock1Min.forecastClose()
    lastM5 = stock5Min.lastKline()
    prelastM5 = stock5Min.preLastKline()
    pre2lastM5 = stock5Min.pre2LastKline()
    current = stock1Min.lastKline()
    lastm1 = stock1Min.preLastKline()
    prelastm1 = stock1Min.pre2LastKline()
    lastM15 = stock15Min.lastKline()

    lastM15 = stock15Min.lastKline()
    prelastM15 = stock15Min.preLastKline()
    pre2lastM15 = stock15Min.pre2LastKline()

    if current.time-lastM5.time>=5*60:
        return

    prelast5diff = prelastM5.j-prelastM5.k
    pre2last5diff = pre2lastM5.j - pre2lastM5.k

    prelast1diff = lastm1.j-lastm1.k
    pre2last1diff = prelastm1.j - prelastm1.k

    prelast15diff = prelastM15.j - prelastM15.k
    pre2last15diff = pre2lastM15.j - pre2lastM15.k

    pricelogging.info("time=%s,price=%s,1j=%s,1k=%s,5j=%s,5k=%s,15j=%s,15k=%s,1macd=%s,5macd=%s,15macd=%s" % \
                      (time.ctime(current.time),current.close,lastm1.j,lastm1.k,prelastM5.j,prelastM5.k,prelastM15.j,prelastM15.k,lastm1.macd,prelastM5.macd,prelastM15.macd))

    def pos(kk):
        if kk.downToUp() and kk.upmiddle(kk.findDownKline().time)==True:
            return 2
        elif kk.downToUp() and kk.upmiddle(kk.findDownKline().time)==False:
            return 1
        elif kk.downToUp()==False and kk.downmiddle(kk.findUpKline().time)==False:
            return 3
        elif kk.downToUp()==False and kk.downmiddle(kk.findUpKline().time)==True:
            return 4

    k1pos = pos(stock1Min)
    k5pos = pos(stock5Min)
    k15pos = pos(stock15Min)

    pricelogging.info("bpri=%s,time=%s,lastM5.j=%s,lastM5.macd=%s,m1.up=%s,m1.boll=%s,m1.down=%s,m5.up=%s,m5.boll=%s,m5.down=%s" % (buyPrice1,time.ctime(current.time),lastM5.j,lastM5.macd,
                                                                                                                                    lastm1.up,lastm1.boll,lastm1.dn,prelastM5.up,prelastM5.boll,prelastM5.dn))
    if current.time == buy1Time:
        return

    if buyPrice1==None:
        if sellSpec==True and lastM5.macd > prelastM5.macd and lastM5.j > prelastM5.j:
            pricelogging.info("disable tbuy sell End %s " % time.ctime(current.time))
            spec=2
            sellSpec = None
            if lastm1.j < prelastm1.j:
                return
            if lastm1.j<80:
                buy1Time = current.time
                buy2Time = lastM5.time
                buyPrice1 = current.close
                kk1pos = k1pos
                kk5pos = k5pos
                kk15pos = k15pos
                spec = 3
                pricelogging.info("tbuyb311-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
                return

        if sellSpec==None and lastM5.j-lastM5.k>0 and stock5Min.kdjUpDontTouchMaxKline().j>80 and lastM5.j<prelastM5.j and lastM5.macd < prelastM5.macd:
            pricelogging.info("disable tbuy sell Start %s " % time.ctime(current.time))
            sellSpec=True
            return

        if sellSpec == True:
            pricelogging.info("disable tbuy sell %s " % time.ctime(current.time))
            return

        if prelastm1.j<20 and lastm1.j > prelastm1.j and abs(lastm1.j-prelastm1.j) > 19:
            if lastM5.j<20:
                return
            if lastm1.macd<0 and lastm1.macd < prelastm1.macd:
                return

            if lastM5.j < prelastM5.j:
                return

            if lastM5.j > prelastM5.j and prelastM5.macd < 0 and lastM5.macd < prelastM5.macd:
                return

            buy1Time = current.time
            buy2Time = lastM5.time
            buyPrice1 = current.close
            kk1pos = k1pos
            kk5pos = k5pos
            kk15pos = k15pos
            spec=1
            pricelogging.info("tbuyb2-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (buyPrice1,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
            return

        if prelastm1.j<20 and lastm1.j > prelastm1.j and lastm1.j-lastm1.k>0:
            if lastM5.j<20:
                return

            if lastM5.j < prelastM5.j:
                return
            if lastM5.j > prelastM5.j and prelastM5.macd < 0 and lastM5.macd < prelastM5.macd:
                return
            buy1Time = current.time
            buy2Time = lastM5.time
            buyPrice1 = current.close
            kk1pos = k1pos
            kk5pos = k5pos
            kk15pos = k15pos
            spec=1
            pricelogging.info("tbuyb4-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (buyPrice1,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
            return

        if stock1Min.preMyLastKline(3).j<20 and prelastm1.j>stock1Min.preMyLastKline(3).j and lastm1.j > prelastm1.j:
            if lastM5.j<20:
                return

            if lastm1.macd<0 and lastm1.macd < prelastm1.macd:
                return

            if lastM5.j < prelastM5.j:
                return

            if lastM5.j > prelastM5.j and prelastM5.macd < 0 and lastM5.macd < prelastM5.macd:
                return

            buy1Time = current.time
            buy2Time = lastM5.time
            buyPrice1 = current.close
            kk1pos = k1pos
            kk5pos = k5pos
            kk15pos = k15pos
            spec=1
            pricelogging.info("tbuyb3-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (buyPrice1,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
            return


    if buyPrice1!=None:
        if spec == 3:
            if lastm1.j < prelastm1.j:
                pricelogging.info("tbuybi568-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
                buyPrice1 = None
                spec = None
            elif lastm1.j>=80:
                spec = 1;
            return

        if stock1Min.lastKline().close - buyPrice1 < -15:
            pricelogging.info("tbuybi548-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = None
            spec = None
            return

        if spec==2:
            if prelastm1.j>80 and lastm1.j < prelastm1.j and abs(lastM5.macd)<0.2 and stock1Min.lastKline().close - buyPrice1<0:
                if lastM5.j>prelastM5.j and lastM5.macd>prelastM5.macd and lastM5.j<80:
                    pass
                else:
                    pricelogging.info("tbuybi578-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
                    buyPrice1 = None
                    spec = 2
                    return
            if prelastM5.j<pre2lastM5.j:
                if prelastM5.macd>0.5 and prelastM5.macd > pre2lastM5.macd and stock1Min.lastKline().close - buyPrice1>0:
                    pricelogging.info("tbuybikk508-%s,disable,time=%s" % (buyPrice1,time.ctime(stock1Min.lastKline().time)))
                    return;

                if prelastM5.macd<-0.8 and lastM5.macd>prelastM5.macd:
                    pricelogging.info("tbuybikk548-%s,disable,time=%s" % (buyPrice1,time.ctime(stock1Min.lastKline().time)))
                    return;

                pricelogging.info("tbuybi558-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
                buyPrice1 = None
                spec = None
                return
        if spec!=2 and prelastm1.j>80 and lastm1.j < prelastm1.j:
            if lastm1.macd>prelastm1.macd and lastM5.j>prelastM5.j and lastM5.macd > prelastM5.macd:
                pricelogging.info("tbuybikk518-%s,disable,time=%s" % (buyPrice1,time.ctime(stock1Min.lastKline().time)))
                return

            if lastM5.j - lastM5.k >0 and lastM15.j > prelastM15.j and lastM15.macd > prelastM15.macd and lastM5.macd > prelastM5.macd and  lastm1.macd > 0 and stock1Min.lastKline().close - buyPrice1>0:
                pricelogging.info("tbuybikk598-%s,disable,time=%s" % (buyPrice1,time.ctime(stock1Min.lastKline().time)))
                spec = 2
                return

            if lastM5.macd < 0 and lastM5.j - lastM5.k<0:
                pricelogging.info("tbuybi568-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
                buyPrice1 = None
                return
            if stock1Min.lastKline().close - buyPrice1<0 and ((lastM5.j-lastM5.k>0) or lastM5.j>prelastM5.j):
                spec = 2
                return

            if lastM5.macd>prelastM5.macd and stock1Min.lastKline().close-buyPrice1>0:
                return

            pricelogging.info("tbuybi538-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = None
            if lastM5.j>prelastM5.j:
                spec=2
            return

        if spec==1 and lastm1.j<80 and lastm1.j < prelastm1.j and lastM5.j<prelastM5.j:
            if lastM5.j<20 and lastm1.macd>prelastm1.macd:
                return
            pricelogging.info("tbuybi668-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = None
            spec = None
            return

    if buyPrice1==None and spec==2:
        if lastm1.j > prelastm1.j and lastM5.j>prelastM5.j and lastM5.j<80 and lastm1.j<80:
            if lastM5.macd <0 and lastM5.macd<prelastM5.macd:
                return
            buy1Time = current.time
            buy2Time = lastM5.time
            buyPrice1 = current.close
            kk1pos = k1pos
            kk5pos = k5pos
            kk15pos = k15pos
            spec=2
            pricelogging.info("tbuyb31-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (stock1Min.lastKline().close,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
            return

    if buyPrice1==None and lastM5.j>prelastM5.j and (prelastM5.j<20 or lastM5.j<20) and lastM5.macd>prelastM5.macd:
        if lastM5.macd<0 and lastM5.macd < prelastM5.macd + 0.03:
            return

        if lastM5.j<20 and prelastM5.j<pre2lastM5.j:
            return

        buy1Time = current.time
        buy2Time = lastM5.time
        buyPrice1 = current.close
        kk1pos = k1pos
        kk5pos = k5pos
        kk15pos = k15pos
        spec=2
        pricelogging.info("tbuyb489-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (buyPrice1,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
        return

    if buyPrice1 == None and lastM5.j>prelastM5.j and lastM5.macd>prelastM5.macd and lastM5.macd>0.5 and lastM5.j<80 and lastM15.j-lastM15.k>0 and lastM15.macd>0.5:
        if lastM5.j<20 and prelastM5.j<pre2lastM5.j:
            return

        buy1Time = current.time
        buy2Time = lastM5.time
        buyPrice1 = current.close
        kk1pos = k1pos
        kk5pos = k5pos
        kk15pos = k15pos
        spec=2
        pricelogging.info("tbuyb4189-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (buyPrice1,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
        return
    if buyPrice1==None and lastM15.macd >0 and stock5Min.findLowestkdj()==True and lastM5.macd > prelastM5.macd and lastM5.j>prelastM5.j and lastM5.j-lastM5.k>0 and lastM5.j<80 and lastM5.high<lastM5.boll:
        if lastM5.j<20 and prelastM5.j<pre2lastM5.j:
            return

        buy1Time = current.time
        buy2Time = lastM5.time
        buyPrice1 = current.close
        kk1pos = k1pos
        kk5pos = k5pos
        kk15pos = k15pos
        spec=2
        pricelogging.info("tbuyb4489-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (buyPrice1,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
        return

    if buyPrice1==None and prelastM5.j>pre2lastM5.j and pre2lastM5.j > stock5Min.preMyLastKline(3).j and prelastM5.macd > pre2lastM5.macd and \
                    lastM5.j>prelastM5.j and lastM5.macd>prelastM5.macd and current.high < lastM5.up and lastM15.j>prelastM15.j and lastM15.macd>prelastM15.macd \
            and prelastM15.j>pre2lastM15.j and prelastM15.macd > pre2lastM15.macd and lastM5.macd>0 and lastm1.j>prelastm1.j:
        if lastM5.j<20 and prelastM5.j<pre2lastM5.j:
            return

        buy1Time = current.time
        buy2Time = lastM5.time
        buyPrice1 = current.close
        kk1pos = k1pos
        kk5pos = k5pos
        kk15pos = k15pos
        spec=2
        pricelogging.info("tbuyb4789-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (buyPrice1,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
        return



def go11():
    global buyPrice1,buyPrice2,bidsList,asksList,buy1Time,buy2Time,buyTriggerTime,buyPrice3,downToUp,upToDown,middleToUp,spec,xspec,sellSpec,xbuy,xkdj,up15,up5,kk1pos,kk5pos,kk15pos
    m5up,m5down,m5next = stock5Min.forecastClose()
    m1up,m1down,m1next = stock1Min.forecastClose()
    lastM5 = stock5Min.lastKline()
    prelastM5 = stock5Min.preLastKline()
    pre2lastM5 = stock5Min.pre2LastKline()
    current = stock1Min.lastKline()
    lastm1 = stock1Min.preLastKline()
    prelastm1 = stock1Min.pre2LastKline()
    lastM15 = stock15Min.lastKline()

    lastM15 = stock15Min.lastKline()
    prelastM15 = stock15Min.preLastKline()
    pre2lastM15 = stock15Min.pre2LastKline()

    if current.time-lastM5.time>=5*60:
        return

    prelast5diff = prelastM5.j-prelastM5.k
    pre2last5diff = pre2lastM5.j - pre2lastM5.k

    prelast1diff = lastm1.j-lastm1.k
    pre2last1diff = prelastm1.j - prelastm1.k

    prelast15diff = prelastM15.j - prelastM15.k
    pre2last15diff = pre2lastM15.j - pre2lastM15.k

    pricelogging.info("time=%s,price=%s,1j=%s,1k=%s,5j=%s,5k=%s,15j=%s,15k=%s,1macd=%s,5macd=%s,15macd=%s" % \
                      (time.ctime(current.time),current.close,lastm1.j,lastm1.k,prelastM5.j,prelastM5.k,prelastM15.j,prelastM15.k,lastm1.macd,prelastM5.macd,prelastM15.macd))

    def pos(kk):
        if kk.downToUp() and kk.upmiddle(kk.findDownKline().time)==True:
            return 2
        elif kk.downToUp() and kk.upmiddle(kk.findDownKline().time)==False:
            return 1
        elif kk.downToUp()==False and kk.downmiddle(kk.findUpKline().time)==False:
            return 3
        elif kk.downToUp()==False and kk.downmiddle(kk.findUpKline().time)==True:
            return 4

    k1pos = pos(stock1Min)
    k5pos = pos(stock5Min)
    k15pos = pos(stock15Min)

    pricelogging.info("bpri=%s,time=%s,lastM5.j=%s,lastM5.macd=%s,m1.up=%s,m1.boll=%s,m1.down=%s,m5.up=%s,m5.boll=%s,m5.down=%s" % (buyPrice1,time.ctime(current.time),lastM5.j,lastM5.macd,
                                                                                                                                    lastm1.up,lastm1.boll,lastm1.dn,prelastM5.up,prelastM5.boll,prelastM5.dn))

    if buyPrice1==None:
        if sellSpec==True and prelastM5.macd > pre2lastM5.macd and prelastM5.j > pre2lastM5.j:
            pricelogging.info("disable tbuy sell End %s " % time.ctime(current.time))
            spec=2
            sellSpec = None
            if lastm1.j < prelastm1.j:
                return
            if lastm1.j<80:
                buy1Time = current.time
                buy2Time = lastM5.time
                buyPrice1 = current.open
                kk1pos = k1pos
                kk5pos = k5pos
                kk15pos = k15pos
                spec = 3
                pricelogging.info("tbuyb311-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (stock1Min.lastKline().open,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
                return

        if sellSpec==None and prelastM5.j-prelastM5.k>0 and stock5Min.kdjUpDontTouchMaxKline().j>80 and prelastM5.j<pre2lastM5.j and prelastM5.macd < pre2lastM5.macd:
            pricelogging.info("disable tbuy sell Start %s " % time.ctime(current.time))
            sellSpec=True
            return

        if sellSpec == True:
            pricelogging.info("disable tbuy sell %s " % time.ctime(current.time))
            return

        if prelastm1.j<20 and lastm1.j > prelastm1.j and abs(lastm1.j-prelastm1.j) > 19:
            if lastM5.j<20:
                return
            if lastm1.macd<0 and lastm1.macd < prelastm1.macd:
                return

            if lastM5.j < prelastM5.j:
                return

            if lastM5.j > prelastM5.j and prelastM5.macd < 0 and lastM5.macd < prelastM5.macd:
                return

            buy1Time = current.time
            buy2Time = lastM5.time
            buyPrice1 = current.open
            kk1pos = k1pos
            kk5pos = k5pos
            kk15pos = k15pos
            spec=1
            pricelogging.info("tbuyb2-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (buyPrice1,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
            return

        if prelastm1.j<20 and lastm1.j > prelastm1.j and lastm1.j-lastm1.k>0:
            if lastM5.j<20:
                return

            if lastM5.j < prelastM5.j:
                return
            if lastM5.j > prelastM5.j and prelastM5.macd < 0 and lastM5.macd < prelastM5.macd:
                return
            buy1Time = current.time
            buy2Time = lastM5.time
            buyPrice1 = current.open
            kk1pos = k1pos
            kk5pos = k5pos
            kk15pos = k15pos
            spec=1
            pricelogging.info("tbuyb4-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (buyPrice1,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
            return

        if stock1Min.preMyLastKline(3).j<20 and prelastm1.j>stock1Min.preMyLastKline(3).j and lastm1.j > prelastm1.j:
            if lastM5.j<20:
                return

            if lastM5.j < prelastM5.j:
                return

            if lastM5.j > prelastM5.j and prelastM5.macd < 0 and lastM5.macd < prelastM5.macd:
                return

            buy1Time = current.time
            buy2Time = lastM5.time
            buyPrice1 = current.open
            kk1pos = k1pos
            kk5pos = k5pos
            kk15pos = k15pos
            spec=1
            pricelogging.info("tbuyb3-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (buyPrice1,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
            return


    if buyPrice1!=None:
        if spec == 3:
            if lastm1.j < prelastm1.j:
                pricelogging.info("tbuybi568-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().open,(stock1Min.lastKline().open-buyPrice1),time.ctime(stock1Min.lastKline().time)))
                buyPrice1 = None
                spec = None
            elif lastm1.j>=80:
                spec = 1;
            return

        if stock1Min.lastKline().open - buyPrice1 < -15:
            pricelogging.info("tbuybi548-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().open,(stock1Min.lastKline().open-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = None
            spec = None
            return

        if spec==2:
            if prelastm1.j>80 and lastm1.j < prelastm1.j and abs(lastM5.macd)<0.2 and stock1Min.lastKline().open - buyPrice1<0:
                if lastM5.j>prelastM5.j and lastM5.macd>prelastM5.macd and lastM5.j<80:
                    return
                else:
                    pricelogging.info("tbuybi578-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().open,(stock1Min.lastKline().open-buyPrice1),time.ctime(stock1Min.lastKline().time)))
                    buyPrice1 = None
                    spec = 2
                    return
            if prelastM5.j<pre2lastM5.j:
                if prelastM5.macd>0.5 and prelastM5.macd > pre2lastM5.macd and stock1Min.lastKline().open - buyPrice1>0:
                    pricelogging.info("tbuybikk508-%s,disable,time=%s" % (buyPrice1,time.ctime(stock1Min.lastKline().time)))
                    return;

                if prelastM5.macd<-0.8 and lastM5.macd>prelastM5.macd:
                    pricelogging.info("tbuybikk548-%s,disable,time=%s" % (buyPrice1,time.ctime(stock1Min.lastKline().time)))
                    return;

                pricelogging.info("tbuybi558-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().open,(stock1Min.lastKline().open-buyPrice1),time.ctime(stock1Min.lastKline().time)))
                buyPrice1 = None
                spec = None
                return

        if spec!=2 and prelastm1.j>80 and lastm1.j < prelastm1.j:
            if lastm1.macd>prelastm1.macd and lastM5.j>prelastM5.j and lastM5.macd > prelastM5.macd:
                pricelogging.info("tbuybikk518-%s,disable,time=%s" % (buyPrice1,time.ctime(stock1Min.lastKline().time)))
                return

            if lastM5.j - lastM5.k >0 and lastM15.j > prelastM15.j and lastM15.macd > prelastM15.macd and lastM5.macd > prelastM5.macd and  lastm1.macd > 0 and stock1Min.lastKline().close - buyPrice1>0:
                pricelogging.info("tbuybikk598-%s,disable,time=%s" % (buyPrice1,time.ctime(stock1Min.lastKline().time)))
                spec = 2
                return

            if lastM5.macd < 0 and lastM5.j - lastM5.k<0:
                pricelogging.info("tbuybi568-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().open,(stock1Min.lastKline().open-buyPrice1),time.ctime(stock1Min.lastKline().time)))
                buyPrice1 = None
                return
            if stock1Min.lastKline().open - buyPrice1<0 and ((prelastM5.j-prelastM5.k>0) or prelastM5.j>pre2lastM5.j):
                spec = 2
                return

            if lastM5.macd>prelastM5.macd and stock1Min.lastKline().close-buyPrice1>0:
                return

            pricelogging.info("tbuybi538-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().open,(stock1Min.lastKline().open-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = None
            if prelastM5.j>pre2lastM5.j:
                spec=2
            return

        if spec==1 and lastm1.j<80 and lastm1.j < prelastm1.j and lastM5.j<prelastM5.j:
            if lastM5.j<20 and lastm1.macd>prelastm1.macd:
                return
            pricelogging.info("tbuybi668-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().open,(stock1Min.lastKline().open-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = None
            spec = None
            return

    if buyPrice1==None and spec==2:
        if lastm1.j > prelastm1.j and prelastM5.j>pre2lastM5.j and prelastM5.j<80 and lastm1.j<80:
            if lastM5.macd <0 and lastM5.macd<prelastM5.macd:
                return

            buy1Time = current.time
            buy2Time = lastM5.time
            buyPrice1 = current.open
            kk1pos = k1pos
            kk5pos = k5pos
            kk15pos = k15pos
            spec=2
            pricelogging.info("tbuyb31-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (stock1Min.lastKline().open,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
            return

    if buyPrice1==None and lastM5.j>prelastM5.j and (prelastM5.j<20 or lastM5.j<20) and lastM5.macd>prelastM5.macd:
        if lastM5.macd<0 and lastM5.macd < prelastM5.macd + 0.03:
            return

        if lastM5.j<20 and prelastM5.j<pre2lastM5.j:
            return

        buy1Time = current.time
        buy2Time = lastM5.time
        buyPrice1 = current.open
        kk1pos = k1pos
        kk5pos = k5pos
        kk15pos = k15pos
        spec=2
        pricelogging.info("tbuyb489-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (buyPrice1,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
        return

    if buyPrice1 == None and lastM5.j>prelastM5.j and lastM5.macd>prelastM5.macd and lastM5.macd>0.5 and lastM5.j<80 and lastM15.j-lastM15.k>0 and lastM15.macd>0.5:
        if lastM5.j<20 and prelastM5.j<pre2lastM5.j:
            return

        buy1Time = current.time
        buy2Time = lastM5.time
        buyPrice1 = current.open
        kk1pos = k1pos
        kk5pos = k5pos
        kk15pos = k15pos
        spec=2
        pricelogging.info("tbuyb4189-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (buyPrice1,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
        return

    if buyPrice1==None and lastM15.macd >0 and stock5Min.findLowestkdj()==True and lastM5.macd > prelastM5.macd and lastM5.j>prelastM5.j and lastM5.j-lastM5.k>0 and lastM5.j<80 and lastM5.high<lastM5.boll:
        if lastM5.j<20 and prelastM5.j<pre2lastM5.j:
            return

        buy1Time = current.time
        buy2Time = lastM5.time
        buyPrice1 = current.open
        kk1pos = k1pos
        kk5pos = k5pos
        kk15pos = k15pos
        spec=2
        pricelogging.info("tbuyb4489-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (buyPrice1,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
        return

    if buyPrice1==None and prelastM5.j>pre2lastM5.j and pre2lastM5.j > stock5Min.preMyLastKline(3).j and prelastM5.macd > pre2lastM5.macd and \
                    lastM5.j>prelastM5.j and lastM5.macd>prelastM5.macd and current.high < lastM5.up and lastM15.j>prelastM15.j and lastM15.macd>prelastM15.macd \
            and prelastM15.j>pre2lastM15.j and prelastM15.macd > pre2lastM15.macd and lastM5.macd>0 and lastm1.j>prelastm1.j:
        if lastM5.j<20 and prelastM5.j<pre2lastM5.j:
            return

        buy1Time = current.time
        buy2Time = lastM5.time
        buyPrice1 = current.close
        kk1pos = k1pos
        kk5pos = k5pos
        kk15pos = k15pos
        spec=2
        pricelogging.info("tbuyb4789-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (buyPrice1,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
        return


def go12():
    global buyPrice1,buyPrice2,bidsList,asksList,buy1Time,buy2Time,buyTriggerTime,buyPrice3,downToUp,upToDown,middleToUp,spec,xspec,sellSpec,xbuy,xkdj,up15,up5,kk1pos,kk5pos,kk15pos
    m5up,m5down,m5next = stock5Min.forecastClose()
    m1up,m1down,m1next = stock1Min.forecastClose()
    lastM5 = stock5Min.lastKline()
    prelastM5 = stock5Min.preLastKline()
    pre2lastM5 = stock5Min.pre2LastKline()
    current = stock1Min.lastKline()
    lastm1 = stock1Min.preLastKline()
    prelastm1 = stock1Min.pre2LastKline()
    lastM15 = stock15Min.lastKline()

    lastM15 = stock15Min.lastKline()
    prelastM15 = stock15Min.preLastKline()
    pre2lastM15 = stock15Min.pre2LastKline()

    if current.time-lastM5.time>=5*60:
        return

    if current.time == buy1Time:
        return

    prelast5diff = prelastM5.j-prelastM5.k
    pre2last5diff = pre2lastM5.j - pre2lastM5.k

    prelast1diff = lastm1.j-lastm1.k
    pre2last1diff = prelastm1.j - prelastm1.k

    prelast15diff = prelastM15.j - prelastM15.k
    pre2last15diff = pre2lastM15.j - pre2lastM15.k

    pricelogging.info("time=%s,price=%s,1j=%s,1k=%s,5j=%s,5k=%s,15j=%s,15k=%s,1macd=%s,5macd=%s,15macd=%s" % \
                      (time.ctime(current.time),current.close,lastm1.j,lastm1.k,prelastM5.j,prelastM5.k,prelastM15.j,prelastM15.k,lastm1.macd,prelastM5.macd,prelastM15.macd))

    def pos(kk):
        if kk.downToUp() and kk.upmiddle(kk.findDownKline().time)==True:
            return 2
        elif kk.downToUp() and kk.upmiddle(kk.findDownKline().time)==False:
            return 1
        elif kk.downToUp()==False and kk.downmiddle(kk.findUpKline().time)==False:
            return 3
        elif kk.downToUp()==False and kk.downmiddle(kk.findUpKline().time)==True:
            return 4

    k1pos = pos(stock1Min)
    k5pos = pos(stock5Min)
    k15pos = pos(stock15Min)

    pricelogging.info("bpri=%s,time=%s,lastM5.j=%s,lastM5.macd=%s,m1.up=%s,m1.boll=%s,m1.down=%s,m5.up=%s,m5.boll=%s,m5.down=%s" % (buyPrice1,time.ctime(current.time),lastM5.j,lastM5.macd,
                                                                                                                                    lastm1.up,lastm1.boll,lastm1.dn,prelastM5.up,prelastM5.boll,prelastM5.dn))
    pricelogging.info("%s,macd-1=%s,macd-5=%s" % (time.ctime(lastm1.time),stock1Min.forecastMacd(),stock5Min.forecastMacd()))
    pricelogging.info("tt,lopen=%s,lclose=%s,lmacd=%s,popen=%s,pclose=%s,pmacd=%s" % (lastm1.open,lastm1.close,lastm1.macd,prelastm1.open,prelastm1.close,prelastm1.macd))

    lastm1_datetime = datetime.fromtimestamp(lastm1.time)
    prelastm1_datetime = datetime.fromtimestamp(prelastm1.time)

    prelastm5_datetime = datetime.fromtimestamp(prelastM5.time)

    pricelogging.info("ltime=%s,ptime=%s,ppmacd=%s,lastm1_datetime=%s,prelastm1_datetime=%s" % (lastm1_datetime.minute % 5,prelastm1_datetime.minute % 5,stock1Min.preMyLastKline(3).macd,lastm1_datetime,prelastm1_datetime) )

    pricelogging.info("tboll=%s"  % (lastm1_datetime.minute % 5 > prelastm1_datetime.minute % 5 and lastm1.macd>prelastm1.macd and prelastm1.macd>stock1Min.preMyLastKline(3).macd))
    pricelogging.info("tx=%s,tddx=%s,5open=%s,5close=%s" % ((lastm1.open < lastm1.close and prelastm1.open < prelastm1.close),( prelastM5.open>prelastM5.close and prelastM5.j < pre2lastM5.j),prelastM5.open,prelastM5.close) )


    if buyPrice1 == None:
        if lastm1_datetime.minute % 5 > prelastm1_datetime.minute % 5 and lastm1.macd>prelastm1.macd and prelastm1.macd>stock1Min.preMyLastKline(3).macd:
            if lastm1.open > lastm1.close and prelastm1.open > prelastm1.close:
                return

            if prelastM5.macd<0 and not (lastm1.open < lastm1.close and prelastm1.open < prelastm1.close):
                return

            if prelastM5.open>prelastM5.close and prelastM5.j < pre2lastM5.j and not (lastm1.open < lastm1.close and prelastm1.open < prelastm1.close):
                return

            if lastm1.high>lastm1.up:
                return

            if prelastM5.macd<0 and stock5Min.touchShortDown()==False:
                return

            if prelastM5.macd<0 and stock1Min.touchDown()==False:
                return

            if prelastM5.j>80 and prelastM5.high+0.3>prelastM5.up and lastm1.high+0.3 > lastm1.up:
                return

            if prelastM5.open>prelastM5.close and prelastM5.macd>0 and prelastM5.macd<0.1 and prelastM5.j < pre2lastM5.j:
                return

            buy1Time = current.time
            buy2Time = lastM5.time
            buyPrice1 = current.close
            kk1pos = k1pos
            kk5pos = k5pos
            kk15pos = k15pos
            spec = 1
            pricelogging.info("tbuyb1-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (buyPrice1,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
            return

    if buyPrice1!= None:
        if stock1Min.lastKline().close - buyPrice1 < -15:
            pricelogging.info("tbuybi548-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = None
            spec = None
            return

        #1
        if abs(lastm1.close-lastm1.open)<=0.03 and prelastM5.macd < pre2lastM5.macd:
            pricelogging.info("tbuybi618-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = None
            spec = None
            return

        #2
        if prelastm1+0.3 > prelastm1.up and prelastm1.j > lastm1.j:
            pricelogging.info("tbuybi628-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = None
            spec = None
            return

        #3
        if prelastm1.high+0.3 > prelastm1.boll and  (abs(prelastm1.high-prelastm1.boll) < abs(prelastm1.high-prelastm1.up))  and prelastm1.j > lastm1.j and lastm1.up - lastm1.dn > 3:
            if lastm1.macd>0.1 and not (prelastm1.macd<stock1Min.preMyLastKline(3).macd and lastm1.macd<prelastm1.macd):
                return
            pricelogging.info("tbuybi638-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = None
            spec = None
            return

        if prelastM5.macd < 0 and buy1Time == lastm1.time and lastm1.close < lastm1.open and lastm1.j < prelastm1.j and \
                ((lastm1.macd>prelastm1.macd and abs(lastm1.macd - prelastm1.macd)<0.03) or (lastm1.macd < prelastm1.macd) ):
            pricelogging.info("tbuybi588-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = None
            spec = None
            return

        if prelastM5.time == buy2Time and prelastM5.macd<pre2lastM5.macd:
            pricelogging.info("xdd,t=%s,t1=%s,t2=%s" % ((buy1Time <= stock1Min.preMyLastKline(4).time),(lastm1.macd > prelastm1.macd and prelastm1.macd>stock1Min.preMyLastKline(3).macd and stock1Min.preMyLastKline(3).macd > stock1Min.preMyLastKline(4).macd \
                                                                                                        and prelastM5.j > pre2lastM5.j and lastm1.j>prelastm1.j),(lastm1.macd > prelastm1.macd and prelastm1.macd>stock1Min.preMyLastKline(3).macd and prelastM5.j<20 and lastm1.j > prelastm1.j and lastm1.j-lastm1.k>0)) )

            if buy1Time <= stock1Min.preMyLastKline(4).time:
                if lastm1.macd > prelastm1.macd and prelastm1.macd>stock1Min.preMyLastKline(3).macd and stock1Min.preMyLastKline(3).macd > stock1Min.preMyLastKline(4).macd:
                    if prelastM5.j<20 and lastm1.j-lastm1.k>0:
                        return
                    if prelastM5.j > pre2lastM5.j and lastm1.j>prelastm1.j:
                        return
            else:
                if lastm1.macd > prelastm1.macd and prelastm1.macd>stock1Min.preMyLastKline(3).macd and prelastM5.j<20 and lastm1.j > prelastm1.j and lastm1.j-lastm1.k>0:
                    return

            pricelogging.info("tbuybi668-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = None
            return

        if prelastM5.time == buy2Time and prelastM5.macd>pre2lastM5.macd and abs(prelastM5.macd - pre2lastM5.macd)<=0.03 and stock5Min.touchUp() and \
                        lastm1.j<prelastm1.j and prelastm1.j>80:
            pricelogging.info("tbuybi898-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = None
            return

        if prelastM5.time>buy2Time:
            pricelogging.info("prem5.macd=%s,pre2m5.macd=%s,m5j=%s,p2m5j=%s,touchup=%s" % (prelastM5.macd,pre2lastM5.macd,prelastM5.j,pre2lastM5.j,stock5Min.touchUpMyShort()))
            if prelastM5.macd > pre2lastM5.macd and prelastM5.j>pre2lastM5.j:
                if lastM5.j>80 and (stock5Min.touchUpMyShort() or (abs(lastM5.close-lastM5.boll)<abs(lastM5.close-lastM5.dn)) or (abs(prelastM5.close-prelastM5.boll)<abs(prelastM5.close-prelastM5.dn)) ):
                    pass
                else:
                    return
            if lastm1.macd < prelastm1.macd:
                pricelogging.info("tbuybi788-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
                buyPrice1 = None
                return




def go13():
    global buyPrice1,buyPrice2,bidsList,asksList,buy1Time,buy2Time,buyTriggerTime,buyPrice3,downToUp,upToDown,middleToUp,spec,xspec,sellSpec,xbuy,xkdj,up15,up5,kk1pos,kk5pos,kk15pos,m5data
    m5up,m5down,m5next = stock5Min.forecastClose()
    m1up,m1down,m1next = stock1Min.forecastClose()
    lastM5 = stock5Min.lastKline()
    prelastM5 = stock5Min.preLastKline()
    pre2lastM5 = stock5Min.pre2LastKline()
    current = stock1Min.lastKline()
    lastm1 = stock1Min.preLastKline()
    prelastm1 = stock1Min.pre2LastKline()
    lastM15 = stock15Min.lastKline()

    lastM15 = stock15Min.lastKline()
    prelastM15 = stock15Min.preLastKline()
    pre2lastM15 = stock15Min.pre2LastKline()

    if current.time-lastM5.time>=5*60:
        return

    if current.time == buy1Time:
        return

    prelast5diff = prelastM5.j-prelastM5.k
    pre2last5diff = pre2lastM5.j - pre2lastM5.k

    prelast1diff = lastm1.j-lastm1.k
    pre2last1diff = prelastm1.j - prelastm1.k

    prelast15diff = prelastM15.j - prelastM15.k
    pre2last15diff = pre2lastM15.j - pre2lastM15.k

    pricelogging.info("time=%s,price=%s,1j=%s,1k=%s,5j=%s,5k=%s,15j=%s,15k=%s,1macd=%s,5macd=%s,15macd=%s" % \
                      (time.ctime(current.time),current.close,lastm1.j,lastm1.k,prelastM5.j,prelastM5.k,prelastM15.j,prelastM15.k,lastm1.macd,prelastM5.macd,prelastM15.macd))

    def pos(kk):
        if kk.downToUp() and kk.upmiddle(kk.findDownKline().time)==True:
            return 2
        elif kk.downToUp() and kk.upmiddle(kk.findDownKline().time)==False:
            return 1
        elif kk.downToUp()==False and kk.downmiddle(kk.findUpKline().time)==False:
            return 3
        elif kk.downToUp()==False and kk.downmiddle(kk.findUpKline().time)==True:
            return 4

    k1pos = pos(stock1Min)
    k5pos = pos(stock5Min)
    k15pos = pos(stock15Min)

    pricelogging.info("bpri=%s,time=%s,lastM5.j=%s,lastM5.macd=%s,m1.up=%s,m1.boll=%s,m1.down=%s,m5.up=%s,m5.boll=%s,m5.down=%s" % (buyPrice1,time.ctime(current.time),lastM5.j,lastM5.macd,
                                                                                                                                    lastm1.up,lastm1.boll,lastm1.dn,prelastM5.up,prelastM5.boll,prelastM5.dn))
    pricelogging.info("%s,macd-1=%s,macd-5=%s" % (time.ctime(lastm1.time),stock1Min.forecastMacd(),stock5Min.forecastMacd()))
    pricelogging.info("tt,lopen=%s,lclose=%s,lmacd=%s,popen=%s,pclose=%s,pmacd=%s" % (lastm1.open,lastm1.close,lastm1.macd,prelastm1.open,prelastm1.close,prelastm1.macd))

    lastm1_datetime = datetime.fromtimestamp(lastm1.time)
    prelastm1_datetime = datetime.fromtimestamp(prelastm1.time)

    prelastm5_datetime = datetime.fromtimestamp(prelastM5.time)

    pricelogging.info("ltime=%s,ptime=%s,ppmacd=%s,lastm1_datetime=%s,prelastm1_datetime=%s" % (lastm1_datetime.minute % 5,prelastm1_datetime.minute % 5,stock1Min.preMyLastKline(3).macd,lastm1_datetime,prelastm1_datetime) )

    pricelogging.info("tboll=%s"  % (lastm1_datetime.minute % 5 > prelastm1_datetime.minute % 5 and lastm1.macd>prelastm1.macd and prelastm1.macd>stock1Min.preMyLastKline(3).macd))
    pricelogging.info("tx=%s,tddx=%s,5open=%s,5close=%s" % ((lastm1.open < lastm1.close and prelastm1.open < prelastm1.close),( prelastM5.open>prelastM5.close and prelastM5.j < pre2lastM5.j),prelastM5.open,prelastM5.close) )


    '''
    xping1,updown1,lauchKline1 = stock1Min.goUpOrDown()
    xping5,updown5,lauchKline5 = stock5Min.goUpOrDown()

    xp5,xp5_b = stock5Min.findSearchTouchKLine(lauchKline5.time)
    xp5_2,xp5_2_b = stock5Min.findSearchTouchKLine(lastM5.time)

    if xp5.time == xp5_2.time:
        updown5 = xp5_b
        lauchKline5 = xp5



    kk1Down = stock1Min.touchSimlarTimeDown(lauchKline1.time)
    kk1Up = stock1Min.touchSimlarTimeUp(lauchKline1.time)
    kk1Boll = stock1Min.touchSimlarTimeBoll(lauchKline1.time)
    kk1DownToBoll = stock1Min.touchSimlarTimeBetweenDownAndBoll(lauchKline1.time)
    kk1UpToBoll = stock1Min.touchSimlarTimeBetweenUpAndBoll(lauchKline1.time)


    kk5Down = stock5Min.touchSimlarTimeDown(lauchKline5.time,0)
    kk5Up = stock5Min.touchSimlarTimeUp(lauchKline5.time,0)
    kk5Boll = stock5Min.touchSimlarTimeBoll(lauchKline5.time,0)
    kk5DownToBoll = stock5Min.touchSimlarTimeBetweenDownAndBoll(lauchKline5.time,0)
    kk5UpToBoll = stock5Min.touchSimlarTimeBetweenUpAndBoll(lauchKline5.time,0)
    '''

    f1po = stock1Min.mkposition()
    f5po = stock5Min.mkposition(count=0)

    kk1Down = False
    kk1Up = False
    kk1Boll = False
    kk1DownToBoll = False
    kk1UpToBoll = False

    kk5Down = False
    kk5Up = False
    kk5Boll = False
    kk5DownToBoll = False
    kk5UpToBoll = False


    if f1po[0][0] == 1 :
        kk1Down = True

    if f1po[1][0] == 2 :
        kk1DownToBoll = True

    if f1po[2][0] == 3 :
        kk1Boll = True

    if f1po[3][0] == 4 :
        kk1UpToBoll = True

    if f1po[4][0] == 5 :
        kk1Up = True


    if f5po[0][0] == 1 :
        kk5Down = True

    if f5po[1][0] == 2 :
        kk5DownToBoll = True

    if f5po[2][0] == 3 :
        kk5Boll = True

    if f5po[3][0] == 4 :
        kk5UpToBoll = True

    if f5po[4][0] == 5 :
        kk5Up = True


    pricelogging.info("fx1=%s,fx5=%s" % (f1po,f5po))

    pricelogging.info("kk1down=%s,up=%s,boll=%s,downtoboll=%s,uptoboll=%s" % (kk1Down,kk1Up,kk1Boll,kk1DownToBoll,kk1UpToBoll))

    pricelogging.info("kk5down=%s,up=%s,boll=%s,downtoboll=%s,uptoboll=%s" % (kk5Down,kk5Up,kk5Boll,kk5DownToBoll,kk5UpToBoll))

    pricelogging.info("k1iscross=%s,k5icross=%s,isupordownline1=%s,isupordownline5=%s" % (stock1Min.iscrossKline(),stock5Min.iscrossKline(),stock1Min.isUpOrDownKline(),stock5Min.isUpOrDownKline()) )

    if buyPrice1 == None:
        fdata = stock1Min.findInFiveData()

        if lastM5.macd<0 and lastM5.macd<-0.6 and lastM5.macd < prelastM5.macd:
            return

        if stock5Min.iscrossKline() and stock5Min.isUpOrDownKline() and lastm1.macd>prelastm1.macd and lastM5.macd>0.2 and lastm1.macd<0 and lastm1.macd>-0.2:
            buy1Time = current.time
            buy2Time = lastM5.time
            buyPrice1 = current.close
            kk1pos = k1pos
            kk5pos = k5pos
            kk15pos = k15pos
            spec = 2
            pricelogging.info("tbuyb11-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (buyPrice1,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
            return

        if prelastM5.macd<pre2lastM5.macd and (kk5Up or (kk5UpToBoll and f5po[3][1]==False) or (kk5Boll and f5po[2][1]==False) ):
            return

        if stock1Min.iscrossKline():
            if (kk1Down or (kk1DownToBoll and f1po[1][1]==True) ):
                if kk5Down and not kk5Boll:
                    buy1Time = current.time
                    buy2Time = lastM5.time
                    buyPrice1 = current.close
                    kk1pos = k1pos
                    kk5pos = k5pos
                    kk15pos = k15pos
                    spec = 1
                    pricelogging.info("tbuyb1-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (buyPrice1,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
                    return
                if lastM5.macd > 0.3 and kk5UpToBoll:
                    if lastm1.macd < prelastm1.macd and lastm1.macd<0 and prelastm1.macd>0:
                        return
                    buy1Time = current.time
                    buy2Time = lastM5.time
                    buyPrice1 = current.close
                    kk1pos = k1pos
                    kk5pos = k5pos
                    kk15pos = k15pos
                    spec = 1
                    pricelogging.info("tbuyb13-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (buyPrice1,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
                    return
            elif (kk1Boll and f1po[2][1]==True) and ((kk5DownToBoll and f5po[1][1]==True) or (kk5Boll and f1po[2][1]==True) or (kk5UpToBoll and f1po[3][1]==True)) and not kk5Up and (lastm1.j<20 or (lastm1.macd<0 and lastm1.macd>-0.16)):
                if lastM5.macd>0 and lastM5.macd<0.16:
                    return

                if kk5Up and not kk5Down and lastm1.macd<0 and fdata[0].open>lastm1.close:
                    return

                if lastm1.macd < prelastm1.macd and lastm1.macd<0 and prelastm1.macd>0:
                    return

                if prelastM5.macd < pre2lastM5.macd and prelastM5.macd <0 and pre2lastM5.macd >0:
                    return

                buy1Time = current.time
                buy2Time = lastM5.time
                buyPrice1 = current.close
                kk1pos = k1pos
                kk5pos = k5pos
                kk15pos = k15pos
                spec = 2
                pricelogging.info("tbuyb2-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (buyPrice1,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
                return
            elif ((kk1Boll and f1po[2][1]==False) or (kk1UpToBoll and f1po[3][1]==False)) \
                    and ( (((kk5Boll and f5po[2][1]==True) or (kk5UpToBoll and f5po[3][1]==True)) and (lastM5.macd>0 and lastM5.macd>prelastM5.macd) )  or ( (kk5DownToBoll and f5po[1][1]==True) and ( (lastM5.macd>0 and prelastM5.macd<0) or (lastM5.macd <0 and lastM5.macd> -0.1)  ) ) ) \
                    and not kk5Up and stock1Min.isUpOrDownKline() and lastm1.j<90:

                if lastm1.macd < prelastm1.macd and lastm1.macd<0 and prelastm1.macd>0:
                    return

                if prelastM5.macd < pre2lastM5.macd and prelastM5.macd <0 and pre2lastM5.macd >0:
                    return

                buy1Time = current.time
                buy2Time = lastM5.time
                buyPrice1 = current.close
                kk1pos = k1pos
                kk5pos = k5pos
                kk15pos = k15pos
                spec = 11
                pricelogging.info("tbuyb24-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (buyPrice1,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
                return

            elif kk1Down and kk5Boll and lastM5.j<20:
                if stock1Min.isUpOrDownKline(1)==False and stock1Min.isUpOrDownKline(2)==False and stock1Min.isUpOrDownKline(3)==False:
                    return
                buy1Time = current.time
                buy2Time = lastM5.time
                buyPrice1 = current.close
                kk1pos = k1pos
                kk5pos = k5pos
                kk15pos = k15pos
                spec = 3
                pricelogging.info("tbuyb3-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (buyPrice1,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
                return
        if stock1Min.isMoreUpKline():
            if kk1Down and kk5Down and not kk5Boll:
                buy1Time = current.time
                buy2Time = lastM5.time
                buyPrice1 = current.close
                kk1pos = k1pos
                kk5pos = k5pos
                kk15pos = k15pos
                spec = 4
                pricelogging.info("tbuyb4-%s,time=%s,deciderTime=%s,k5=%s,k1=%s,k15=%s,spec=%s" % (buyPrice1,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),k5pos,k1pos,k15pos,spec))
                return


    if buyPrice1 != None:
        if stock5Min.iscrossKline() and prelastM5.macd>0 and prelastM5.macd<0.17 and prelastM5.macd<pre2lastM5.macd and (kk5Up or kk5UpToBoll):
            if lastm1.macd>prelastm1.macd and lastm1.macd<0.17:
                return
            pricelogging.info("tbuybi8981-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = None
            return

        if spec==11 and prelastM5.macd<pre2lastM5.macd and (kk5Up or kk5UpToBoll):
            if stock5Min.iscrossKline():
                spec = 2
                pricelogging.info("tbuy disable to 2,5time=%s,1time=%s" % (time.ctime(lastM5.time),time.ctime(lastm1.time)))
            if lastM5.macd < 0.2:
                spec = 2
                pricelogging.info("tbuy disable to 21,5time=%s,1time=%s" % (time.ctime(lastM5.time),time.ctime(lastm1.time)))

        if spec==11 and kk5Up and (lastM5.macd<prelastM5.macd or lastM5.k-lastM5.j<0):
            pricelogging.info("tbuybi8981-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
            buyPrice1 = None
            return

        kkk1up = kk1Up
        if not kkk1up :
            if kk1UpToBoll and f5po[3][1]:
                kkk1up = True

        if stock1Min.iscrossKline() or stock1Min.isUpOrDownKline()==False:
            if spec==11:
                return

            if lastm1.macd>0 and prelastm1.macd<0:
                return

            if lastm1.macd>0 and prelastm1.macd>0 and lastm1.macd>prelastm1.macd and lastm1.macd>1:
                return

            if kk1Boll and not kk1Down and (prelastM5.macd<pre2lastM5.macd and prelastM5.macd<0.2) and (kk5Up or kk5UpToBoll):
                if lastm1.macd>prelastm1.macd and lastm1.macd<0.17:
                    return
                pricelogging.info("tbuybi8980-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
                buyPrice1 = None
                return

            if kk1Boll and (kk5Down or kk5DownToBoll) and lastm1.j>80 and (spec==1 or spec==3 or spec==4) and lastm1.macd<-0.1:
                pricelogging.info("tbuybi898-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
                buyPrice1 = None
                return
            elif (kk1Up and not kk1Down and lastm1.j>80) or (kk1Up and not kk1Down and lastm1.macd<prelastm1.macd) :
                pricelogging.info("tbuybi890-%s,sell-%s,diff=%s,time=%s" % (buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
                buyPrice1 = None
                return



def go14():
    global buyPrice1,buyPrice2,bidsList,asksList,buy1Time,buy2Time,buyTriggerTime,buyPrice3,downToUp,upToDown,middleToUp,spec,xspec,sellSpec,xbuy,xkdj,up15,up5,kk1pos,kk5pos,kk15pos,m5data
    m5up,m5down,m5next = stock5Min.forecastClose()
    m1up,m1down,m1next = stock1Min.forecastClose()
    lastM5 = stock5Min.lastKline()
    prelastM5 = stock5Min.preLastKline()
    pre2lastM5 = stock5Min.pre2LastKline()
    current = stock1Min.lastKline()
    lastm1 = stock1Min.preLastKline()
    prelastm1 = stock1Min.pre2LastKline()
    lastM15 = stock15Min.lastKline()

    lastM15 = stock15Min.lastKline()
    prelastM15 = stock15Min.preLastKline()
    pre2lastM15 = stock15Min.pre2LastKline()

    if current.time-lastM5.time>=5*60:
        return

    if current.time == buy1Time:
        return

    f1po1,f1po5 = ply.pl(stock1Min,stock5Min,"1","5",5)
    f2po5,f2po15 = ply.pl(stock5Min,stock15Min,"5","15",15)

    bymacd1 = ply.canbuybymacd(lastm1,prelastm1)
    bykdj1 = ply.canbuybykdj(lastm1,prelastm1)

    bymacd5 = ply.canbuybymacd(lastM5,prelastM5)
    bykdj5 = ply.canbuybykdj(lastM5,prelastM5)

    bymacd15 = ply.canbuybymacd(lastM15,prelastM15)
    bykdj15 = ply.canbuybykdj(lastM15,prelastM15)

    pricelogging.info("time=%s,fp1=%s,fp2=%s,fp3=%s,bymacd=%s,bykdj1=%s,bymacd5=%s,bykdj5=%s,bymacd15=%s,bykdj15=%s" % (time.ctime(current.time),f1po1,f1po5,f2po15,bymacd1,bykdj1,bymacd5,bykdj5,bymacd15,bykdj15))

    if prelastM5.po==None:
        return

    def xbuy3():
        fdata = stock1Min.findInFiveData()
        if ply.canbuy(stock1Min,lastm1,prelastm1,stock1Min.preMyLastKline(3),lastM5,prelastM5,pre2lastM5)==True :
            pricelogging.info("time = %s ,tbuy buy by macd 121-3" % (time.ctime(current.time)))
            return 10

    def xbuy4():
        if lastm1.j-lastm1.k<0 and lastm1.j > prelastm1.j:
            return 31
        if lastm1.j-lastm1.k>0 and prelastm1.j-prelastm1.k<0:
            return 32


    def buy(tag):
        global buyPrice1,buyPrice2,bidsList,asksList,buy1Time,buy2Time,buyTriggerTime,buyPrice3,downToUp,upToDown,middleToUp,spec,xspec,sellSpec,xbuy,xkdj,up15,up5,kk1pos,kk5pos,kk15pos,m5data
        buy1Time = current.time
        buy2Time = lastM5.time
        buyPrice1 = current.close
        sellSpec = lastM5.j - lastM5.k
        m5data = None
        kk1pos = f1po1
        kk5pos = f1po5
        pricelogging.info("tbuy-%s,-%s,time=%s,deciderTime=%s,spec=%s" % (tag,buyPrice1,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),spec))
        return

    def sell(tag):
        global buyPrice1,buyPrice2,bidsList,asksList,buy1Time,buy2Time,buyTriggerTime,buyPrice3,downToUp,upToDown,middleToUp,spec,xspec,sellSpec,xbuy,xkdj,up15,up5,kk1pos,kk5pos,kk15pos,m5data
        pricelogging.info("tbuy-%s-%s,sell-%s,diff=%s,time=%s" % (tag,buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = None
        spec = None
        buy1Time = None
        buy2Time = None
        xspec = None
        xkdj = None
        upToDown = None
        sellSpec = None
        m5data = None
        kk1pos = None
        kk5pos = None
        return

    txtbuy = xbuy3()

    if txtbuy!=None and spec==None:
        spec = txtbuy


    if (spec==11 or spec==10 or spec == 21 or spec==22) and buyPrice1==None:
        buy(spec)
        return

    if spec == 15:
        if lastm1.close < lastm1.open :
            if xbuy3()==None:
                sell("115-2")
            if lastM5.j-lastM5.k >0:
                spec = 12
        else:
            spec=11

    if buyPrice1!=None and spec!=15:
        if ply.cansell(stock1Min,lastm1,prelastm1,stock1Min.preMyLastKline(3),lastM5,prelastM5,pre2lastM5) == True:

            if current.close - buyPrice1<0 and lastm1.j-lastm1.k>0 and lastm1.macd>0.7 and lastM5.j>prelastM5.j and prelastM5.open < prelastM5.close:
                pricelogging.info("time = %s ,tbuy disable by macd 117-5" % (time.ctime(current.time)))
                return
            if datetime.fromtimestamp(lastm1.time).minute % 5==0 and lastm1.close<lastm1.open and prelastM5.macd>0 and prelastM5.macd > pre2lastM5.macd \
                    and prelastM5.close > prelastM5.open and pre2lastM5.close>pre2lastM5.open:
                spec = 15
                return

            if datetime.fromtimestamp(lastm1.time).minute % 5==4 and lastm1.close<lastm1.open and prelastM5.macd>0 and prelastM5.macd > pre2lastM5.macd \
                    and prelastM5.close > prelastM5.open and pre2lastM5.close>pre2lastM5.open and lastm1.macd>1 and lastM5.macd>1:
                spec = 15
                return
            if xbuy3()==None:
                sell("115-1")
            if lastM5.j-lastM5.k >0:
                spec = 12

    if spec == 12 and buyPrice1==None:
        if lastM5.j-lastM5.k<0:
            pricelogging.info("time = %s ,tbuy disable by macd 112-5" % (time.ctime(current.time)))
            sepc = None
            sellSpec = None
            m5data = None

        if ply.canbuy(stock1Min,lastm1,prelastm1,stock1Min.preMyLastKline(3),lastM5,prelastM5,pre2lastM5)==True:
            buy("1119")


def go15():
    global buyPrice1,buyPrice2,bidsList,asksList,buy1Time,buy2Time,buyTriggerTime,buyPrice3,downToUp,upToDown,middleToUp,spec,xspec,sellSpec,xbuy,xkdj,up15,up5,kk1pos,kk5pos,kk15pos,m5data
    m5up,m5down,m5next = stock5Min.forecastClose()
    m1up,m1down,m1next = stock1Min.forecastClose()
    lastM5 = stock5Min.lastKline()
    prelastM5 = stock5Min.preLastKline()
    pre2lastM5 = stock5Min.pre2LastKline()
    current = stock1Min.lastKline()
    lastm1 = stock1Min.preLastKline()
    prelastm1 = stock1Min.pre2LastKline()
    lastM15 = stock15Min.lastKline()

    lastM15 = stock15Min.lastKline()
    prelastM15 = stock15Min.preLastKline()
    pre2lastM15 = stock15Min.pre2LastKline()

    if current.time-lastM5.time>=5*60:
        return

    if current.time == buy1Time:
        return

    f1po1,f1po5 = ply.pl(stock1Min,stock5Min,"1","5",5)
    f2po5,f2po15 = ply.pl(stock5Min,stock15Min,"5","15",15)

    bymacd1 = ply.canbuybymacd(lastm1,prelastm1)
    bykdj1 = ply.canbuybykdj(lastm1,prelastm1)

    bymacd5 = ply.canbuybymacd(lastM5,prelastM5)
    bykdj5 = ply.canbuybykdj(lastM5,prelastM5)

    bymacd15 = ply.canbuybymacd(lastM15,prelastM15)
    bykdj15 = ply.canbuybykdj(lastM15,prelastM15)

    pricelogging.info("time=%s,fp1=%s,fp2=%s,fp3=%s,bymacd=%s,bykdj1=%s,bymacd5=%s,bykdj5=%s,bymacd15=%s,bykdj15=%s" % (time.ctime(current.time),f1po1,f1po5,f2po15,bymacd1,bykdj1,bymacd5,bykdj5,bymacd15,bykdj15))

    def valueMax(kline):
        if kline.close>kline.open:
            return kline.close
        return kline.open

    def valueMin(kline):
        if kline.close<kline.open:
            return kline.close
        return kline.open


    def buy(tag):
        global buyPrice1,buyPrice2,bidsList,asksList,buy1Time,buy2Time,buyTriggerTime,buyPrice3,downToUp,upToDown,middleToUp,spec,xspec,sellSpec,xbuy,xkdj,up15,up5,kk1pos,kk5pos,kk15pos,m5data

        if buyPrice1==None:
            buy1Time = current.time
            buy2Time = lastM5.time
            buyPrice1 = current.close
            sellSpec = lastM5.j - lastM5.k
            m5data = None
            kk1pos = f1po1
            kk5pos = f1po5
            pricelogging.info("tbuy-%s,-%s,time=%s,deciderTime=%s,spec=%s" % (tag,buyPrice1,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),spec))
            return
        else:
            pricelogging.info("tbuy-%s-buy-disable,time=%s" % (tag,time.ctime(stock1Min.lastKline().time)) )




    xdata = stock1Min.searchKDJRange()
    x5data = stock5Min.searchKDJRange()

    pricelogging.info(xdata)

    def zs(xt):

        if xt[0][2] == "DOWN" :
            xmax1 = xt[0][1][0]
            xmin1 = xt[0][1][1]

            xmax2 = xt[1][0][0]
            xmin2 = xt[1][0][1]

            xmax3 = xt[2][1][0]
            xmin3 = xt[2][1][1]

            xmax4 = xt[3][0][0]
            xmin4 = xt[3][0][1]

            xmax5 = xt[4][1][0]
            xmin5 = xt[4][1][1]

            if xmax2 < xmax4 and xmin3 < xmin5:  # 下降趋势
                if xmax2 < xmin5:  # 3卖
                    return (xmin3,xmax2,xt[2][1][2],xt[1][0][2])
                else:
                    return (max(xmin3,xmin5),min(xmax2,xmax4),xt[2][1][2],xt[1][0][2])  #慢下降
            else:
                return (max(xmin3,xmin5),min(xmax2,xmax4),xt[2][1][2],xt[1][0][2])   # 上涨趋势

        if xt[0][2] == "UP" :
            xmax1 = xt[0][0][0]
            xmin1 = xt[0][0][1]

            xmax2 = xt[1][1][0]
            xmin2 = xt[1][1][1]

            xmax3 = xt[2][0][0]
            xmin3 = xt[2][0][1]

            xmax4 = xt[3][1][0]
            xmin4 = xt[3][1][1]

            xmax5 = xt[4][0][0]
            xmin5 = xt[4][0][1]

            if xmax3 > xmax5 and xmin2 > xmin4:  # 上涨趋势
                if xmin2 > xmax5: #3 买
                    return (xmin2,xmax3,xt[1][1][2],xt[2][0][2])
                else:
                    return (max(xmin2,xmin4),min(xmax3,xmax5),xt[1][1][2],xt[2][0][2])
            else:
                return (max(xmin2,xmin4),min(xmax3,xmax5),xt[1][1][2],xt[2][0][2])

    def sell(tag):
        global buyPrice1,buyPrice2,bidsList,asksList,buy1Time,buy2Time,buyTriggerTime,buyPrice3,downToUp,upToDown,middleToUp,spec,xspec,sellSpec,xbuy,xkdj,up15,up5,kk1pos,kk5pos,kk15pos,m5data
        if buyPrice1==None:
            pricelogging.info("tbuy-%s-sell-disable,time=%s" % (tag,time.ctime(stock1Min.lastKline().time)) )
            return

        xzs = zs(xdata)
        xspec = True
        if tag!=90 and spec==43 and stock1Min.lastKline().close-buyPrice1<0:
            if lastm1.macd>0:
                if xdata[0][2] == "DOWN":
                    if xdata[2][1][0] < stock1Min.lastKline().close and abs(xdata[2][1][0]-stock1Min.lastKline().close)<2:
                        return
                elif xdata[0][2] == "UP":
                    if xdata[1][1][0] < stock1Min.lastKline().close and abs(xdata[1][1][0]-stock1Min.lastKline().close)<2:
                        return

        if tag!=90 and spec!=43 and stock1Min.lastKline().close-buyPrice1<0 and (lastM5.close > lastM5.boll or (prelastM5.j-prelastM5.k>0 and prelastM5.macd > pre2lastM5.macd)):
            if stock1Min.lastKline().close < xzs[1]+1 and stock1Min.lastKline().close>xzs[0]-1 and abs(xzs[0]-stock1Min.lastKline().close)<2:
                return
            if xdata[0][2] == "DOWN":
                if xdata[2][1][0] < stock1Min.lastKline().close and abs(xdata[2][1][0]-stock1Min.lastKline().close)<2:
                    return
            elif xdata[0][2] == "UP":
                if xdata[1][1][0] < stock1Min.lastKline().close and abs(xdata[1][1][0]-stock1Min.lastKline().close)<2:
                    return

        pricelogging.info("tbuy-%s-%s,sell-%s,diff=%s,time=%s" % (tag,buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = None
        spec = None
        buy1Time = None
        buy2Time = None
        xspec = None
        xkdj = None
        upToDown = None
        sellSpec = None
        m5data = None
        kk1pos = None
        kk5pos = None
        return

    def position(xt):
        if xt[0][2] == "DOWN" :

            xmax1 = xt[0][1][0]
            xmin1 = xt[0][1][1]

            xmax2 = xt[1][0][0]
            xmin2 = xt[1][0][1]

            xmax3 = xt[2][1][0]
            xmin3 = xt[2][1][1]

            xmax4 = xt[3][0][0]
            xmin4 = xt[3][0][1]

            xmax5 = xt[4][1][0]
            xmin5 = xt[4][1][1]

            if xmax2 < xmax4 and xmin3 < xmin5:  # 下降趋势
                if xmax2 < xmin5:  # 3卖
                    return 21
                else:
                    return 22  #慢下降
            elif xmax2 > xmax4 and xmin3 > xmin5:
                return 23   # 上涨趋势
            elif xmax2 < xmax4 and xmin3 > xmin5:
                return 24 #左包含,左边长,震荡
            elif xmax2 > xmax4 and xmin3 < xmin5:
                return 25 #右包含,有边长,震荡
            else:
                return 26 #震荡

        if xt[0][2] == "UP" :
            xmax1 = xt[0][0][0]
            xmin1 = xt[0][0][1]

            xmax2 = xt[1][1][0]
            xmin2 = xt[1][1][1]

            xmax3 = xt[2][0][0]
            xmin3 = xt[2][0][1]

            xmax4 = xt[3][1][0]
            xmin4 = xt[3][1][1]

            xmax5 = xt[4][0][0]
            xmin5 = xt[4][0][1]

            if xmax3 > xmax5 and xmin2 > xmin4:  # 上涨趋势
                if xmin2 > xmax5: #3 买
                    return 31
                else:
                    return 32  # 慢上涨

            elif xmax3 < xmax5 and xmin2 < xmin4:  # 下降趋势
                return 33
            elif xmin2 > xmin4 and xmax5 > xmax3:
                return 34 # 左包含,震荡
            elif xmin2 < xmin4 and xmax3 > xmax5:
                return 35 # 右包含,震荡
            else :
                return 36 #震荡


    def canb(xt,kline,prekline):
        px = position(xt)
        rzs = zs(xt)

        pricelogging.info("tbuy,-time=%s-%s-%s-px=%s,boll=%s,close=%s,kf=%s,xt1=%s" % (time.ctime(kline.time),rzs[0],rzs[1],px,kline.boll,kline.close,abs(kline.up-kline.close),xt[1][0][1]))
        if kline.close > kline.boll and rzs[0]>kline.close and kline.macd > 0 and kline.macd>prekline.macd:
            if abs(rzs[0]-kline.close)<2 and kline.macd < 0.6:
                return
            if kline.macd < 0.6:
                return
            if xdata[0][2] == "DOWN":
                return ("buy",1)
            elif xdata[0][2] == "UP" and (px==33 or px ==35):
                return ("buy",1)
        else:
            if px==24 or px == 34 or px == 31 or px==32:
                if kline.close > rzs[1] and kline.close>kline.open and kline.macd > prekline.macd:
                    return ("buy",3)
            else:
                if kline.close > rzs[0] and kline.close>kline.open and kline.macd > prekline.macd:
                    if xdata[0][2] == "DOWN" and xt[1][0][1]>rzs[0]:
                        if kline.close > xt[1][0][1]:
                            return ("buy",7)
                    else:
                        if abs(kline.close-rzs[1])>4:
                            return ("buy",5)

            if kline.close > rzs[1] and kline.close>kline.open and kline.macd > prekline.macd:
                if xdata[0][2] == "DOWN" and xt[1][0][1]>rzs[0]:
                    if kline.close > xt[1][0][1]:
                        return ("buy",7)
                else:
                    return ("buy",4)

    def cans(xt,kline,prekline):
        px = position(xt)
        rzs = zs(xt)

        pricelogging.info("tbuy,-stime=%s-%s-%s-px=%s" % (time.ctime(kline.time),rzs[0],rzs[1],px))
        if (px == 31 or px == 32) and (kline.macd<0) and kline.j-kline.k <0 and kline.close < xt[2][0][0]:
            return ("sell",31)

        if (px == 23) and (kline.macd<0) and kline.j-kline.k <0 and xt[1][0][0] < xt[3][0][0]:
            return ("sell",32)

        if kline.close < rzs[0] and kline.macd < prekline.macd:
            return ("sell",11)

        if kline.close < rzs[1] and kline.macd < prekline.macd:
            return ("sell",21)


    def canb2(xt,kline,prekline):
        px5 = position(x5data)
        rzs5 = zs(x5data)

        px = position(xt)
        rzs = zs(xt)

        fdata = stock1Min.findInFiveData()

        if kline.close > kline.boll and rzs[0]>kline.close and kline.macd>prekline.macd and lastM5.macd>prelastM5.macd:
            if fdata[len(fdata)-1].close > fdata[0].close:
                return ("buy",43)
        else:
            if kline.close > rzs5[1] and lastM5.macd > 3:
                if kline.close > rzs[1] and kline.close>kline.boll and kline.close>kline.open and kline.macd > prekline.macd:
                    return ("buy",38)

                if kline.close > rzs[0] and kline.close>kline.boll and kline.close>kline.open and kline.macd > prekline.macd:
                    return ("buy",39)

            if kline.close > rzs5[0] and lastM5.macd > prelastM5.macd:
                if kline.close > rzs[1] and kline.close>kline.boll and kline.close>kline.open and kline.macd > prekline.macd:
                    return ("buy",33)

                if kline.close > rzs[0] and kline.close>kline.boll and kline.close>kline.open and kline.macd > prekline.macd:
                    return ("buy",31)

            elif kline.close > rzs5[0] and lastM5.macd < prelastM5.macd and lastM5.macd>0:
                if kline.close > rzs[1] and kline.close>kline.boll and kline.close>kline.open and kline.macd > prekline.macd and kline.macd>0:
                    return ("buy",32)

            elif kline.close<rzs5[0] and lastM5.macd > prelastM5.macd and lastM5.macd<0:
                if kline.close > rzs[0] and kline.close>kline.boll and kline.macd > prekline.macd:
                    return ("buy",35)

            elif kline.close<rzs5[0] and lastM5.macd > prelastM5.macd and lastM5.macd>0:
                if kline.close > rzs[1] and kline.macd > prekline.macd and kline.close>kline.boll:
                    return ("buy",37)

                if kline.close > rzs[0] and kline.close>kline.boll and kline.macd > prekline.macd:
                    return ("buy",36)

    ret = canb2(xdata,lastm1,prelastm1)
    if ret!=None and spec==43 and buyPrice1!=None:
        spec = ret[1]

    if buyPrice1==None:
        ret = canb2(xdata,lastm1,prelastm1)
        if ret!=None:
            spec = ret[1]
            buy1Time = lastm1.time
            buy(ret[1])
            return

    if buyPrice1!=None:
        if xspec == True and lastm1.close-buyPrice1>0:
            sell(90)

        px5 = position(x5data)
        rzs5 = zs(x5data)

        px = position(xdata)
        rzs = zs(xdata)

        ret = cans(xdata,lastm1,prelastm1)
        rzs = zs(xdata)

        if spec == 43 and lastm1.close < rzs[0] and lastm1.macd<prelastm1.macd and lastm1.j-lastm1.k<0:
            if lastm1.macd>0 and lastM5.macd > prelastM5.macd:
                pass
            else:
                sell(spec)

        if lastm1.macd < 0 and lastm1.macd < prelastm1.macd and lastm1.close<lastm1.boll:
            sell(62)
            return

        if lastm1.macd<prelastm1.macd and prelastm1.macd - lastm1.macd >= 0.4:
            sell(63)
            return

        if prelastM5.close < prelastM5.open and lastm1.macd<0.2 and lastm1.macd < prelastm1.macd:
            if lastm1.close > rzs5[1] and prelastM5.macd > pre2lastM5.macd:
                if lastm1.close<lastm1.boll:
                    sell(68)
            else:
                sell(67)
            return

        if lastM5.macd < prelastM5.macd:
            if lastM5.macd>0:
                if lastm1.close < rzs[0] and lastm1.macd < prelastm1.macd:
                    return sell(64)
            elif lastM5.macd<0:
                return sell(65)

        if lastm1.high>lastm1.up and lastm1.close < lastm1.open and lastm1.j < prelastm1.j:
            if xdata[0][2] == "UP":
                if abs(xdata[2][0][0]-lastm1.close)<1:
                    return sell(90)



def go16():
    global buyPrice1,buyPrice2,bidsList,asksList,buy1Time,buy2Time,buyTriggerTime,buyPrice3,downToUp,upToDown,middleToUp,spec,xspec,sellSpec,xbuy,xkdj,up15,up5,kk1pos,kk5pos,kk15pos,m5data
    m5up,m5down,m5next = stock5Min.forecastClose()
    m1up,m1down,m1next = stock1Min.forecastClose()
    lastM5 = stock5Min.lastKline()
    prelastM5 = stock5Min.preLastKline()
    pre2lastM5 = stock5Min.pre2LastKline()
    current = stock1Min.lastKline()
    lastm1 = stock1Min.preLastKline()
    prelastm1 = stock1Min.pre2LastKline()
    lastM15 = stock15Min.lastKline()

    lastM15 = stock15Min.lastKline()
    prelastM15 = stock15Min.preLastKline()
    pre2lastM15 = stock15Min.pre2LastKline()

    if current.time-lastM5.time>=5*60:
        return

    if current.time == buy1Time:
        return

    f1po1,f1po5 = ply.pl(stock1Min,stock5Min,"1","5",5)
    f2po5,f2po15 = ply.pl(stock5Min,stock15Min,"5","15",15)

    bymacd1 = ply.canbuybymacd(lastm1,prelastm1)
    bykdj1 = ply.canbuybykdj(lastm1,prelastm1)

    bymacd5 = ply.canbuybymacd(lastM5,prelastM5)
    bykdj5 = ply.canbuybykdj(lastM5,prelastM5)

    bymacd15 = ply.canbuybymacd(lastM15,prelastM15)
    bykdj15 = ply.canbuybykdj(lastM15,prelastM15)

    pricelogging.info("time=%s,fp1=%s,fp2=%s,fp3=%s,bymacd=%s,bykdj1=%s,bymacd5=%s,bykdj5=%s,bymacd15=%s,bykdj15=%s" % (time.ctime(current.time),f1po1,f1po5,f2po15,bymacd1,bykdj1,bymacd5,bykdj5,bymacd15,bykdj15))

    def valueMax(kline):
        if kline.close>kline.open:
            return kline.close
        return kline.open

    def valueMin(kline):
        if kline.close<kline.open:
            return kline.close
        return kline.open


    def buy(tag):
        global buyPrice1,buyPrice2,bidsList,asksList,buy1Time,buy2Time,buyTriggerTime,buyPrice3,downToUp,upToDown,middleToUp,spec,xspec,sellSpec,xbuy,xkdj,up15,up5,kk1pos,kk5pos,kk15pos,m5data

        if buyPrice1==None:
            buy1Time = current.time
            buy2Time = lastM5.time
            buyPrice1 = current.close
            sellSpec = lastM5.j - lastM5.k
            m5data = None
            kk1pos = f1po1
            kk5pos = f1po5
            pricelogging.info("tbuy-%s,-%s,time=%s,deciderTime=%s,spec=%s" % (tag,buyPrice1,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),spec))
            return
        else:
            pricelogging.info("tbuy-%s-buy-disable,time=%s" % (tag,time.ctime(stock1Min.lastKline().time)) )




    xdata = stock1Min.searchKDJRange()
    x5data = stock5Min.searchKDJRange()

    pricelogging.info(xdata)

    def zs(xt):

        if xt[0][2] == "DOWN" :
            xmax1 = xt[0][1][0]
            xmin1 = xt[0][1][1]

            xmax2 = xt[1][0][0]
            xmin2 = xt[1][0][1]

            xmax3 = xt[2][1][0]
            xmin3 = xt[2][1][1]

            xmax4 = xt[3][0][0]
            xmin4 = xt[3][0][1]

            xmax5 = xt[4][1][0]
            xmin5 = xt[4][1][1]

            if xmax2 < xmax4 and xmin3 < xmin5:  # 下降趋势
                if xmax2 < xmin5:  # 3卖
                    return (xmin3,xmax2,xt[2][1][2],xt[1][0][2])
                else:
                    return (max(xmin3,xmin5),min(xmax2,xmax4),xt[2][1][2],xt[1][0][2])  #慢下降
            else:
                return (max(xmin3,xmin5),min(xmax2,xmax4),xt[2][1][2],xt[1][0][2])   # 上涨趋势

        if xt[0][2] == "UP" :
            xmax1 = xt[0][0][0]
            xmin1 = xt[0][0][1]

            xmax2 = xt[1][1][0]
            xmin2 = xt[1][1][1]

            xmax3 = xt[2][0][0]
            xmin3 = xt[2][0][1]

            xmax4 = xt[3][1][0]
            xmin4 = xt[3][1][1]

            xmax5 = xt[4][0][0]
            xmin5 = xt[4][0][1]

            if xmax3 > xmax5 and xmin2 > xmin4:  # 上涨趋势
                if xmin2 > xmax5: #3 买
                    return (xmin2,xmax3,xt[1][1][2],xt[2][0][2])
                else:
                    return (max(xmin2,xmin4),min(xmax3,xmax5),xt[1][1][2],xt[2][0][2])
            else:
                return (max(xmin2,xmin4),min(xmax3,xmax5),xt[1][1][2],xt[2][0][2])

    def sell(tag):
        global buyPrice1,buyPrice2,bidsList,asksList,buy1Time,buy2Time,buyTriggerTime,buyPrice3,downToUp,upToDown,middleToUp,spec,xspec,sellSpec,xbuy,xkdj,up15,up5,kk1pos,kk5pos,kk15pos,m5data
        if buyPrice1==None:
            pricelogging.info("tbuy-%s-sell-disable,time=%s" % (tag,time.ctime(stock1Min.lastKline().time)) )
            return
        '''
        xzs = zs(xdata)
        xspec = True
        if tag!=90 and spec==43 and stock1Min.lastKline().close-buyPrice1<0:
            if lastm1.macd>0:
                if xdata[0][2] == "DOWN":
                    if xdata[2][1][0] < stock1Min.lastKline().close and abs(xdata[2][1][0]-stock1Min.lastKline().close)<2:
                        return
                elif xdata[0][2] == "UP":
                    if xdata[1][1][0] < stock1Min.lastKline().close and abs(xdata[1][1][0]-stock1Min.lastKline().close)<2:
                        return

        if tag!=90 and spec!=43 and stock1Min.lastKline().close-buyPrice1<0 and (lastM5.close > lastM5.boll or (prelastM5.j-prelastM5.k>0 and prelastM5.macd > pre2lastM5.macd)):
            if stock1Min.lastKline().close < xzs[1]+1 and stock1Min.lastKline().close>xzs[0]-1 and abs(xzs[0]-stock1Min.lastKline().close)<2:
                return
            if xdata[0][2] == "DOWN":
                if xdata[2][1][0] < stock1Min.lastKline().close and abs(xdata[2][1][0]-stock1Min.lastKline().close)<2:
                    return
            elif xdata[0][2] == "UP":
                if xdata[1][1][0] < stock1Min.lastKline().close and abs(xdata[1][1][0]-stock1Min.lastKline().close)<2:
                    return
            '''
        pricelogging.info("tbuy-%s-%s,sell-%s,diff=%s,time=%s" % (tag,buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = None
        spec = None
        buy1Time = None
        buy2Time = None
        xspec = None
        xkdj = None
        upToDown = None
        sellSpec = None
        if xdata[0][2] == "DOWN":
            buyTriggerTime = xdata[1][0][2]
        if xdata[0][2] == "UP" :
            buyTriggerTime = xdata[1][1][2]
        m5data = None
        kk1pos = None
        kk5pos = None
        return

    def position(xt):
        if xt[0][2] == "DOWN" :

            xmax1 = xt[0][1][0]
            xmin1 = xt[0][1][1]

            xmax2 = xt[1][0][0]
            xmin2 = xt[1][0][1]

            xmax3 = xt[2][1][0]
            xmin3 = xt[2][1][1]

            xmax4 = xt[3][0][0]
            xmin4 = xt[3][0][1]

            xmax5 = xt[4][1][0]
            xmin5 = xt[4][1][1]

            if xmax2 < xmax4 and xmin3 < xmin5:  # 下降趋势
                if xmax2 < xmin5:  # 3卖
                    return 21
                else:
                    return 22  #慢下降
            elif xmax2 > xmax4 and xmin3 > xmin5:
                return 23   # 上涨趋势
            elif xmax2 < xmax4 and xmin3 > xmin5:
                return 24 #左包含,左边长,震荡
            elif xmax2 > xmax4 and xmin3 < xmin5:
                return 25 #右包含,有边长,震荡
            else:
                return 26 #震荡

        if xt[0][2] == "UP" :
            xmax1 = xt[0][0][0]
            xmin1 = xt[0][0][1]

            xmax2 = xt[1][1][0]
            xmin2 = xt[1][1][1]

            xmax3 = xt[2][0][0]
            xmin3 = xt[2][0][1]

            xmax4 = xt[3][1][0]
            xmin4 = xt[3][1][1]

            xmax5 = xt[4][0][0]
            xmin5 = xt[4][0][1]

            if xmax3 > xmax5 and xmin2 > xmin4:  # 上涨趋势
                if xmin2 > xmax5: #3 买
                    return 31
                else:
                    return 32  # 慢上涨

            elif xmax3 < xmax5 and xmin2 < xmin4:  # 下降趋势
                return 33
            elif xmin2 > xmin4 and xmax5 > xmax3:
                return 34 # 左包含,震荡
            elif xmin2 < xmin4 and xmax3 > xmax5:
                return 35 # 右包含,震荡
            else :
                return 36 #震荡


    def canb3(xt,kline,prekline):
        px5 = position(x5data)
        rzs5 = zs(x5data)

        px = position(xt)
        rzs = zs(xt)

        fdata = stock1Min.findInFiveData()

        pricelogging.info("tbuy,-time=%s-%s-%s-px=%s,5p=%s,%s" % (time.ctime(kline.time),rzs[0],rzs[1],px,rzs5[0],rzs5[1]))


        if x5data[0][2] == "DOWN":
            pricelogging.info("tbuy0")
            if kline.close > kline.boll and rzs[0]>kline.close and kline.macd>prekline.macd:
                if lastM5.j-lastM5.k<0 and lastM5.macd<prelastM5.macd:
                    if not ((kline.close>kline.boll and kline.macd>0) or (kline.close > rzs[1] and kline.macd > prekline.macd)):
                        pricelogging.info("tbuy1")
                        return

                if fdata[len(fdata)-1].close > fdata[0].close:
                    return ("buy",43)

            if x5data[0][1][1] != None:
                pricelogging.info("tbuy01=%s,%s",x5data[2][1][1],x5data[0][1][1])
                if lastM5.j-lastM5.k<0 and lastM5.macd<prelastM5.macd:
                    if not ((kline.close>kline.boll and kline.macd>0) or (kline.close > rzs[1] and kline.macd > prekline.macd)):
                        pricelogging.info("tbuy2")
                        return

                if kline.macd > prekline.macd and kline.j-kline.k>0:
                    if kline.close < rzs[1] and abs(kline.close - rzs[1])<1:
                        pricelogging.info("tbuy3")
                        return
                    if kline.close < rzs5[1] and abs(kline.close - rzs5[1])<1:
                        pricelogging.info("tbuy4")
                        return

                    if xdata[0][2] == "DOWN":
                        if buyTriggerTime == xdata[1][0][2]:
                            if kline.close < stock1Min.findBigKline(xdata[1][0][2].time).close:
                                pricelogging.info("tbuy5")
                                return

                    if xdata[0][2] == "UP":
                        if buyTriggerTime == xdata[1][1][2]:
                            if kline.close < stock1Min.findBigKline(xdata[1][1][2].time).close:
                                pricelogging.info("tbuy6")
                                return

                    if x5data[0][1][1]<x5data[2][1][1] and x5data[2][1][1]-x5data[0][1][1]>3:
                        if kline.close<kline.boll:
                            pricelogging.info("tbuy51")
                            return

                    return ("buy",44)
                if kline.j > prekline.j and kline.macd > prekline.macd and kline.close > rzs[0]:
                    if kline.close < rzs[1] and abs(kline.close - rzs[1])<1:
                        pricelogging.info("tbuy7")
                        return
                    if kline.close < rzs5[1] and abs(kline.close - rzs5[1])<1:
                        pricelogging.info("tbuy8")
                        return

                    if xdata[0][2] == "DOWN":
                        if buyTriggerTime == xdata[1][0][2]:
                            if kline.close < stock1Min.findBigKline(xdata[1][0][2].time).close:
                                pricelogging.info("tbuy9")
                                return

                    if xdata[0][2] == "UP":
                        if buyTriggerTime == xdata[1][1][2]:
                            if kline.close < stock1Min.findBigKline(xdata[1][1][2].time).close:
                                pricelogging.info("tbuy10")
                                return

                    if x5data[0][1][1]<x5data[2][1][1] and x5data[2][1][1]-x5data[0][1][1]>3:
                        if kline.close<kline.boll:
                            pricelogging.info("tbuy51")
                            return

                    return ("buy",45)
            else:
                pricelogging.info("tbuy02")
                if abs(x5data[2][1][1]-lastM5.close)<2:
                    if kline.macd > prekline.macd and kline.j > prekline.j and kline.close > kline.open:
                        return ("buy",46)
        elif x5data[0][2] == "UP":
            if lastM5.close < lastM5.boll and lastM5.j>prelastM5.j:

                return
            pricelogging.info("tbuy11")
            if lastM5.macd>0 or (lastM5.j>prelastM5.j and lastM5.j-lastM5.k<0) or (lastM5.j-lastM5.k>0):
                if xdata[0][2] == "DOWN":
                    if buyTriggerTime == xdata[1][0][2]:
                        if kline.close > stock1Min.findBigKline(xdata[1][0][2].time).close:
                            return ("buy",33)
                    else:
                        if kline.close>kline.boll and kline.close>kline.open and kline.macd > prekline.macd and kline.close > xdata[2][1][1]:
                            return ("buy",33)

                        if kline.close<kline.boll and abs(kline.high-kline.boll)<0.5 and kline.j-kline.k>0 and kline.j>prekline.j and kline.close>kline.open and kline.macd > prekline.macd and kline.close > xdata[2][1][1]:
                            return ("buy",33)

                if xdata[0][2] == "UP":
                    if buyTriggerTime == xdata[1][1][2]:
                        if kline.close > stock1Min.findBigKline(xdata[1][1][2].time).close:
                            return ("buy",33)
                    else:
                        if kline.close>kline.boll and kline.close>kline.open and kline.macd > prekline.macd and kline.close > xdata[1][1][1] and kline.close > xdata[3][1][1]:
                            return ("buy",33)

                        if kline.close<kline.boll and abs(kline.high-kline.boll)<0.5 and kline.j-kline.k>0 and kline.j>prekline.j  and kline.close>kline.open and kline.macd > prekline.macd and kline.close > xdata[1][1][1] and kline.close > xdata[3][1][1]:
                            return ("buy",33)

    def xb5():
        global  xbuy,buyPrice3
        if x5data[0][2] == "UP":
            if (pre2lastM5.high >= pre2lastM5.up or (pre2lastM5.high < pre2lastM5.up and abs(pre2lastM5.high-pre2lastM5.up)<0.5)) and prelastM5.close < prelastM5.open and prelastM5.close < pre2lastM5.close and prelastM5.j<pre2lastM5.j:
                xbuy = True
                buyPrice3 = pre2lastM5.close

    def cansell3(xt,kline,prekline):
        px = position(xt)
        rzs = zs(xt)

        px5 = position(x5data)
        rzs5 = zs(x5data)

        #pricelogging.info("tbuy,-stime=%s-%s-%s-px=%s" % (time.ctime(kline.time),rzs[0],rzs[1],px))

        def xb():
            if x5data[0][2] == "UP" and x5data[1][1][1] > x5data[3][1][1] and prelastM5.j>pre2lastM5.j:
                if lastm1.close - buyPrice1>1:
                    return True
                if kline.close > kline.boll:
                    return False
                if kline.close < kline.boll and abs(kline.close-kline.boll)<0.3:
                    return False
                if lastm1.close - buyPrice1<0:
                    return False

            return True

        if xdata[0][2] == "UP":
            if (prekline.high >= prekline.up or (prekline.high < prekline.up and abs(prekline.high-prekline.up)<0.5)) and kline.close < kline.open and kline.close < prekline.close:
                hkline = stock1Min.findBigKline(xdata[1][1][2].time)
                pricelogging.info("h=%s,k=%s",hkline,kline)
                if hkline.close>hkline.open and hkline.open<kline.close:
                    if kline.close<kline.open and prekline.close<prekline.open and abs(kline.close-prekline.close)>0.3:
                        if not xb():
                            return
                        return ("sell",91)
                    if kline.j-kline.k<0:
                        if not xb():
                            return
                        return ("sell",92)
                    return
                if not xb():
                    return
                return ("sell",90)

        if spec ==33 and buy1Time == prekline.time and kline.close < kline.open and kline.j < prekline.j and kline.macd < prekline.macd:
            return ("sell",93)

        if xdata[0][2] == "UP":
            if spec == 33:
                if xdata[0][2] == "DOWN" and kline.close > kline.boll:
                    return
            if kline.close < xdata[1][1][1] and kline.macd < prekline.macd:
                return ("sell",51)
        elif xdata[0][2] == "DOWN":
            if spec == 33:
                if xdata[0][2] == "DOWN" and kline.close > kline.boll:
                    return
            if kline.close < xdata[2][1][1] and kline.macd < prekline.macd:
                return ("sell",52)


    if buyPrice1==None:
        ret = canb3(xdata,lastm1,prelastm1)
        rzs5 = zs(x5data)

        if xbuy!=True:
            xb5()
            pricelogging.info("tbuy - xvf=%s,%s",xbuy,buyPrice3)

        if xbuy == True:
            if (prelastM5.j-prelastM5.k<0 and prelastM5.j>pre2lastM5.j) or (lastm1.close>buyPrice3+0.6):
                xbuy = None
                buyPrice3 = None
            else:
                return

        if ret!=None:
            spec = ret[1]
            buy1Time = current.time
            buy2Time = lastM5.time
            xspec = rzs5[0]
            buy(ret[1])
            return

    if buyPrice1!=None:
        px = position(xdata)
        rzs = zs(xdata)
        px5 = position(x5data)
        rzs5 = zs(x5data)
        pricelogging.info("tbuy,-time=%s-%s-%s-px=%s,5p=%s,%s" % (time.ctime(lastm1.time),rzs[0],rzs[1],px,rzs5[0],rzs5[1]))

        xret = cansell3(xdata,lastm1,prelastm1)
        fdata = stock1Min.findInFiveData()

        if xbuy!=True:
            xb5()
            pricelogging.info("tbuy - xvf=%s,%s",xbuy,buyPrice3)


        if xret != None:
            if lastm1.close-buyPrice1<0 and lastm1.up-lastm1.dn<1.5 and lastm1.close > lastm1.dn:
                return
            sell(xret[1])
            return

def go17():
    global buyPrice1,buyPrice2,bidsList,lastbuyTime,asksList,buy1Time,buy2Time,buyTriggerTime,buyPrice3,downToUp,upToDown,middleToUp,spec,xspec,sellSpec,xbuy,xkdj,up15,up5,kk1pos,kk5pos,kk15pos,m5data
    m5up,m5down,m5next = stock5Min.forecastClose()
    m1up,m1down,m1next = stock1Min.forecastClose()
    lastM5 = stock5Min.lastKline()
    prelastM5 = stock5Min.preLastKline()
    pre2lastM5 = stock5Min.pre2LastKline()
    current = stock1Min.lastKline()
    lastm1 = stock1Min.preLastKline()
    prelastm1 = stock1Min.pre2LastKline()
    lastM15 = stock15Min.lastKline()

    lastM15 = stock15Min.lastKline()
    prelastM15 = stock15Min.preLastKline()
    pre2lastM15 = stock15Min.pre2LastKline()

    if current.time-lastM5.time>=5*60:
        return

    if current.time == buy1Time:
        return

    f1po1,f1po5 = ply.pl(stock1Min,stock5Min,"1","5",5)
    f2po5,f2po15 = ply.pl(stock5Min,stock15Min,"5","15",15)

    bymacd1 = ply.canbuybymacd(lastm1,prelastm1)
    bykdj1 = ply.canbuybykdj(lastm1,prelastm1)

    bymacd5 = ply.canbuybymacd(lastM5,prelastM5)
    bykdj5 = ply.canbuybykdj(lastM5,prelastM5)

    bymacd15 = ply.canbuybymacd(lastM15,prelastM15)
    bykdj15 = ply.canbuybykdj(lastM15,prelastM15)

    pricelogging.info("time=%s,fp1=%s,fp2=%s,fp3=%s,bymacd=%s,bykdj1=%s,bymacd5=%s,bykdj5=%s,bymacd15=%s,bykdj15=%s" % (time.ctime(current.time),f1po1,f1po5,f2po15,bymacd1,bykdj1,bymacd5,bykdj5,bymacd15,bykdj15))

    def valueMax(kline):
        if kline.close>kline.open:
            return kline.close
        return kline.open

    def valueMin(kline):
        if kline.close<kline.open:
            return kline.close
        return kline.open


    def buy(tag):
        global buyPrice1,lastbuyTime,buyPrice2,bidsList,asksList,buy1Time,buy2Time,buyTriggerTime,buyPrice3,downToUp,upToDown,middleToUp,spec,xspec,sellSpec,xbuy,xkdj,up15,up5,kk1pos,kk5pos,kk15pos,m5data
        if lastbuyTime == lastM5.time:
            pricelogging.info("tbuy-%s-buy-disable,time=%s" % (tag,time.ctime(stock1Min.lastKline().time)) )
            return

        if buyPrice1==None:
            buy1Time = current.time
            buy2Time = lastM5.time
            buyPrice1 = current.close
            m5data = None
            kk1pos = f1po1
            kk5pos = f1po5
            buyTriggerTime = None
            pricelogging.info("tbuy-%s,-%s,time=%s,deciderTime=%s,spec=%s" % (tag,buyPrice1,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),spec))
            return
        else:
            pricelogging.info("tbuy-%s-buy-disable,time=%s" % (tag,time.ctime(stock1Min.lastKline().time)) )




    xdata = stock1Min.searchKDJRange()
    x5data = stock5Min.searchKDJRange()

    xkdjdata = stock1Min.searchKDJTopAndDown()
    x5kdjdata = stock5Min.searchKDJTopAndDown()

    pricelogging.info(xdata)
    pricelogging.info(xkdjdata)
    pricelogging.info(x5kdjdata)

    def zs(xt):
        if xt[0][2] == "DOWN" :
            xmax1 = xt[0][1][0]
            xmin1 = xt[0][1][1]

            xmax2 = xt[1][0][0]
            xmin2 = xt[1][0][1]

            xmax3 = xt[2][1][0]
            xmin3 = xt[2][1][1]

            xmax4 = xt[3][0][0]
            xmin4 = xt[3][0][1]

            xmax5 = xt[4][1][0]
            xmin5 = xt[4][1][1]

            if xmax2 < xmax4 and xmin3 < xmin5:  # 下降趋势
                if xmax2 < xmin5:  # 3卖
                    return (xmin3,xmax2,xt[2][1][2],xt[1][0][2])
                else:
                    return (max(xmin3,xmin5),min(xmax2,xmax4),xt[2][1][2],xt[1][0][2])  #慢下降
            else:
                return (max(xmin3,xmin5),min(xmax2,xmax4),xt[2][1][2],xt[1][0][2])   # 上涨趋势

        if xt[0][2] == "UP" :
            xmax1 = xt[0][0][0]
            xmin1 = xt[0][0][1]

            xmax2 = xt[1][1][0]
            xmin2 = xt[1][1][1]

            xmax3 = xt[2][0][0]
            xmin3 = xt[2][0][1]

            xmax4 = xt[3][1][0]
            xmin4 = xt[3][1][1]

            xmax5 = xt[4][0][0]
            xmin5 = xt[4][0][1]

            if xmax3 > xmax5 and xmin2 > xmin4:  # 上涨趋势
                if xmin2 > xmax5: #3 买
                    return (xmin2,xmax3,xt[1][1][2],xt[2][0][2])
                else:
                    return (max(xmin2,xmin4),min(xmax3,xmax5),xt[1][1][2],xt[2][0][2])
            else:
                return (max(xmin2,xmin4),min(xmax3,xmax5),xt[1][1][2],xt[2][0][2])

    def sell(tag):
        global buyPrice1,lastbuyTime,buyPrice2,bidsList,asksList,buy1Time,buy2Time,buyTriggerTime,buyPrice3,downToUp,upToDown,middleToUp,spec,xspec,sellSpec,xbuy,xkdj,up15,up5,kk1pos,kk5pos,kk15pos,m5data
        if buyPrice1==None:
            pricelogging.info("tbuy-%s-sell-disable,time=%s" % (tag,time.ctime(stock1Min.lastKline().time)) )
            return
        '''
        xzs = zs(xdata)
        xspec = True
        if tag!=90 and spec==43 and stock1Min.lastKline().close-buyPrice1<0:
            if lastm1.macd>0:
                if xdata[0][2] == "DOWN":
                    if xdata[2][1][0] < stock1Min.lastKline().close and abs(xdata[2][1][0]-stock1Min.lastKline().close)<2:
                        return
                elif xdata[0][2] == "UP":
                    if xdata[1][1][0] < stock1Min.lastKline().close and abs(xdata[1][1][0]-stock1Min.lastKline().close)<2:
                        return

        if tag!=90 and spec!=43 and stock1Min.lastKline().close-buyPrice1<0 and (lastM5.close > lastM5.boll or (prelastM5.j-prelastM5.k>0 and prelastM5.macd > pre2lastM5.macd)):
            if stock1Min.lastKline().close < xzs[1]+1 and stock1Min.lastKline().close>xzs[0]-1 and abs(xzs[0]-stock1Min.lastKline().close)<2:
                return
            if xdata[0][2] == "DOWN":
                if xdata[2][1][0] < stock1Min.lastKline().close and abs(xdata[2][1][0]-stock1Min.lastKline().close)<2:
                    return
            elif xdata[0][2] == "UP":
                if xdata[1][1][0] < stock1Min.lastKline().close and abs(xdata[1][1][0]-stock1Min.lastKline().close)<2:
                    return
            '''
        pricelogging.info("tbuy-%s-%s,sell-%s,diff=%s,time=%s" % (tag,buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
        if stock1Min.lastKline().close-buyPrice1 > 0:
            lastbuyTime == None
        else:
            lastbuyTime = buy2Time
        buyPrice1 = None
        spec = None
        buy1Time = None
        buy2Time = None
        xspec = None
        xkdj = None
        upToDown = None
        sellSpec = None
        buyTriggerTime = lastM5.time
        m5data = None
        kk1pos = None
        kk5pos = None
        return

    def position(xt):
        if xt[0][2] == "DOWN" :

            xmax1 = xt[0][1][0]
            xmin1 = xt[0][1][1]

            xmax2 = xt[1][0][0]
            xmin2 = xt[1][0][1]

            xmax3 = xt[2][1][0]
            xmin3 = xt[2][1][1]

            xmax4 = xt[3][0][0]
            xmin4 = xt[3][0][1]

            xmax5 = xt[4][1][0]
            xmin5 = xt[4][1][1]

            if xmax2 < xmax4 and xmin3 < xmin5:  # 下降趋势
                if xmax2 < xmin5:  # 3卖
                    return 21
                else:
                    return 22  #慢下降
            elif xmax2 > xmax4 and xmin3 > xmin5:
                return 23   # 上涨趋势
            elif xmax2 < xmax4 and xmin3 > xmin5:
                return 24 #左包含,左边长,震荡
            elif xmax2 > xmax4 and xmin3 < xmin5:
                return 25 #右包含,有边长,震荡
            else:
                return 26 #震荡

        if xt[0][2] == "UP" :
            xmax1 = xt[0][0][0]
            xmin1 = xt[0][0][1]

            xmax2 = xt[1][1][0]
            xmin2 = xt[1][1][1]

            xmax3 = xt[2][0][0]
            xmin3 = xt[2][0][1]

            xmax4 = xt[3][1][0]
            xmin4 = xt[3][1][1]

            xmax5 = xt[4][0][0]
            xmin5 = xt[4][0][1]

            if xmax3 > xmax5 and xmin2 > xmin4:  # 上涨趋势
                if xmin2 > xmax5: #3 买
                    return 31
                else:
                    return 32  # 慢上涨

            elif xmax3 < xmax5 and xmin2 < xmin4:  # 下降趋势
                return 33
            elif xmin2 > xmin4 and xmax5 > xmax3:
                return 34 # 左包含,震荡
            elif xmin2 < xmin4 and xmax3 > xmax5:
                return 35 # 右包含,震荡
            else :
                return 36 #震荡


    def trzs(xt):
        if xt[0][0] == "DOWN" :
            return (valueMax(xt[1][1]),valueMin(xt[2][2]),valueMax(xt[3][1]))
        elif xt[0][0] == "UP":
            return (valueMin(xt[1][2]),valueMax(xt[2][1]),valueMin(xt[3][2]))

    def rrrzs(xt):
        if xt[0][0] == "DOWN" :
            return (valueMin(xt[0][2]),valueMin(xt[2][2]))
        elif xt[0][0] == "UP":
            return (valueMin(xt[1][2]),valueMin(xt[3][2]))

    def bolldown():
        if xkdjdata[0][0] == "DOWN":
            if stock1Min.touchBollDn(xkdjdata[1][1].time)==True:
                return valueMin(xkdjdata[0][2])
        if xkdjdata[0][0] == "UP":
            if stock1Min.touchBollDn(xkdjdata[2][1].time)==True:
                return valueMin(xkdjdata[1][2])

    def canb3(xt,kline,prekline):
        global  xbuy
        px5 = position(x5data)
        rzs5 = zs(x5data)

        px = position(xt)
        rzs = zs(xt)

        fdata = stock1Min.findInFiveData()
        gh = trzs(xkdjdata)
        gh5 = trzs(x5kdjdata)

        pricelogging.info("tbuy,-time=%s-%s-%s-px=%s,5p=%s,%s,=%s,5j=%s" % (time.ctime(kline.time),rzs[0],rzs[1],px,rzs5[0],rzs5[1],gh,gh5))
        pricelogging.info("kline=%s,=%s",lastm1,lastm1.time-prelastM5.time)
        pricelogging.info("kline=%s,=%s",lastm1,lastm1.time-prelastM5.time)

        if x5kdjdata[0][0] == "DOWN":
            if prelastM5.j - prelastM5.k>-9.8:
                if lastm1.time - prelastM5.time >=7*60:
                    if xkdjdata[0][0] == "UP":
                        if valueMin(xkdjdata[1][2]) > valueMin(xkdjdata[3][2]) and lastm1.macd>prelastm1.macd and lastm1.close>lastm1.open:
                            return 41
                        else:
                            if lastm1.macd>0 and lastm1.macd>prelastm1.macd and lastm1.close>lastm1.open:
                                return 43
                    if xkdjdata[0][0] == "DOWN":
                        if valueMin(xkdjdata[0][2]) > valueMin(xkdjdata[2][2]) and lastm1.macd>prelastm1.macd and lastm1.close>lastm1.open:
                            return 42
                        else:
                            if lastm1.macd>0 and lastm1.macd>prelastm1.macd and lastm1.close>lastm1.open:
                                return 44
            else:
                pricelogging.info("x5=%s",x5kdjdata[1][1])
                pricelogging.info("x=%s,",stock5Min.touchBollDn(x5kdjdata[1][1].time))
                pricelogging.info("x1=%s,p=%s,",prelastM5.close > x5kdjdata[0][2].close,x5kdjdata[0][2])
                if prelastM5.j > pre2lastM5.j and stock5Min.touchBollDn(x5kdjdata[1][1].time)==True and prelastM5.close > x5kdjdata[0][2].close:
                    dntime = stock5Min.touchBollDnTime(x5kdjdata[1][1].time)
                    pricelogging.info("dntime=%s",time.ctime(dntime))
                    if prelastM5.time > dntime:
                        if xkdjdata[0][0] == "UP":
                            pricelogging.info("k3=%s",xkdjdata[3][2])
                            pricelogging.info("k1=%s",xkdjdata[1][2])
                            if xkdjdata[3][2].time>=dntime:
                                if valueMin(xkdjdata[1][2]) > valueMin(xkdjdata[3][2]) and lastm1.macd>0:
                                    return 61
                        elif xkdjdata[0][0] == "DOWN" and lastm1.j-lastm1.k>0 and lastm1.macd>0:
                            pricelogging.info("k0=%s",xkdjdata[0][2])
                            pricelogging.info("k2=%s",xkdjdata[2][2])
                            if xkdjdata[3][2].time>=dntime:
                                if valueMin(xkdjdata[0][2]) > valueMin(xkdjdata[2][2]) and lastm1.macd>0 and lastm1.j-lastm1.k>0:
                                    return 62

        if x5kdjdata[0][0] == "UP" and lastM5.macd>0:
            if xbuy==True:
                xbuy=None
                if xkdjdata[0][0] == "DOWN":
                    if lastm1.j-lastm1.k>0 and lastm1.macd > prelastm1.macd:
                        return 73

            if xkdjdata[0][0] == "DOWN":
                if lastm1.macd > prelastm1.macd and lastm1.j>prelastm1.j and stock1Min.touchBollDn(xkdjdata[1][1].time)==True and lastm1.close > valueMin(xkdjdata[0][2]):
                    if abs(lastm1.up-lastm1.dn) > 5:
                        return 71

                '''
                if lastM5.macd>0 and lastm1.j-lastm1.k>0:
                    dntime = stock5Min.touchBollDnTime(x5kdjdata[2][1].time)
                    if xt[0][2] == "DOWN":
                        pricelogging.info("time=%s,xt=%s,xttime=%s,d1=%s,d2=%s",time.ctime(dntime),xt[0][2],time.ctime(xt[2][1][2].time),xt[0][1][1],xt[2][1][0])
                        if stock1Min.touchBollDn(xt[1][0][2].time) ==True:
                            if xt[2][1][2].time > dntime and xt[0][1][1]!=None and xt[0][1][1]>xt[2][1][0] and lastm1.macd > prelastm1.macd:
                                return 81
                    if xt[0][2] == "UP":
                        pricelogging.info("time=%s,xt=%s,xttime=%s,d1=%s,d2=%s",time.ctime(dntime),xt[0][2],time.ctime(xt[3][1][2].time),xt[1][1][1],xt[3][1][0])
                        if stock1Min.touchBollDn(xt[2][0][2].time) ==True:
                            if xt[3][1][2].time > dntime and xt[1][1][1]!=None and xt[1][1][1]>xt[3][1][0] and lastm1.macd > prelastm1.macd:
                                return 81
                '''
            if xkdjdata[0][0] == "UP":
                if lastm1.macd > prelastm1.macd and lastm1.macd >0 and lastm1.close>valueMax(xkdjdata[2][1]):
                    return 72

                if lastm1.macd > prelastm1.macd and lastm1.j>prelastm1.j and stock1Min.touchBollDn(xkdjdata[1][1].time)==True and lastm1.close > valueMin(xkdjdata[0][2]):
                    if abs(lastm1.up-lastm1.dn) > 5:
                        return 71

                '''
                if lastM5.macd>0 and lastm1.j-lastm1.k>0:
                    dntime = stock5Min.touchBollDnTime(x5kdjdata[2][1].time)
                    if xt[0][2] == "DOWN":
                        pricelogging.info("time=%s,xt=%s,xttime=%s,d1=%s,d2=%s",time.ctime(dntime),xt[0][2],time.ctime(xt[2][1][2].time),xt[0][1][1],xt[2][1][0])
                        if stock1Min.touchBollDn(xt[1][0][2].time) ==True:
                            if xt[2][1][2].time > dntime and xt[0][1][1]!=None and xt[0][1][1]>xt[2][1][0] and lastm1.macd > prelastm1.macd:
                                return 81
                    if xt[0][2] == "UP":
                        pricelogging.info("time=%s,xt=%s,xttime=%s,d1=%s,d2=%s",time.ctime(dntime),xt[0][2],time.ctime(xt[3][1][2].time),xt[1][1][1],xt[3][1][0])
                        if stock1Min.touchBollDn(xt[2][0][2].time) ==True:
                            if xt[3][1][2].time > dntime and xt[1][1][1]!=None and xt[1][1][1]>xt[3][1][0] and lastm1.macd > prelastm1.macd:
                                return 81
                '''

    def cansell3(xt,kline,prekline):
        px = position(xt)
        rzs = zs(xt)

        px5 = position(x5data)
        rzs5 = zs(x5data)


        gh = trzs(xkdjdata)
        gh5 = rrrzs(x5kdjdata)

        pricelogging.info("tbuy,-stime=%s-%s-%s-px=%s,5p=%s,%s,=%s,5j=%s" % (time.ctime(kline.time),rzs[0],rzs[1],px,rzs5[0],rzs5[1],gh,gh5))

        #pricelogging.info("tbuy,-stime=%s-%s-%s-px=%s" % (time.ctime(kline.time),rzs[0],rzs[1],px))

        if x5kdjdata[0][0] == "UP":
            if prelastM5.j - prelastM5.k<9.8:
                if xkdjdata[0][0] == "UP":
                    if valueMax(xkdjdata[0][1]) < valueMax(xkdjdata[2][1]) and lastm1.macd<prelastm1.macd:
                        return 51
                    else:
                        if lastm1.macd<0 and lastm1.macd<prelastm1.macd:
                            return 53
                if xkdjdata[0][0] == "DOWN":
                    if valueMax(xkdjdata[1][1]) < valueMax(xkdjdata[3][1]) and lastm1.macd<prelastm1.macd:
                        if xkdjdata[3][1].time < buy1Time:
                            if lastm1.close < valueMin(xkdjdata[1][1]):
                                return 52
                        else:
                            return 52
                    else:
                        if lastm1.macd<0 and lastm1.macd<prelastm1.macd:
                            return 54
            else:
                if xkdjdata[0][0] == "DOWN":
                    if buy1Time!=None and xkdjdata[3][1].time > buy1Time:
                        if valueMax(xkdjdata[1][1]) < valueMax(xkdjdata[3][1]) and lastm1.macd<prelastm1.macd:
                            return 56
                if xkdjdata[0][0] == "UP":
                    if buy1Time!=None and xkdjdata[2][1].time > buy1Time:
                        if valueMax(xkdjdata[0][1]) < valueMax(xkdjdata[2][1]) and lastm1.macd<prelastm1.macd and lastm1.macd<0:
                            return 56

            if prelastM5.j<pre2lastM5.j and prelastM5.macd<pre2lastM5.macd:
                if valueMin(x5kdjdata[1][2]) > valueMin(x5kdjdata[3][2]) and valueMax(x5kdjdata[2][1]) > valueMax(x5kdjdata[0][1]):
                    return 55

    if xbuy==True and lastm1.close<lastm1.boll:
        xbuy= None

    if buyPrice1==None:
        ret = canb3(xdata,lastm1,prelastm1)
        if ret!=None:
            spec = ret
            buy1Time = current.time
            buy2Time = lastM5.time
            xspec = x5kdjdata[0]
            buy(ret)

            if spec == 41 or spec == 42  or spec == 43 or spec == 44:
                m5data = bolldown()

                if xkdjdata[0][0] == "DOWN":
                    pricelogging.info("xdn=%s",xkdjdata[0][2])
                    pricelogging.info("xdn1=%s",xkdjdata[2][2])
                    pricelogging.info("xdn2=%s",xkdjdata[1][1])
                    pricelogging.info("xdn3=%s",current.close)
                    if valueMin(xkdjdata[0][2]) > valueMin(xkdjdata[2][2]) and current.close < valueMax(xkdjdata[1][1]):
                        sellSpec = valueMax(xkdjdata[1][1])
                if xkdjdata[0][0] == "UP":
                    pricelogging.info("xdn=%s",xkdjdata[1][2])
                    pricelogging.info("xdn1=%s",xkdjdata[3][2])
                    pricelogging.info("xdn2=%s",xkdjdata[2][1])
                    pricelogging.info("xdn3=%s",current.close)
                    if valueMin(xkdjdata[1][2]) > valueMin(xkdjdata[3][2]) and current.close < valueMax(xkdjdata[2][1]):
                        sellSpec = valueMax(xkdjdata[2][1])


    if buyPrice1!=None:
        pricelogging.info("sellspec=%s",sellSpec)

        if spec==71:
            if lastm1.time == buy1Time and lastm1.close<lastm1.open and abs(lastm1.close-lastm1.open)>1 and lastm1.j < prelastm1.j:
                sell(110)
                spec = None
                return

        if lastm1.time <= buy1Time:
            return

        if sellSpec !=None:
            if lastm1.macd<0:
                if lastm1.close < sellSpec:
                    sell(120)
                    sellSpec = None
                    return
                else:
                    sellSpec = None


        if spec==72  or spec==71 or spec==73:
            if lastm1.macd < prelastm1.macd:
                if spec == 73:
                    if xkdjdata[0][0] == "UP":
                        if valueMax(xkdjdata[0][1]) > valueMax(xkdjdata[2][1]):
                            spec = 63
                            return

                if spec==71 and current.close-buyPrice1<0 and lastm1.low > lastm1.dn and lastM5.macd>0:
                    return

                sell(spec)
                spec = None
                if xkdjdata[0][0] == "UP":
                    if lastm1.close > valueMax(xkdjdata[2][1]):
                        xbuy = True
            return

        if spec==41 or spec==42 or spec==43 or spec==44:
            if lastm1.j-lastm1.k<0 and lastm1.macd<prelastm1.macd and lastm1.close < buyPrice1:
                pricelogging.info("m5data=%s",m5data)
                if abs(lastm1.close-buyPrice1)<2 and m5data!=None and lastm1.close > m5data and prelastM5.macd>pre2lastM5.macd:
                    return
                sell(130)
                return

        if spec==81:
            if lastm1.j-lastm1.k<0 and lastm1.macd < prelastm1.macd:
                sell(140)
            return

        px = position(xdata)
        rzs = zs(xdata)
        px5 = position(x5data)
        rzs5 = zs(x5data)

        xret = cansell3(xdata,lastm1,prelastm1)
        fdata = stock1Min.findInFiveData()

        gh = trzs(xkdjdata)
        gh5 = rrrzs(x5kdjdata)


        if x5kdjdata[0][0]=="DOWN":
            if xkdjdata[0][0] == "DOWN":
                if valueMin(xkdjdata[0][2]) < valueMin(xkdjdata[2][2]) and lastm1.macd<prelastm1.macd:
                    sell(xret)
                    spec  = xret
                    return

        if xret != None:
            sell(xret)
            spec  = xret
            return


def go18():
    global buyPrice1,buyPrice2,bidsList,lastbuyTime,asksList,buy1Time,buy2Time,buyTriggerTime,buyPrice3,downToUp,upToDown,middleToUp,spec,xspec,sellSpec,xbuy,xkdj,up15,up5,kk1pos,kk5pos,kk15pos,m5data
    global fenx1,fenx5,lastfenx1,lastfenx5,buttomDown,buttomDownKline
    m5kdjzero,m5kdjbignext = stock5Min.forecastKDJClose()
    m5macdZero,m5macdbignext = stock5Min.forecastMacd()

    lastM5 = stock5Min.lastKline()
    prelastM5 = stock5Min.preLastKline()
    pre2lastM5 = stock5Min.pre2LastKline()
    current = stock1Min.lastKline()
    lastm1 = stock1Min.preLastKline()
    prelastm1 = stock1Min.pre2LastKline()
    lastM15 = stock15Min.lastKline()

    lastM15 = stock15Min.lastKline()
    prelastM15 = stock15Min.preLastKline()
    pre2lastM15 = stock15Min.pre2LastKline()

    if current.time-lastM5.time>=5*60:
        return

    if current.time == buy1Time:
        return


    def valueMax(kline):
        if kline.close>kline.open:
            return kline.close
        return kline.open

    def valueMin(kline):
        if kline.close<kline.open:
            return kline.close
        return kline.open


    def buy(tag):
        global buyPrice1,lastbuyTime,buyPrice2,bidsList,asksList,buy1Time,buy2Time,buyTriggerTime,buyPrice3,downToUp,upToDown,middleToUp,spec,xspec,sellSpec,xbuy,xkdj,up15,up5,kk1pos,kk5pos,kk15pos,m5data

        if buyPrice1==None:
            buy1Time = current.time
            buy2Time = lastM5.time
            buyPrice1 = current.close
            m5data = None
            buyTriggerTime = None
            pricelogging.info("tbuy-%s,-%s,time=%s,deciderTime=%s,spec=%s" % (tag,buyPrice1,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),spec))
            return
        else:
            pricelogging.info("tbuy-%s-buy-disable,time=%s" % (tag,time.ctime(stock1Min.lastKline().time)) )


    def sell(tag):
        global buyPrice1,lastbuyTime,buyPrice2,bidsList,asksList,buy1Time,buy2Time,buyTriggerTime,buyPrice3,downToUp,upToDown,middleToUp,spec,xspec,sellSpec,xbuy,xkdj,up15,up5,kk1pos,kk5pos,kk15pos,m5data
        if buyPrice1==None:
            pricelogging.info("tbuy-%s-sell-disable,time=%s" % (tag,time.ctime(stock1Min.lastKline().time)) )
            return
        '''
        xzs = zs(xdata)
        xspec = True
        if tag!=90 and spec==43 and stock1Min.lastKline().close-buyPrice1<0:
            if lastm1.macd>0:
                if xdata[0][2] == "DOWN":
                    if xdata[2][1][0] < stock1Min.lastKline().close and abs(xdata[2][1][0]-stock1Min.lastKline().close)<2:
                        return
                elif xdata[0][2] == "UP":
                    if xdata[1][1][0] < stock1Min.lastKline().close and abs(xdata[1][1][0]-stock1Min.lastKline().close)<2:
                        return

        if tag!=90 and spec!=43 and stock1Min.lastKline().close-buyPrice1<0 and (lastM5.close > lastM5.boll or (prelastM5.j-prelastM5.k>0 and prelastM5.macd > pre2lastM5.macd)):
            if stock1Min.lastKline().close < xzs[1]+1 and stock1Min.lastKline().close>xzs[0]-1 and abs(xzs[0]-stock1Min.lastKline().close)<2:
                return
            if xdata[0][2] == "DOWN":
                if xdata[2][1][0] < stock1Min.lastKline().close and abs(xdata[2][1][0]-stock1Min.lastKline().close)<2:
                    return
            elif xdata[0][2] == "UP":
                if xdata[1][1][0] < stock1Min.lastKline().close and abs(xdata[1][1][0]-stock1Min.lastKline().close)<2:
                    return
            '''
        pricelogging.info("tbuy-%s-%s,sell-%s,diff=%s,time=%s" % (tag,buyPrice1,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice1),time.ctime(stock1Min.lastKline().time)))
        buyPrice1 = None
        spec = None
        buy1Time = None
        buy2Time = None
        xspec = None
        xkdj = None
        upToDown = None
        sellSpec = None
        buyTriggerTime = None
        m5data = None
        kk1pos = None
        kk5pos = None
        return


    def canb3(xt,kline,prekline):
        global  xbuy,xspec,buyTriggerTime,buttomDown,buttomDownKline,buyPrice3,downToUp

        fdata = stock1Min.findInFiveData()

        kkdata = stock1Min.checkMacdUp()
        kkdata5 = stock5Min.checkMacdUp()

        pricelogging.info("xkline=%s",kkdata)

        if lastm1.macd<0:
            if kkdata[0].high < kkdata[2].low or (kkdata[0].low < kkdata[2].low and abs(kkdata[0].low-kkdata[2].low)>kkdata[2].boll-kkdata[2].dn):
                if prelastm1.mn["5"] < prelastm1.mn["15"] and prelastm1.mn["15"] < prelastm1.mn["30"] and prelastm1.mn["30"] < prelastm1.mn["60"]:
                    if lastm1.dif<lastm1.dea and lastm1.dif-lastm1.dea>-0.5 and lastm1.macd > prelastm1.macd and lastM5.macd>prelastM5.macd:
                        if prelastM5.mn["5"] < prelastM5.mn["15"] and prelastM5.mn["15"] < prelastM5.mn["30"] and prelastM5.mn["30"] < prelastM5.mn["60"]:
                            buyTriggerTime = (lastm1,stock1Min.checkvm(kkdata[0].time),kkdata[0])
                            return
                            #if valueMin(prelastM5) < prelastM5.mn["5"]:
                            #    return
                        if lastm1.mn["5"]>lastm1.mn["15"]:
                            return (42,stock1Min.checkvm(kkdata[0].time),kkdata[0])
                        elif lastm1.mn["5"]-lastm1.mn["15"]<5 and lastm1.mn["5"] > prelastm1.mn["5"] and lastm1.close>lastm1.mn["15"]:
                            return (43,stock1Min.checkvm(kkdata[0].time),kkdata[0])
        else:
            if kkdata[1].high < kkdata[3].low or (kkdata[0].low < kkdata[2].low and abs(kkdata[0].low-kkdata[2].low)>kkdata[2].boll-kkdata[2].dn):
                if prelastm1.mn["5"] < prelastm1.mn["15"] and prelastm1.mn["15"] < prelastm1.mn["30"] and prelastm1.mn["30"] < prelastm1.mn["60"]:
                    if lastm1.macd > 0 and lastm1.macd > prelastm1.macd and lastM5.macd>prelastM5.macd:
                        if prelastM5.mn["5"] < prelastM5.mn["15"] and prelastM5.mn["15"] < prelastM5.mn["30"] and prelastM5.mn["30"] < prelastM5.mn["60"]:
                            buyTriggerTime = (lastm1,stock1Min.checkvm(kkdata[1].time),kkdata[1])
                            return
                        if lastm1.mn["5"]>lastm1.mn["15"]:
                            return (42,stock1Min.checkvm(kkdata[1].time),kkdata[1])
                        elif lastm1.mn["5"]-lastm1.mn["15"]<5 and lastm1.mn["5"] > prelastm1.mn["5"]:
                            return (43,stock1Min.checkvm(kkdata[1].time),kkdata[1])


        if buyTriggerTime != None:
            if valueMin(prelastM5) >= prelastM5.mn["5"]:
                buyPrice3 = lastm1

        if buyPrice3!=None and buyTriggerTime!=None:
            if lastm1.macd < 0 and lastm1.macd>prelastm1.macd and valueMin(lastm1) > buyTriggerTime[1]:
                distance = stock1Min.checkdistance(buyTriggerTime[2].time)
                if distance  == 1:
                    xt = (41,buyTriggerTime[1],buyTriggerTime[2])
                    buyTriggerTime = None
                    buyPrice3 = None
                    return xt
                elif distance > 1:
                    buyTriggerTime = None
                    buyPrice3 = None

            elif lastm1.macd > 0 and prelastm1.macd<0 and valueMin(lastm1) > buyTriggerTime[1]:
                distance = stock1Min.checkdistance(buyTriggerTime[2].time)
                if distance == 2:
                    xt = (44,buyTriggerTime[1],buyTriggerTime[2])
                    buyTriggerTime = None
                    buyPrice3 = None
                    return xt
                elif distance > 2:
                    buyTriggerTime = None
                    buyPrice3 = None

        if downToUp==True:
            if lastm1.macd<0 and lastm1.macd > prelastm1.macd and lastm1.mn["5"]>prelastm1.mn["5"]:
                if valueMin(kkdata[0]) > buttomDown:
                    return (45,buttomDown,buttomDownKline)
                else:
                    downToUp = None
                    buttomDown = None
                    buttomDownKline = None


    def canbuy4():
        kkdata5 = stock5Min.checkMacdUp()
        if lastM5.macd>0:
            if kkdata5[1].high < kkdata5[3].low:
                if prelastM5.mn["5"] < prelastM5.mn["15"] and prelastM5.mn["15"] < prelastM5.mn["30"] and prelastM5.mn["30"] < prelastM5.mn["60"]:
                    if lastM5.macd > prelastM5.macd:
                        if lastM5.mn["5"]>lastM5.mn["15"]:
                            return 92
                if prelastM5.mn["5"] > prelastM5.mn["15"] and prelastM5.mn["15"] > prelastM5.mn["30"] and prelastM5.mn["30"] > prelastM5.mn["60"]:
                    if lastM5.macd > prelastM5.macd:
                        return 94


    def canbuy5():
        kkdata = stock1Min.checkMacdUp()
        if lastm1.close > lastm1.mn["60"] and prelastm1.mn["5"] > prelastm1.mn["15"] and lastm1.close> prelastm1.mn["5"]:
            if lastm1.macd>0 and lastm1.macd>prelastm1.macd:
                if prelastM5.macd>pre2lastM5.macd:
                    return (72,kkdata[2].high,kkdata[2])

    def cansell3(xt,kline,prekline):
        global sellSpec,spec,up15,up5,m5data,downToUp,buttomDown

        kkdata = stock1Min.checkMacdUp()

        if spec==43 or spec==42 or spec==41 or spec==44 or spec==45:
            if lastm1.close<sellSpec:
                return 110

            if spec==43 or spec==42:
                if (up5==None or up5==1) and  lastm1.mn["5"] > lastm1.mn["15"] and lastm1.mn["15"] > lastm1.mn["30"] and lastm1.mn["30"] > lastm1.mn["60"]:
                    if lastm1.close > m5data.high + (m5data.boll - m5data.dn):
                        downToUp = True

                if downToUp == True and lastm1.mn["5"]<lastm1.mn["15"] and lastm1.macd<prelastm1.macd:
                    buttomDown = sellSpec
                    return 40

            if lastm1.macd<0:
                if up5 == None:
                    up5 = 1
                else:
                    up5 +=1

                if up5==1:
                    up15 = kkdata[1]
                    if up15.macd>100:
                        up5 = None
                else:
                    if up15.macd > 100 or up15.macd<-60:
                        up5 = None
                        up15 = None
                        return
                    pricelogging.info("tbuyqq=%s,up15=%s,t=%s,t1=%s",kkdata[1],up15,kkdata[1].close>up15.high + (up15.boll-up15.dn),kkdata[1].close>up15.high + (up15.boll-up15.dn))
                    if kkdata[1].close>up15.high + (up15.boll-up15.dn):
                        if prelastm1.mn["30"] > prelastm1.mn["60"] and prelastm1.mn["5"]>prelastm1.mn["30"] and lastm1.mn["5"]<lastm1.mn["30"]:
                            return 43

                    if kkdata[1].close>up15.high + (up15.boll-up15.dn):
                        if kkdata[1].high < kkdata[3].low:
                            return 41


        '''
        if spec==43:
            if lastm1.close<sellSpec:
                return 110
            if lastm1.time-buy1Time>3*60:
                if lastm1.mn["5"] < lastm1.mn["15"]:
                    if lastm1.close > buyPrice1 :
                        return 120
            if lastm1.mn["5"] > lastm1.mn["15"]:
                spec = 42
            return

        if spec==42:
            if lastm1.mn["5"] < lastm1.mn["15"] and lastm1.macd<prelastm1.macd:
                if lastm1.close<sellSpec:
                    return 110
                else:
                    if lastm1.close > buyPrice1:
                        return 51


        if spec==72:
            if lastm1.close-buyPrice1>15:
                if lastm1.mn["5"] < lastm1.mn["15"] and lastm1.macd<prelastm1.macd:
                    return 83
            else:
                if lastm1.macd<prelastm1.macd:
                    return 84

        '''
        '''
        if lastm1.macd<prelastm1.macd and lastm1.mn["5"]<prelastm1.mn["5"]:
            if lastM5.macd>0 and lastM5.macd > prelastM5.macd:
                return

            if lastM5.macd>prelastM5.macd and prelastM5.close>prelastM5.open:
                if prelastM5.macd<0:
                    if kkdata[0].low < kkdata[2].low:
                        return

            if lastM5.mn["5"] < prelastM5.mn["15"]:
                return 61
            else:
                return
        '''


    pricelogging.info("m5macdbig=%s",m5macdbignext)
    pricelogging.info("xkline=%s",lastm1)

    if buyPrice1==None:
        ret = canb3(None,lastm1,prelastm1)
        if ret!=None:
            if type(ret)==int:
                spec = ret
                sellSpec = None
            else:
                spec = ret[0]
                sellSpec = ret[1]
                buttomDownKline = ret[2]

            buy1Time = current.time
            buy2Time = lastM5.time
            buy(ret)
            m5data = lastm1
            downToUp = None
            buyTriggerTime = None
            buyPrice3 = None
            return



    if buyPrice1!=None:
        pricelogging.info("sellspec=%s",sellSpec)


        xret = cansell3(None,lastm1,prelastm1)

        if xret != None:
            sell(xret)
            xspec = None
            sellSpec = None
            up15 = None
            up5 = None
            buyTriggerTime = None
            buyPrice3 = None
            return


def go19():
    global buyPrice1,buyPrice2,bidsList,lastbuyTime,asksList,buy1Time,buy2Time,buyTriggerTime,buyPrice3,downToUp,upToDown,middleToUp,spec,xspec,sellSpec,xbuy,xkdj,up15,up5,kk1pos,kk5pos,kk15pos,m5data
    global fenx1,fenx5,lastfenx1,lastfenx5,buttomDown,buttomDownKline,up5Copy,buyTriggerTimeCopy
    m5kdjzero,m5kdjbignext = stock5Min.forecastKDJClose()
    m5macdZero,m5macdbignext = stock5Min.forecastMacd()

    lastM5 = stock5Min.lastKline()
    prelastM5 = stock5Min.preLastKline()
    pre2lastM5 = stock5Min.pre2LastKline()
    current = stock1Min.lastKline()
    lastm1 = stock1Min.preLastKline()
    prelastm1 = stock1Min.pre2LastKline()
    prelastm2 = stock1Min.preMyLastKline(3)
    lastM15 = stock15Min.lastKline()

    lastM15 = stock15Min.lastKline()
    prelastM15 = stock15Min.preLastKline()
    pre2lastM15 = stock15Min.pre2LastKline()

    if current.time-lastM5.time>=5*60:
        return

    if current.time == buy1Time:
        return


    def valueMax(kline):
        if kline.close>kline.open:
            return kline.close
        return kline.open

    def valueMin(kline):
        if kline.close<kline.open:
            return kline.close
        return kline.open


    def buy(tag):
        global buyPrice1,lastbuyTime,buyPrice2,bidsList,asksList,buy1Time,buy2Time,buyTriggerTime,buyPrice3,downToUp,upToDown,middleToUp,spec,xspec,sellSpec,xbuy,xkdj,up15,up5,kk1pos,kk5pos,kk15pos,m5data

        if buyPrice1==None:
            buy1Time = current.time
            buy2Time = lastM5.time
            buyPrice1 = current.close
            m5data = None
            buyTriggerTime = None
            pricelogging.info("tbuy-%s,-%s,time=%s,deciderTime=%s,spec=%s" % (tag,buyPrice1,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),spec))
            return
        else:
            pricelogging.info("tbuy-%s-buy-disable,time=%s" % (tag,time.ctime(stock1Min.lastKline().time)) )


    def sell(tag):
        global buyPrice1,lastbuyTime,buyPrice2,bidsList,asksList,buy1Time,buy2Time,buyTriggerTime,buyPrice3,downToUp,upToDown,middleToUp,spec,xspec,sellSpec,xbuy,xkdj,up15,up5,kk1pos,kk5pos,kk15pos,m5data
        if buyPrice1==None:
            pricelogging.info("tbuy-%s-sell-disable,time=%s" % (tag,time.ctime(stock1Min.lastKline().time)) )
            return
        '''
        xzs = zs(xdata)
        xspec = True
        if tag!=90 and spec==43 and stock1Min.lastKline().close-buyPrice1<0:
            if lastm1.macd>0:
                if xdata[0][2] == "DOWN":
                    if xdata[2][1][0] < stock1Min.lastKline().close and abs(xdata[2][1][0]-stock1Min.lastKline().close)<2:
                        return
                elif xdata[0][2] == "UP":
                    if xdata[1][1][0] < stock1Min.lastKline().close and abs(xdata[1][1][0]-stock1Min.lastKline().close)<2:
                        return

        if tag!=90 and spec!=43 and stock1Min.lastKline().close-buyPrice1<0 and (lastM5.close > lastM5.boll or (prelastM5.j-prelastM5.k>0 and prelastM5.macd > pre2lastM5.macd)):
            if stock1Min.lastKline().close < xzs[1]+1 and stock1Min.lastKline().close>xzs[0]-1 and abs(xzs[0]-stock1Min.lastKline().close)<2:
                return
            if xdata[0][2] == "DOWN":
                if xdata[2][1][0] < stock1Min.lastKline().close and abs(xdata[2][1][0]-stock1Min.lastKline().close)<2:
                    return
            elif xdata[0][2] == "UP":
                if xdata[1][1][0] < stock1Min.lastKline().close and abs(xdata[1][1][0]-stock1Min.lastKline().close)<2:
                    return
            '''
        pricelogging.info("tbuy-%s-%s,sell-%s,diff=%s,time=%s,up5=%s" % (tag,buyPrice1,stock1Min.lastKline().open,(stock1Min.lastKline().open-buyPrice1),time.ctime(stock1Min.lastKline().time),up5))
        buyPrice1 = None
        spec = None
        buy1Time = None
        buy2Time = None
        xspec = None
        xkdj = None
        upToDown = None
        sellSpec = None
        buyTriggerTime = None
        m5data = None
        kk1pos = None
        kk5pos = None
        return


    def canb3(xt,kline,prekline):
        global  xbuy,xspec,buyTriggerTime,buttomDown,buttomDownKline,buyPrice3,downToUp,up5,buyTriggerTimeCopy,up5Copy

        fdata = stock1Min.findInFiveData()

        kkdata = stock1Min.checkMacdUp()
        kkdata5 = stock5Min.checkMacdUp()

        pricelogging.info("xkline=%s",kkdata)

        '''
        if xspec == 42:
            if buyTriggerTime!=None and lastM5.macd<0:
                if lastm1.mn["5"] > lastm1.mn["15"] and prelastm1.mn["5"] < prelastm1.mn["15"]:
                    tmpx = stock1Min.checkbymeancrossCount(buyTriggerTime[2].time);

                    if tmpx == 2:
                        vmin,vmax = stock1Min.checkbymeancrossRange(buyTriggerTime[2].time)
                        if vmin < buyTriggerTime[1]:
                            pricelogging.info("tbuy spec=%s,time=%s,131,trigger=%s" % (xspec,time.ctime(lastm1.time),buyTriggerTime))
                            xspec = None
                            buyTriggerTime = None
                        else:
                            xt = (44,buyTriggerTime[1],buyTriggerTime[2],kkdata[1])
                            xspec = None
                            buyTriggerTime = None
                            up5 = (vmin,vmax,vmax)
                            return xt
                    elif tmpx>2:
                        pricelogging.info("tbuy spec=%s,time=%s,132,trigger=%s" % (xspec,time.ctime(lastm1.time),buyTriggerTime))
                        xspec = None
                        buyTriggerTime = None
        '''
        if xspec == 51 and up5==None:
            if lastm1.macd<0:
                if prelastm1.mn["5"] < prelastm1.mn["15"] and prelastm1.mn["15"] < prelastm1.mn["30"] and prelastm1.mn["30"] < prelastm1.mn["60"]:
                    if lastm1.mn["5"]>lastm1.mn["15"]:
                        return (42,stock1Min.checkvm(kkdata[0].time)-3,kkdata[0])
            else:
                if prelastm1.mn["5"] < prelastm1.mn["15"] and prelastm1.mn["15"] < prelastm1.mn["30"] and prelastm1.mn["30"] < prelastm1.mn["60"]:
                    if lastm1.mn["5"]>lastm1.mn["15"]:
                        return (42,stock1Min.checkvm(kkdata[1].time)-3,kkdata[1])


        if xspec == None:
            if lastm1.macd<0:
                if prelastm1.mn["5"] < prelastm1.mn["15"] and prelastm1.mn["15"] < prelastm1.mn["30"] and prelastm1.mn["30"] < prelastm1.mn["60"]:
                    if lastm1.mn["5"]>lastm1.mn["15"]:
                        return (42,stock1Min.checkvm(kkdata[0].time)-3,kkdata[0])
            else:
                if prelastm1.mn["5"] < prelastm1.mn["15"] and prelastm1.mn["15"] < prelastm1.mn["30"] and prelastm1.mn["30"] < prelastm1.mn["60"]:
                    if lastm1.mn["5"]>lastm1.mn["15"]:
                        return (42,stock1Min.checkvm(kkdata[1].time)-3,kkdata[1])
            if buyTriggerTimeCopy!=None:
                if lastm1.mn["5"] > lastm1.mn["15"] and lastm1.macd>0:
                    if lastm1.mn["5"] > lastm1.mn["60"] and (lastM5.macd>0 or (lastM5.mn["5"]>lastM5.mn["15"] and lastM5.mn["15"] > lastM5.mn["60"])):
                        if up5!=None:
                            if lastm1.close > up5[0]:
                                up5 = up5Copy
                                xt =  (46,buyTriggerTimeCopy[1],buyTriggerTimeCopy[2])

                                buyTriggerTimeCopy = None
                                up5Copy = None

                                return xt
                            else:
                                buyTriggerTimeCopy = None
                                up5Copy = None
                        else:
                            if lastm1.close > buyTriggerTimeCopy[1]:
                                up5 = up5Copy
                                xt =  (46,buyTriggerTimeCopy[1],buyTriggerTimeCopy[2])

                                buyTriggerTimeCopy = None
                                up5Copy = None

                                return xt
                            else:
                                buyTriggerTimeCopy = None
                                up5Copy = None
                    else:
                        buyTriggerTimeCopy = None
                        up5Copy = None
        elif xspec == 42:
                if lastm1.macd < 0 and lastm1.macd>prelastm1.macd:
                    distance = stock1Min.checkdistance(buyTriggerTime[2].time)
                    #pricelogging.info("tbuy short spec=%s,time=%s,distance=%s,trigger=%s,pre1=%s,pre2=%s,last=%s" % (xspec,time.ctime(lastm1.time),distance,buyTriggerTime,prelastm1,prelastm2,lastm1))
                    if distance == 1:
                        if valueMin(lastm1) > buyTriggerTime[1] and (lastm1.mn["5"]>lastm1.mn["15"]):
                            xt = (44,buyTriggerTime[1],buyTriggerTime[2],kkdata[1])
                            xspec = None
                            buyTriggerTime = None
                            return xt
                        if valueMin(lastm1) < buyTriggerTime[1]:
                            pricelogging.info("tbuy spec=%s,time=%s,119,trigger=%s" % (xspec,time.ctime(lastm1.time),buyTriggerTime))
                            xspec = None
                            buyTriggerTime = None
                    elif distance > 1:
                        pricelogging.info("tbuy spec=%s,time=%s,121,trigger=%s" % (xspec,time.ctime(lastm1.time),buyTriggerTime))
                        xspec = None
                        buyTriggerTime = None

                if lastm1.macd>0:
                    distance = stock1Min.checkdistance(buyTriggerTime[2].time)
                    #pricelogging.info("tbuy spec=%s,time=%s,distance=%s,trigger=%s,pre1=%s,pre2=%s,last=%s" % (xspec,time.ctime(lastm1.time),distance,buyTriggerTime,prelastm1,prelastm2,lastm1))
                    if distance == 1:
                        if lastm1.mn["5"]>prelastm1.mn["5"]:
                            xt = (43,buyTriggerTime[1],buyTriggerTime[2],kkdata[0])
                            xspec = None
                            buyTriggerTime = None
                            return xt
                    elif distance>1:
                        pricelogging.info("tbuy spec=%s,time=%s,122,trigger=%s" % (xspec,time.ctime(lastm1.time),buyTriggerTime))
                        xspec = None
                        buyTriggerTime = None

        elif xspec == 51:
            if buyTriggerTime!=None:
                if lastm1.macd < 0 and lastm1.macd>prelastm1.macd and up5==None:
                    distance = stock1Min.checkdistance(buyTriggerTime[2].time)
                    if distance == 1:
                        if valueMin(lastm1) > buyTriggerTime[1] and lastm1.mn["5"] > lastm1.mn["15"]:
                            xt = (44,buyTriggerTime[1],buyTriggerTime[2],kkdata[1])
                            xspec = None
                            buyTriggerTime = None

                            if lastm1.mn["30"] > lastm1.mn["60"] and lastm1.mn["15"] > lastm1.mn["30"]:
                                tmpmin = stock1Min.checkbymeancrossMin(2)
                                tmpmax = stock1Min.checkbymeancrossMax(tmpmin[1])
                                if tmpmin!=None and tmpmin[0]!=None:
                                    up5 = (stock1Min.checkvm(tmpmin[0].time)-2,tmpmax[0].high,tmpmax)
                            return xt
                        if valueMin(lastm1) < buyTriggerTime[1]:
                            pricelogging.info("tbuy spec=%s,time=%s,119,trigger=%s" % (xspec,time.ctime(lastm1.time),buyTriggerTime))
                            xspec = None
                            buyTriggerTime = None
                    elif distance > 1:
                        pricelogging.info("tbuy spec=%s,time=%s,124,trigger=%s" % (xspec,time.ctime(lastm1.time),buyTriggerTime))
                        xspec = None
                        buyTriggerTime = None

                elif lastm1.macd > 0 and lastm1.macd>prelastm1.macd and up5==None:
                    distance = stock1Min.checkdistance(buyTriggerTime[2].time)
                    if distance == 2:
                        if valueMin(lastm1) > buyTriggerTime[1] and lastm1.mn["5"] > lastm1.mn["15"]:
                            xt = (44,buyTriggerTime[1],buyTriggerTime[2],kkdata[1])
                            xspec = None
                            buyTriggerTime = None

                            if lastm1.mn["30"] > lastm1.mn["60"] and lastm1.mn["15"] > lastm1.mn["30"]:
                                tmpmin = stock1Min.checkbymeancrossMin(2)
                                tmpmax = stock1Min.checkbymeancrossMax(tmpmin[1])
                                if tmpmin!=None and tmpmin[0]!=None:
                                    up5 = (stock1Min.checkvm(tmpmin[0].time)-2,tmpmax[0].high,tmpmax)
                            return xt
                        if valueMin(lastm1) < buyTriggerTime[1]:
                            pricelogging.info("tbuy spec=%s,time=%s,119,trigger=%s" % (xspec,time.ctime(lastm1.time),buyTriggerTime))
                            xspec = None
                            buyTriggerTime = None
                    elif distance > 2:
                        pricelogging.info("tbuy spec=%s,time=%s,124,trigger=%s" % (xspec,time.ctime(lastm1.time),buyTriggerTime))
                        xspec = None
                        buyTriggerTime = None

                elif up5!=None:
                    if lastm1.mn["5"] > lastm1.mn["15"] and prelastm1.mn["5"] < prelastm1.mn["15"]:
                        tmpmin = stock1Min.checkbymeancrossMin(2)
                        if lastm1.close > up5[0]:
                            tmpmax = stock1Min.checkbymeancrossMax(tmpmin[1])
                            up5 = (stock1Min.checkvm(tmpmin[0].time)-2,tmpmax[0].high,tmpmax)
                            return (45,buyTriggerTime[1],buyTriggerTime[2],kkdata[1])

                    '''
                    if lastm1.close > up5[2] or (lastm1.close > up5[2]-1 and lastm1.close >=up5[1]+2):
                        if prelastm1.mn["30"] > prelastm1.mn["60"] and prelastm1.mn["5"]>prelastm1.mn["30"] and lastm1.mn["5"]<lastm1.mn["30"]:
                            return (53,buyTriggerTime[1],buyTriggerTime[2],kkdata[1])
                    '''
                    if lastm1.close<up5[0] and lastm1.mn["5"] < lastm1.mn["60"]:
                        return (52,buyTriggerTime[1],buyTriggerTime[2],kkdata[1])

    def canbuy4():
        global xspec,buyTriggerTime
        kkdata = stock1Min.checkMacdUp()

        if buyTriggerTime==None:
            return
        if lastm1.macd>0:
            distance = stock1Min.checkdistance(buyTriggerTime[2].time)
            if distance == 2:
                return (min(valueMin(kkdata[1]),kkdata[1].dn)-2, min(valueMax(kkdata[2]),kkdata[1].up), min(valueMax(kkdata[2]),kkdata[1].up) + kkdata[1].up-kkdata[1].boll)

        if lastm1.mn["5"] > lastm1.mn["15"] and prelastm1.mn["5"] < prelastm1.mn["15"]:
            tmpx = stock1Min.checkbymeancrossCount(buyTriggerTime[2].time);
            if tmpx == 2:
                vmin,vmax = stock1Min.checkbymeancrossRange(buyTriggerTime[2].time)
                return (vmin,vmax,vmax)

    def cansell3(xt,kline,prekline):
        global sellSpec,spec,up15,up5,buyTriggerTime,buyPrice1

        kkdata = stock1Min.checkMacdUp()
        if lastm1.close<sellSpec:
            return 110

        if prelastm1.mn["5"]>prelastm1.mn["15"] and prelastm1.mn["15"] > prelastm1.mn["30"] and prelastm1.mn["15"] > prelastm1.mn["60"]:
            if lastm1.mn["5"]<lastm1.mn["15"]:

                temp1 = stock1Min.checkdistance3bymacd(buyTriggerTime[2].time)
                temp2 = stock1Min.checkdistance4bymean(buyTriggerTime[2].time,2)

                pricelogging.info("xbuy 51 time=%s,tmp1=%s,temp2=%s" % (time.ctime(lastm1.time),temp1,temp2))

                if temp1!=None and temp2!=None:
                    if max(lastm1.time-temp1.time,lastm1.time-temp2.time) > 15*60 :
                        return 51

        if prelastm1.mn["5"]>prelastm1.mn["15"] and lastm1.mn["5"]<lastm1.mn["15"] and up5==None and buyTriggerTime!=None and lastm1.macd<0:
            tmpx = stock1Min.checkbymeancrossCount(buyTriggerTime[2].time);
            if tmpx==1:
                return 51


        if up5!=None:
            if lastm1.close<up5[0] and lastm1.mn["5"] < lastm1.mn["60"]:
                return 52

            if prelastm1.mn["30"] > prelastm1.mn["60"] and prelastm1.mn["5"]>prelastm1.mn["30"] and prelastm1.mn["15"] > prelastm1.mn["30"] and lastm1.mn["5"]<lastm1.mn["30"]:
                return 51

            '''
            if lastm1.close > up5[2] or (lastm1.close > up5[2]-1 and lastm1.close >=up5[1]+2):
                if prelastm1.mn["30"] > prelastm1.mn["60"] and prelastm1.mn["5"]>prelastm1.mn["30"] and lastm1.mn["5"]<lastm1.mn["30"]:
                    return 53
            '''
    pricelogging.info("m5macdbig=%s",m5macdbignext)
    pricelogging.info("xkline=%s",lastm1)

    if buyPrice1==None:
        ret = canb3(None,lastm1,prelastm1)
        if ret!=None:
            if ret[0] == 42 :
                buyTriggerTime = ret
                xspec = 42
                buyTriggerTimeCopy = None
                up5Copy = None

                pricelogging.info("tbuy spec=%s,time=%s,trigger=%s" % (xspec,time.ctime(lastm1.time),buyTriggerTime))

                ret = canb3(None,lastm1,prelastm1)
                if ret==None:
                    return

            if ret[0] == 43 or ret[0] == 44:
                buy1Time = current.time
                buy2Time = lastM5.time
                buy(ret)
                buyTriggerTime = ret
                xspec = None
                spec = ret[0]
                sellSpec = ret[1]
                up5= None
                up15 = None

                buyTriggerTimeCopy = None
                up5Copy = None

            if ret[0] == 45:
                buy1Time = current.time
                buy2Time = lastM5.time
                buy(ret)
                buyTriggerTime = ret
                xspec = None
                spec = ret[0]
                sellSpec = ret[1]

                buyTriggerTimeCopy = None
                up5Copy = None
            if ret[0] == 52:
                buyTriggerTimeCopy = buyTriggerTime
                up5Copy = up5

                xspec = None
                sellSpec = None
                spec = None
                up15 = None
                up5 = None
                buyTriggerTime = None
                buyPrice3 = None

            if ret[0] == 46:
                buy1Time = current.time
                buy2Time = lastM5.time
                buy(ret)
                buyTriggerTime = ret
                xspec = None
                spec = ret[0]
                sellSpec = ret[1]

        if up5==None:
            ret = canbuy4()
            if ret!=None:
                up5 = ret
                pricelogging.info("tbuy,sellspec=%s,up5=%s",sellSpec,up5)
        return


    if buyPrice1!=None:
        if up5==None:
            ret = canbuy4()
            if ret!=None:
                up5 = ret
                pricelogging.info("tbuy,sellspec=%s,up5=%s",sellSpec,up5)

        pricelogging.info("sellspec=%s,up5=%s",sellSpec,up5)
        xret = cansell3(None,lastm1,prelastm1)
        if xret != None:
            if xret == 51:
                tmp_buyTriggerTime = buyTriggerTime
                tmp_sellSpec = sellSpec
                sell(xret)
                buyTriggerTime = tmp_buyTriggerTime
                sellSpec = tmp_sellSpec
                xspec = 51

                buyTriggerTimeCopy = None
                up5Copy = None
            else:
                buyTriggerTimeCopy = buyTriggerTime
                up5Copy = up5


                sell(xret)
                xspec = None
                sellSpec = None
                spec = None
                up15 = None
                up5 = None
                buyTriggerTime = None
                buyPrice3 = None


                return


def go20():
    global buyPrice1,buyPrice2,bidsList,lastbuyTime,asksList,buy1Time,buy2Time,buyTriggerTime,buyPrice3,downToUp,upToDown,middleToUp,spec,xspec,sellSpec,xbuy,xkdj,up15,up5,kk1pos,kk5pos,kk15pos,m5data
    global fenx1,fenx5,lastfenx1,lastfenx5,buttomDown,buttomDownKline,up5Copy,buyTriggerTimeCopy
    m5kdjzero,m5kdjbignext = stock5Min.forecastKDJClose()
    m5macdZero,m5macdbignext = stock5Min.forecastMacd()

    lastM5 = stock5Min.lastKline()
    prelastM5 = stock5Min.preLastKline()
    pre2lastM5 = stock5Min.pre2LastKline()
    current = stock1Min.lastKline()
    lastm1 = stock1Min.preLastKline()
    prelastm1 = stock1Min.pre2LastKline()
    prelastm2 = stock1Min.preMyLastKline(3)
    lastM15 = stock15Min.lastKline()

    lastM15 = stock15Min.lastKline()
    prelastM15 = stock15Min.preLastKline()
    pre2lastM15 = stock15Min.pre2LastKline()

    if current.time-lastM5.time>=5*60:
        return

    if current.time == buy1Time:
        return


    def valueMax(kline):
        if kline.close>kline.open:
            return kline.close
        return kline.open

    def valueMin(kline):
        if kline.close<kline.open:
            return kline.close
        return kline.open


    def buy(tag):
        global buyPrice1,lastbuyTime,buyPrice2,bidsList,asksList,buy1Time,buy2Time,buyTriggerTime,buyPrice3,downToUp,upToDown,middleToUp,spec,xspec,sellSpec,xbuy,xkdj,up15,up5,kk1pos,kk5pos,kk15pos,m5data

        if buyPrice1==None:
            buy1Time = current.time
            buy2Time = lastM5.time
            buyPrice1 = current.close
            m5data = None
            buyTriggerTime = None
            pricelogging.info("tbuy-%s,-%s,time=%s,deciderTime=%s,spec=%s" % (tag,buyPrice1,time.ctime(stock1Min.lastKline().time),time.ctime(buy1Time),spec))
            return
        else:
            pricelogging.info("tbuy-%s-buy-disable,time=%s" % (tag,time.ctime(stock1Min.lastKline().time)) )


    def sell(tag):
        global buyPrice1,lastbuyTime,buyPrice2,bidsList,asksList,buy1Time,buy2Time,buyTriggerTime,buyPrice3,downToUp,upToDown,middleToUp,spec,xspec,sellSpec,xbuy,xkdj,up15,up5,kk1pos,kk5pos,kk15pos,m5data
        if buyPrice1==None:
            pricelogging.info("tbuy-%s-sell-disable,time=%s" % (tag,time.ctime(stock1Min.lastKline().time)) )
            return
        '''
        xzs = zs(xdata)
        xspec = True
        if tag!=90 and spec==43 and stock1Min.lastKline().close-buyPrice1<0:
            if lastm1.macd>0:
                if xdata[0][2] == "DOWN":
                    if xdata[2][1][0] < stock1Min.lastKline().close and abs(xdata[2][1][0]-stock1Min.lastKline().close)<2:
                        return
                elif xdata[0][2] == "UP":
                    if xdata[1][1][0] < stock1Min.lastKline().close and abs(xdata[1][1][0]-stock1Min.lastKline().close)<2:
                        return

        if tag!=90 and spec!=43 and stock1Min.lastKline().close-buyPrice1<0 and (lastM5.close > lastM5.boll or (prelastM5.j-prelastM5.k>0 and prelastM5.macd > pre2lastM5.macd)):
            if stock1Min.lastKline().close < xzs[1]+1 and stock1Min.lastKline().close>xzs[0]-1 and abs(xzs[0]-stock1Min.lastKline().close)<2:
                return
            if xdata[0][2] == "DOWN":
                if xdata[2][1][0] < stock1Min.lastKline().close and abs(xdata[2][1][0]-stock1Min.lastKline().close)<2:
                    return
            elif xdata[0][2] == "UP":
                if xdata[1][1][0] < stock1Min.lastKline().close and abs(xdata[1][1][0]-stock1Min.lastKline().close)<2:
                    return
            '''
        pricelogging.info("tbuy-%s-%s,sell-%s,diff=%s,time=%s,up5=%s" % (tag,buyPrice1,stock1Min.lastKline().open,(stock1Min.lastKline().open-buyPrice1),time.ctime(stock1Min.lastKline().time),up5))
        buyPrice1 = None
        spec = None
        buy1Time = None
        buy2Time = None
        xspec = None
        xkdj = None
        upToDown = None
        sellSpec = None
        m5data = None
        kk1pos = None
        kk5pos = None
        return


    def canb5():
        if lastm1.close > lastm1.mn["5"] and lastm1.macd>prelastm1.macd:
            return "BUY" #buy

        if lastm1.mn["5"]<lastm1.mn["15"]:
            return "DIS" #dis

    def cansell5():
        if lastm1.close < lastm1.mn["5"] and lastm1.macd<prelastm1.macd:
            return "SELL" #sell

        if lastm1.mn["5"] > lastm1.mn["15"]:
            return "DIS" #dis


    def canb3(xt,kline,prekline):
        global  xbuy,xspec,buyTriggerTime,buttomDown,buttomDownKline,buyPrice3,downToUp,up5,buyTriggerTimeCopy,up5Copy

        kkdata = stock1Min.checkMacdUp()

        pricelogging.info("xkline=%s,current=%s",kkdata,current)


        if prelastM5.macd>=0:
            if lastm1.mn["5"] < lastm1.mn["15"] and lastm1.mn["15"]-lastm1.mn["5"] < 1.5 and lastm1.macd>prelastm1.macd:
                tempmin = stock1Min.checkbymeancrossMin(1)
                return (74,tempmin[0].low,tempmin[0],lastm1.up)
            if lastm1.mn["5"] > lastm1.mn["15"] and prelastm1.mn["5"] < prelastm1.mn["5"] and lastm1.macd>prelastm1.macd:
                tempmin = stock1Min.checkbymeancrossMin(2)
                return (74,tempmin[0].low,tempmin[0],lastm1.up)
        else:
            if lastm1.mn["5"] > lastm1.mn["15"] and prelastm1.mn["5"] < prelastm1.mn["5"] and lastm1.macd>prelastm1.macd:
                tempmin = stock1Min.checkbymeancrossMin(2)
                return (73,tempmin[0].low,tempmin[0],lastm1.up)


    def cansell3(xt,kline,prekline):
        global sellSpec,spec,up15,up5,buyTriggerTime,buyPrice1

        kkdata = stock1Min.checkMacdUp()

        if lastm1.close<buyTriggerTime[1]:
            return 110

        if prelastm1.mn["5"]>prelastm1.mn["15"] and lastm1.mn["5"]<lastm1.mn["15"]:
            return 51


    pricelogging.info("m5macdbig=%s",m5macdbignext)
    pricelogging.info("xkline=%s",lastm1)

    if buyPrice1==None:
        if xspec==73:
            ret = canb5()
            if ret == "BUY":
                if buyTriggerTime!=None and buyTriggerTimeCopy!=None and buyTriggerTimeCopy[1] > buyTriggerTime[1]:
                    buy1Time = current.time
                    buy2Time = lastM5.time
                    buy(xspec)
                    xspec = None
                    buyTriggerTime = buyTriggerTimeCopy
                else:
                    xspec = None
                    pricelogging.info("tbuy dis spec=73,time=%s,buytrigger=%s" % lastm1,buyTriggerTime)
            else:
                xspec = None
                pricelogging.info("tbuy dis spec=73,time=%s,buytrigger=%s" % lastm1,buyTriggerTime)
            return

        ret = canb3(None,lastm1,prelastm1)
        if ret!=None:
            if ret[0] == 73:
                if buyTriggerTime==None:
                    buyTriggerTime = ret
                    return

                pricelogging.info("tbuy spec=73,time=%s,buytrigger=%s" % lastm1,buyTriggerTime)

                xspec = 73
                buyTriggerTimeCopy = ret
            if ret[0] == 74:
                buy1Time = current.time
                buy2Time = lastM5.time
                buy(ret)
                buyTriggerTime = ret
        return


    if buyPrice1!=None:
        if prelastM5.macd < 0 and lastm1.mn["5"]<lastm1.mn["15"]:
            sell(120)

        if xspec == 51:
            ret = cansell5()
            if ret == "SELL":
                if stock1Min.checkmax2(buyTriggerTime[2].time,buyTriggerTime[3]) == True \
                        or lastm1.time - buyTriggerTime[2].time > 15*60:
                    sell(xspec)
                    xspec = None
                    sellSpec = None
                    spec = None
                    return
                else:
                    xspec=None
            if ret == "DIS":
                xspec=None
            return

        xret = cansell3(None,lastm1,prelastm1)
        if xret != None:
            if xret == 51:
                xspec = 51
            else:
                sell(xret)
                xspec = None
                sellSpec = None
                spec = None
                return



def on_message(self,evt):
    global last_time
    global buyPrice
    global tradeIndex
    global tradeLastTime
    global bidsList,asksList
    data = inflate(evt) #data decompress
    mjson = json.loads(data)

    if type(mjson) == dict and mjson.has_key("event") and mjson["event"]=="pong":
        last_time = time.time()
        return
    if type(mjson) == list:
        for tdata in mjson:
            if tdata.has_key("channel") and tdata["channel"] == "ok_sub_spotcny_btc_kline_1min" and tdata.has_key("data"):
                kdata = tdata["data"]
                if type(kdata[0]) == int :
                    stock1Min.on_kline(KLine(kdata))
                else:
                    for k in kdata:
                        stock1Min.on_kline(KLine(k))
                kdj,touchBoll = stock1Min.canBuy()
                pricelogging.info("kdj=%s,touch=%s,fiveIsStrong=%s" % (kdj,touchBoll,stock5Min.isUp()))

                if buyPrice!=None and kdj==False:
                    pricelogging.info("buy-%s,sell-%s,diff=%s" % (buyPrice,stock1Min.lastKline().close,(stock1Min.lastKline().close-buyPrice)))
                    buyPrice = None
                if buyPrice==None and kdj==True and touchBoll==True:
                    buyPrice=stock1Min.lastKline().close
                    pricelogging.info("buy-%s,time=%s,boll" % (stock1Min.lastKline().close,stock1Min.lastKline().time))
                if buyPrice==None and kdj==True and touchBoll==False and stock5Min.isUp()==True:
                    buyPrice=stock1Min.lastKline().close
                    pricelogging.info("buy-%s,time=%s" % (stock1Min.lastKline().close,stock1Min.lastKline().time))
                go()
            if tdata.has_key("channel") and tdata["channel"] == "ok_sub_spotcny_btc_kline_5min" and tdata.has_key("data"):
                kdata = tdata["data"]
                if type(kdata[0]) == int :
                    stock5Min.on_kline(KLine(kdata))
                else:
                    for k in kdata:
                        stock5Min.on_kline(KLine(k))
                go()
            if tdata.has_key("channel") and tdata["channel"] == "ok_sub_spotcny_btc_kline_15min" and tdata.has_key("data"):
                kdata = tdata["data"]
                if type(kdata[0]) == int :
                    stock15Min.on_kline(KLine(kdata))
                else:
                    for k in kdata:
                        stock15Min.on_kline(KLine(k))
                go()

            if tdata.has_key("channel") and tdata["channel"] == "ok_sub_spotcny_btc_trades" and tdata.has_key("data"):
                kdata = tdata["data"]
                for k in kdata:
                    td = Trade(k)
                    stock15Sec.tkine(td)
                    '''
                    if tradeIndex.has_key(str(td.time)) == False:
                        tradeIndex[str(td.time)] = td.vol
                        if tradeLastTime == None:
                            tradeLastTime = str(td.time)
                        else:
                            logging.info("Trade=" + str(tradeIndex[tradeLastTime]))
                            tradeLastTime = str(td.time)
                    else:
                        tradeIndex[str(td.time)] = td.vol +  tradeIndex[str(td.time)]
                    '''

            if tdata.has_key("channel") and tdata["channel"] == "ok_sub_spotcny_btc_depth_60" and tdata.has_key("data"):
                bidsList.insert(0,tdata["data"]["bids"])
                asksList.insert(0,tdata["data"]["asks"])

                if len(bidsList)>=6:
                    bidsList.pop()
                if len(asksList)>=6:
                    asksList.pop()


def findTotalSupportWithBids(price,data):
    ret = 0;
    for d,v in data:
        if d>=price:
            ret = ret + v
    return ret;

def findTotalSupportWithAsks(price,data):
    ret = 0
    for d,v in data:
        if d<=price:
            ret = ret +v
    return ret

def findMaxSupport(data):
    for d,v in data:
        if v>20 :
            return d,v

    ret = None
    for d,v in data:
        if ret==None:
            ret = (d,v)
        elif ret[1]<v:
            ret = (d,v)
    return ret

def canBuyWithBids(cur,old):
    curd,curv = findMaxSupport(cur)
    oldd,oldv = findMaxSupport(old)

    pricelogging.info("curd=%s,curv=%s,old=%s,oldv=%s" % (curd,curv,oldd,oldv))

    if curd > oldd:
        return True
    elif curd == oldd and curv+20 < oldv:
        return False
    elif curd == oldd and curv>= oldv + 20:
        return True
    elif curd<oldd:
        return False
    else:
        return None

def canBuyWithAsks(cur,old):
    curd,curv = findMaxSupport(cur)
    oldd,oldv = findMaxSupport(old)

    pricelogging.info("asks ,curd=%s,curv=%s,old=%s,oldv=%s" % (curd,curv,oldd,oldv))
    if curd > oldd:
        return True
    elif curd == oldd and curv+20 < oldv:
        return True
    elif curd == oldd and curv>=oldv+20:
        return False
    elif curd<oldd:
        return False
    else:
        return None


def inflate(data):
    decompress = zlib.decompressobj(
        -zlib.MAX_WBITS  # see above
    )
    inflated = decompress.decompress(data)
    inflated += decompress.flush()
    return inflated

def on_error(self,evt):
    print (evt)

def on_close(self,evt):
    print ('DISCONNECT')

def on_pong(self,evt):
    self.send("{'event':'ping'}")

def connect():
    global ws;
    url = "wss://real.okcoin.cn:10440/websocket/okcoinapi"
    websocket.enableTrace(True)
    if len(sys.argv) < 2:
        host = url
    else:
        host = sys.argv[1]
    ws = websocket.WebSocketApp(host,
                                on_message = on_message,
                                on_error = on_error,
                                on_close = on_close)
    ws.on_open = on_open
    ws.on_pong = on_pong

    ws.run_forever(ping_interval=3)

def check_connect():
    event = threading.Event()
    while not event.wait(6):
        #print(time.time() - last_time)
        if last_time == 0:
            continue;
        if time.time()-last_time>6:
            ws.close()

'''
if __name__ == "__main__":
    thread = threading.Thread(target=check_connect)
    thread.setDaemon(True)
    thread.start()

    while True:
        try:
            connect();
            stock1Min = stock("btc_cny",stock.OneMin,500)
            stock5Min = stock("btc_cny",stock.FiveMin,500)
            stock15Sec = stock("btc_cny",stock.FifteenSec,500)
            stock15Min = stock("btc_cny",stock.FifteenMin,500)
            print("reconnect")
        except Exception,e:
            logging.error(e)

'''
