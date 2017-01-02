import sys
import time,os
from datetime import datetime,timedelta
import okcoin_websocket
from stock import stock,KLine
import time
from datetime import datetime
import logging

startime = sys.argv[1].replace(","," ")
endtime = sys.argv[2].replace(","," ")

store_dir = "/root/ningcl/btc"

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S'
                    )
pricelogging = logging.getLogger("price")

class RStock(stock):

    def __init__(self,symbol,stockType,maxLength):
        super(RStock,self).__init__(symbol,stockType,maxLength)

    def fetchKLine(self):
        if self.lastKline() == 0 or self.lastKline() == None:
            fstart = startime
        else:
            ktime = datetime.fromtimestamp(self.lastKline().time)
            fstart = ktime.strftime("%y-%m-%d %H:%M")

        dt = datetime.strptime(fstart,"%y-%m-%d %H:%M")
        if self._stockType == stock.OneMin:
            diff = 1
        elif self._stockType == stock.FiveMin:
            diff = 5
            dt = dt - timedelta(minutes=dt.minute % 5)
        elif self._stockType == stock.FifteenMin:
            diff = 15
            dt = dt - timedelta(minutes=dt.minute % 15)

        fstart = (dt - timedelta(minutes=diff*(self._maxLength-1))).strftime("%y-%m-%d %H:%M")

        klines=[]
        while len(klines) < self._maxLength:
            xlines = self.readKLine(fstart,self._maxLength-len(klines))
            if len(xlines)==0:
                break
            klines.extend(xlines)
            diff = 0
            if self._stockType == stock.OneMin:
                diff = 1
            elif self._stockType == stock.FiveMin:
                diff = 5
            elif self._stockType == stock.FifteenMin:
                diff = 15
            fstart = (datetime.fromtimestamp(klines[-1].time) + timedelta(minutes=diff)).strftime("%y-%m-%d %H:%M")
        self.stocks=[0]*2*self._maxLength
        self.stocks[0:len(klines)]=klines
        self.cursor = len(klines)-1
        self.trades=[0]*2*self._maxLength
        self.baseTime = klines[0].time
        self.macd(len(klines)-1,len(klines))

    def readKlines(self,ftime,length):
        if self._stockType == stock.OneMin:
            diff = 1
        elif self._stockType == stock.FiveMin:
            diff = 5
        elif self._stockType == stock.FifteenMin:
            diff = 15
        fstart = (datetime.fromtimestamp(ftime) + timedelta(minutes=diff)).strftime("%y-%m-%d %H:%M")

        klines = []
        while len(klines) < length:
            xlines = self.readKLine(fstart,length-len(klines))
            if len(xlines)==0:
                break
            klines.extend(xlines)
            diff = 0
            if self._stockType == stock.OneMin:
                diff = 1
            elif self._stockType == stock.FiveMin:
                diff = 5
            elif self._stockType == stock.FifteenMin:
                diff = 15
            fstart = (datetime.fromtimestamp(klines[-1].time) + timedelta(minutes=diff)).strftime("%y-%m-%d %H:%M")

        return klines

    def readKLine(self,fstart,length):
        tday  = datetime.strptime(fstart,"%y-%m-%d %H:%M")
        tstart = time.mktime(tday.timetuple())

        fname = tday.strftime("%y-%m-%d")
        tdaytime = time.mktime(datetime.strptime(fname,"%y-%m-%d").timetuple())


        filetype = None
        if self._stockType == stock.OneMin:
            filetype = "1"
        elif self._stockType == stock.FiveMin:
            filetype = "5"
        elif self._stockType == stock.FifteenMin:
            filetype = "15"

        if os.path.exists(store_dir+"/"+fname+"."+filetype) == False:
            return []

        fwriter = open(store_dir+"/"+fname+"."+filetype,"r+")
        if filetype == "1":
            offset = (tstart-tdaytime)/60
        elif filetype=="5":
            offset = (tstart-tdaytime)/(60*5)
        elif filetype == "15":
            offset = (tstart-tdaytime)/(60*15)
        fwriter.seek(offset*48)

        klines=[]
        while len(klines)<length:
            line = fwriter.readline()
            if line == "":
                break
            print line.split(",")
            klines.append(KLine(line.split(","),"kline"))

        return klines


stock1Min = RStock("btc_cny",stock.OneMin,500)
stock5Min = RStock("btc_cny",stock.FiveMin,500)
stock15Min = RStock("btc_cny",stock.FifteenMin,500)
stock1Min.fetchKLine()
stock5Min.fetchKLine()
stock15Min.fetchKLine()

okcoin_websocket.stock1Min = stock1Min
okcoin_websocket.stock5Min = stock5Min
okcoin_websocket.stock15Min = stock15Min


overtime = time.mktime(datetime.strptime(endtime,"%y-%m-%d %H:%M").timetuple())

cache1Min = []
kline5 = None
kline15 = None


while stock1Min.lastKline().time < overtime:
    if len(cache1Min)==0:
        cache1Min = stock1Min.readKlines(stock1Min.lastKline().time,100)
        cache1Min.reverse()
        while len(cache1Min)!=0:
            kline1Min = cache1Min.pop()
            if kline5 == None:
                kline5 = KLine(kline1Min,"copy")
                dt = datetime.fromtimestamp(kline1Min.time)
                kline5.time = time.mktime((dt - timedelta(minutes=dt.minute % 5)).timetuple())
            elif kline5 != None:
                dt = datetime.fromtimestamp(kline1Min.time)
                if dt.minute % 5 == 0:
                    kline5 = KLine(kline1Min,"copy")
                    kline5.time = time.mktime((dt - timedelta(minutes=dt.minute % 5)).timetuple())
                else:
                    if kline5.high < kline1Min.high:
                        kline5.high = kline1Min.high
                    if kline5.low > kline1Min.low:
                        kline5.low = kline1Min.low
                    kline5.close = kline1Min.close


            if kline15 == None:
                kline15 = KLine(kline1Min,"copy")
                dt = datetime.fromtimestamp(kline1Min.time)
                kline15.time = time.mktime((dt - timedelta(minutes=dt.minute % 15)).timetuple())
            elif kline15 != None:
                dt = datetime.fromtimestamp(kline1Min.time)
                if dt.minute % 15 == 0:
                    kline15 = KLine(kline1Min,"copy")
                    kline15.time = time.mktime((dt - timedelta(minutes=dt.minute % 15)).timetuple())
                else:
                    if kline15.high < kline1Min.high:
                        kline15.high = kline1Min.high
                    if kline15.low > kline1Min.low:
                        kline15.low = kline1Min.low
                    kline15.close = kline1Min.close
            stock1Min.on_kline(kline1Min)
            stock5Min.on_kline(kline5)
            stock15Min.on_kline(kline15)
            #pricelogging.info(stock1Min.lastKline())
            okcoin_websocket.go17()
