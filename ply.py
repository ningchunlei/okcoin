import time
from datetime import datetime
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S'
                    )
pricelogging = logging.getLogger("price")
tradelogging = logging.getLogger("trade")


def canbuybymacd(k1,k2):
    if k1.macd < -0.6 and k1.macd < k2.macd:
        return 4
    if k1.macd < 0 and k2.macd > 0:
        return 0
    if k1.macd >0 and k2.macd>0 and k1.macd < k2.macd and k1.macd < 0.2:
        return 0
    if k1.macd >0.6 and k1.macd > k2.macd:
        return 2
    if k1.macd>0 and k2.macd<0:
        return 1
    if k1.macd <0 and k2.macd<0 and k1.macd>k2.macd and k1.macd>-0.1:
        return 1

    return 3

def canbuybykdj(k1,k2):
    if k1.j-k1.k>0 and k2.j-k2.k<0:
        return 1

    if k1.j-k1.k<0 and k2.j-k2.k>0:
        return 0

    if k1.j < 20 and k1.j > k2.j:
        return 2

    if k1.j > 80 and k1.j < k2.j:
        return 4

    return 3


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


    pricelogging.info("level=%s,time=%s,j=%s,k=%s,macd=%s,up=%s,dn=%s,boll=%s,open=%s,close=%s" % (l1tag,time.ctime(l1_pre.time),l1_pre.j,l1_pre.k,l1_pre.macd,l1_pre.up,l1_pre.dn,l1_pre.boll,l1_pre.open,l1_pre.close))
    pricelogging.info("level=%s,time=%s,j=%s,k=%s,macd=%s,up=%s,dn=%s,boll=%s,open=%s,close=%s" % (l2tag,time.ctime(l2_pre.time),l2_pre.j,l2_pre.k,l2_pre.macd,l2_pre.up,l2_pre.dn,l2_pre.boll,l2_pre.open,l2_pre.close))


    pricelogging.info("clevel=%s,time=%s,j=%s,k=%s,macd=%s,up=%s,dn=%s,boll=%s,open=%s,close=%s" % (l1tag,time.ctime(l1_last.time),l1_last.j,l1_last.k,l1_last.macd,l1_last.up,l1_last.dn,l1_last.boll,l1_last.open,l1_last.close))
    pricelogging.info("clevel=%s,time=%s,j=%s,k=%s,macd=%s,up=%s,dn=%s,boll=%s,open=%s,close=%s" % (l2tag,time.ctime(l2_last.time),l2_last.j,l2_last.k,l2_last.macd,l2_last.up,l2_last.dn,l2_last.boll,l2_last.open,l2_last.close))

    if l1tag == "1":
        f1po = level1Stock.mkposition()
        l1_pre.po = f1po
    else:
        f1po = level1Stock.mkposition(count=0)
        l1_last.po = f1po
    f5po = level2Stock.mkposition(count=0)
    l2_last.po = f5po



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

    pricelogging.info("k1iscross=%s,k5icross=%s,isupordownline1=%s,isupordownline5=%s" % (level1Stock.iscrossKline(),level2Stock.iscrossKline(),level1Stock.isUpOrDownKline(),level1Stock.isUpOrDownKline()) )


    def canbuybypo():

        if kk1Down:
            if kk5Down and not kk5Boll:
                return "buy-down-1-down-1"
            elif kk5DownToBoll and f5po[1][1]==0:
                return "sell-down-1-downtoboll-0"
            elif kk5DownToBoll and f5po[1][1]==1:
                return "buy-down-1-downtoboll-1"
            elif kk5DownToBoll and f5po[1][1]==3:
                return "sell-down-1-downtoboll-3"
            elif kk5Boll and f5po[2][1]==0:
                return "buy-down-1-boll-0"
            elif kk5Boll and f5po[2][1]==1:
                return "buy-down-1-boll-1"
            elif kk5Boll and f5po[2][1]==3:
                return "sell-down-1-boll-3"
            elif kk5UpToBoll and f5po[3][1]==0:
                return "sell-down-1-uptoboll-0"
            elif kk5UpToBoll and f5po[3][1]==1:
                return "buy-down-1-uptoboll-1"
            elif kk5UpToBoll and f5po[3][1]==3:
                return "sell-down-1-uptoboll-3"
            elif kk5Up and not kk5Boll:
                return "sell-down-1-up-0"
        elif kk1DownToBoll and f1po[1][1] == 0 :
            if kk5Down and not kk5Boll:
                return "sell-downtoboll-0-down-1"
            elif kk5DownToBoll and f5po[1][1]==0:
                return "sell-downtoboll-0-downtoboll-0"
            elif kk5DownToBoll and f5po[1][1]==1:
                return "sell-downtoboll-0-downtoboll-1"
            elif kk5DownToBoll and f5po[1][1]==3:
                return "sell-downtoboll-0-downtoboll-3"
            elif kk5Boll and f5po[2][1]==0:
                return "sell-downtoboll-0-boll-0"
            elif kk5Boll and f5po[2][1]==1:
                return "sell-downtoboll-0-boll-1"
            elif kk5Boll and f5po[2][1]==3:
                return "sell-downtoboll-0-boll-3"
            elif kk5UpToBoll and f5po[3][1]==0:
                return "sell-downtoboll-0-uptoboll-0"
            elif kk5UpToBoll and f5po[3][1]==1:
                return "sell-downtoboll-0-uptoboll-1"
            elif kk5UpToBoll and f5po[3][1]==3:
                return "sell-downtoboll-0-uptoboll-3"
            elif kk5Up and not kk5Boll:
                return "sell-downtoboll-0-up-0"
        elif kk1DownToBoll and f1po[1][1] == 1 :
            if kk5Down and not kk5Boll:
                return "buy-downtoboll-1-down-1"
            elif kk5DownToBoll and f5po[1][1]==0:
                return "sell-downtoboll-1-downtoboll-0"
            elif kk5DownToBoll and f5po[1][1]==1:
                return "buy-downtoboll-1-downtoboll-1"
            elif kk5DownToBoll and f5po[1][1]==3:
                return "buy-downtoboll-1-downtoboll-3"
            elif kk5Boll and f5po[2][1]==0:
                return "sell-downtoboll-1-boll-0"
            elif kk5Boll and f5po[2][1]==1:
                return "buy-downtoboll-1-boll-1"
            elif kk5Boll and f5po[2][1]==3:
                return "sell-downtoboll-1-boll-3"
            elif kk5UpToBoll and f5po[3][1]==0:
                return "sell-downtoboll-1-uptoboll-0"
            elif kk5UpToBoll and f5po[3][1]==1:
                return "buy-downtoboll-1-uptoboll-1"
            elif kk5UpToBoll and f5po[3][1]==3:
                return "sell-downtoboll-1-uptoboll-3"
            elif kk5Up and not kk5Boll:
                return "sell-downtoboll-1-up-0"
        elif kk1DownToBoll and f1po[1][1] == 3 :
            if kk5Down and not kk5Boll:
                return "sell-downtoboll-3-down-1"
            elif kk5DownToBoll and f5po[1][1]==0:
                return "sell-downtoboll-3-downtoboll-0"
            elif kk5DownToBoll and f5po[1][1]==1:
                return "buy-downtoboll-3-downtoboll-1"
            elif kk5DownToBoll and f5po[1][1]==3:
                return "sell-downtoboll-3-downtoboll-3"
            elif kk5Boll and f5po[2][1]==0:
                return "sell-downtoboll-3-boll-0"
            elif kk5Boll and f5po[2][1]==1:
                return "buy-downtoboll-3-boll-1"
            elif kk5Boll and f5po[2][1]==3:
                return "sell-downtoboll-3-boll-3"
            elif kk5UpToBoll and f5po[3][1]==0:
                return "sell-downtoboll-3-uptoboll-0"
            elif kk5UpToBoll and f5po[3][1]==1:
                return "buy-downtoboll-3-uptoboll-1"
            elif kk5UpToBoll and f5po[3][1]==3:
                return "sell-downtoboll-3-uptoboll-3"
            elif kk5Up and not kk5Boll:
                return "sell-downtoboll-3-up-0"
        elif kk1Boll and f1po[2][1] == 0 :

            if kk5Down and not kk5Boll:
                return "sell-boll-0-down-1"
            elif kk5DownToBoll and f5po[1][1]==0:
                return "sell-boll-0-downtoboll-0"
            elif kk5DownToBoll and f5po[1][1]==1:
                return "buy-boll-0-downtoboll-1"
            elif kk5DownToBoll and f5po[1][1]==3:
                return "sell-boll-0-downtoboll-3"
            elif kk5Boll and f5po[2][1]==0:
                return "sell-boll-0-boll-0"
            elif kk5Boll and f5po[2][1]==1:
                return "buy-boll-0-boll-1"
            elif kk5Boll and f5po[2][1]==3:
                return "sell-boll-3-boll-3"
            elif kk5UpToBoll and f5po[3][1]==0:
                return "sell-boll-0-uptoboll-0"
            elif kk5UpToBoll and f5po[3][1]==1:
                return "buy-boll-0-uptoboll-1"
            elif kk5UpToBoll and f5po[3][1]==3:
                return "sell-boll-0-uptoboll-3"
            elif kk5Up and not kk5Boll:
                return "sell-boll-0-up-0"

        elif kk1Boll and f1po[2][1] == 1 :

            if kk5Down and not kk5Boll:
                return "sell-boll-1-down-1"
            elif kk5DownToBoll and f5po[1][1]==0:
                return "sell-boll-1-downtoboll-0"
            elif kk5DownToBoll and f5po[1][1]==1:
                return "sell-boll-1-downtoboll-1"
            elif kk5DownToBoll and f5po[1][1]==3:
                return "sell-boll-1-downtoboll-3"
            elif kk5Boll and f5po[2][1]==0:
                return "sell-boll-1-boll-0"
            elif kk5Boll and f5po[2][1]==1:
                return "sell-boll-1-boll-1"
            elif kk5Boll and f5po[2][1]==3:
                return "sell-boll-1-boll-3"
            elif kk5UpToBoll and f5po[3][1]==0:
                return "sell-boll-1-uptoboll-0"
            elif kk5UpToBoll and f5po[3][1]==1:
                return "sell-boll-1-uptoboll-1"
            elif kk5UpToBoll and f5po[3][1]==3:
                return "sell-boll-1-uptoboll-3"
            elif kk5Up and not kk5Boll:
                return "sell-boll-1-up-0"

        elif kk1Boll and f1po[2][1] == 3 :

            if kk5Down and not kk5Boll:
                return "sell-boll-3-down-1"
            elif kk5DownToBoll and f5po[1][1]==0:
                return "sell-boll-3-downtoboll-0"
            elif kk5DownToBoll and f5po[1][1]==1:
                return "sell-boll-3-downtoboll-1"
            elif kk5DownToBoll and f5po[1][1]==3:
                return "sell-boll-3-downtoboll-3"
            elif kk5Boll and f5po[2][1]==0:
                return "sell-boll-3-boll-0"
            elif kk5Boll and f5po[2][1]==1:
                return "sell-boll-3-boll-1"
            elif kk5Boll and f5po[2][1]==3:
                return "sell-boll-3-boll-3"
            elif kk5UpToBoll and f5po[3][1]==0:
                return "sell-boll-3-uptoboll-0"
            elif kk5UpToBoll and f5po[3][1]==1:
                return "sell-boll-3-uptoboll-1"
            elif kk5UpToBoll and f5po[3][1]==3:
                return "sell-boll-3-uptoboll-3"
            elif kk5Up and not kk5Boll:
                return "sell-boll-3-up-0"

        elif kk1UpToBoll and f1po[3][1] == 0 :

            if kk5Down and not kk5Boll:
                return "sell-uptoboll-0-down-1"
            elif kk5DownToBoll and f5po[1][1]==0:
                return "sell-uptoboll-0-downtoboll-0"
            elif kk5DownToBoll and f5po[1][1]==1:
                return "buy-uptoboll-0-downtoboll-1"
            elif kk5DownToBoll and f5po[1][1]==3:
                return "sell-uptoboll-0-downtoboll-3"
            elif kk5Boll and f5po[2][1]==0:
                return "sell-uptoboll-0-boll-0"
            elif kk5Boll and f5po[2][1]==1:
                return "buy-uptoboll-0-boll-1"
            elif kk5Boll and f5po[2][1]==3:
                return "sell-uptoboll-0-boll-3"
            elif kk5UpToBoll and f5po[3][1]==0:
                return "sell-uptoboll-0-uptoboll-0"
            elif kk5UpToBoll and f5po[3][1]==1:
                return "buy-uptoboll-0-uptoboll-1"
            elif kk5UpToBoll and f5po[3][1]==3:
                return "sell-uptoboll-0-uptoboll-3"
            elif kk5Up and not kk5Boll:
                return "sell-uptoboll-0-up-0"

        elif kk1UpToBoll and f1po[3][1] == 1 :

            if kk5Down and not kk5Boll:
                return "sell-uptoboll-1-down-1"
            elif kk5DownToBoll and f5po[1][1]==0:
                return "sell-uptoboll-1-downtoboll-0"
            elif kk5DownToBoll and f5po[1][1]==1:
                return "sell-uptoboll-1-downtoboll-1"
            elif kk5DownToBoll and f5po[1][1]==3:
                return "sell-uptoboll-1-downtoboll-3"
            elif kk5Boll and f5po[2][1]==0:
                return "sell-uptoboll-1-boll-0"
            elif kk5Boll and f5po[2][1]==1:
                return "buy-uptoboll-1-boll-1"
            elif kk5Boll and f5po[2][1]==3:
                return "sell-uptoboll-1-boll-3"
            elif kk5UpToBoll and f5po[3][1]==0:
                return "sell-uptoboll-1-uptoboll-0"
            elif kk5UpToBoll and f5po[3][1]==1:
                return "sell-uptoboll-1-uptoboll-1"
            elif kk5UpToBoll and f5po[3][1]==3:
                return "sell-uptoboll-1-uptoboll-3"
            elif kk5Up and not kk5Boll:
                return "sell-uptoboll-1-up-0"

        elif kk1UpToBoll and f1po[3][1] == 3 :

            if kk5Down and not kk5Boll:
                return "sell-uptoboll-3-down-1"
            elif kk5DownToBoll and f5po[1][1]==0:
                return "sell-uptoboll-3-downtoboll-0"
            elif kk5DownToBoll and f5po[1][1]==1:
                return "sell-uptoboll-3-downtoboll-1"
            elif kk5DownToBoll and f5po[1][1]==3:
                return "sell-uptoboll-3-downtoboll-3"
            elif kk5Boll and f5po[2][1]==0:
                return "sell-uptoboll-3-boll-0"
            elif kk5Boll and f5po[2][1]==1:
                return "sell-uptoboll-3-boll-1"
            elif kk5Boll and f5po[2][1]==3:
                return "sell-uptoboll-3-boll-3"
            elif kk5UpToBoll and f5po[3][1]==0:
                return "sell-uptoboll-3-uptoboll-0"
            elif kk5UpToBoll and f5po[3][1]==1:
                return "sell-uptoboll-3-uptoboll-1"
            elif kk5UpToBoll and f5po[3][1]==3:
                return "sell-uptoboll-3-uptoboll-3"
            elif kk5Up and not kk5Boll:
                return "sell-uptoboll-3-up-0"

        elif kk1Up:
            if kk5Down and not kk5Boll:
                return "sell-up-1-down-1"
            elif kk5DownToBoll and f5po[1][1]==0:
                return "sell-up-1-downtoboll-0"
            elif kk5DownToBoll and f5po[1][1]==1:
                return "sell-up-1-downtoboll-1"
            elif kk5DownToBoll and f5po[1][1]==3:
                return "sell-up-1-downtoboll-3"
            elif kk5Boll and f5po[2][1]==0:
                return "sell-up-1-boll-0"
            elif kk5Boll and f5po[2][1]==1:
                return "sell-up-1-boll-1"
            elif kk5Boll and f5po[2][1]==3:
                return "sell-up-1-boll-3"
            elif kk5UpToBoll and f5po[3][1]==0:
                return "sell-up-1-uptoboll-0"
            elif kk5UpToBoll and f5po[3][1]==1:
                return "sell-up-1-uptoboll-1"
            elif kk5UpToBoll and f5po[3][1]==3:
                return "sell-up-1-uptoboll-3"
            elif kk5Up and not kk5Boll:
                return "sell-up-1-up-0"

        return None

    return f1po,f5po

