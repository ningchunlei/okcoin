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



def pl(level1Stock,level2Stock,l1tag,l2tag,difftime):

    l1_last = level1Stock.lastKline()
    l1_pre = level1Stock.preLastKline()
    l1_pre_pre = level1Stock.pre2LastKline()

    l2_last = level2Stock.lastKline()
    l2_pre = level2Stock.preLastKline()
    l2_pre_pre = level2Stock.pre2LastKline()

    if l1_last.time-l2_last.time>=difftime*60:
        return

    l1_last_kdj = l1_last.j-l1_last.k
    l1_pre_kdj = l1_pre.j-l1_pre.k
    l1_pre_pre_kdj = l1_pre_pre.j-l1_pre_pre.k


    l2_last_kdj = l2_last.j-l2_last.k
    l2_pre_kdj = l2_pre.j-l2_pre.k
    l2_pre_pre_kdj = l2_pre_pre.j-l2_pre_pre.k


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


