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


    if buyPrice1 == None:

        if

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
