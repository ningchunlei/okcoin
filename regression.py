import sys
import time,os
from datetime import datetime,timedelta
import okcoin_websocket
from stock import stock,KLine

startime = sys.argv[1].replace(","," ")
endtime = sys.argv[2].replace(","," ")

print startime
store_dir = "/root/ningcl/btc"

class RStock(stock):

    def __init__(self,symbol,stockType,maxLength):
        super(RStock,self).__init__(symbol,stockType,maxLength)

    def fetchKLine(self):
        if self.stocks[-1] == 0 or self.stocks[-1] == None:
            fstart = startime
        else:
            ktime = datetime.fromtimestamp(self.stocks[-1])
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
        offset = (tstart-tdaytime)/24*60*60
        fwriter.seek(offset)

        klines=[]
        while len(klines)<length:
            line = fwriter.readline()
            if line == "":
                break
            print line.split(",")
            klines.append(KLine(line.split(","),"kline"))

        return klines


stock1Min = RStock("btc_cny",stock.OneMin,30)
stock5Min = RStock("btc_cny",stock.FiveMin,30)
stock15Min = RStock("btc_cny",stock.FifteenMin,30)

stock1Min.fetchKLine()
stock5Min.fetchKLine()
stock15Min.fetchKLine()

overtime = time.mktime(datetime.strptime(endtime,"%y-%m-%d %H:%M").timetuple())

cache1Min = []
kline5 = None
kline15 = None


while stock1Min.stocks[-1].time < overtime:
    if len(cache1Min)==0:
        cache1Min = stock1Min.readKlines(stock1Min.stocks[-1].time,100)
        while len(cache1Min)!=0:
            kline1Min = cache1Min.pop()
            if kline5 == None:
                kline5 = KLine(kline1Min,"copy")
                dt = datetime.fromtimestamp(kline1Min.time)
                kline5.time = dt - timedelta(minutes=dt.minute % 5)
            elif kline5 != None:
                dt = datetime.fromtimestamp(kline1Min.time)
                if dt.minute % 5 == 0:
                    kline5 = KLine(kline1Min,"copy")
                    kline5.time = dt - timedelta(minutes=dt.minute % 5)
                else:
                    if kline5.high < kline1Min.high:
                        kline5.high = kline1Min.high
                    if kline5.low > kline1Min.low:
                        kline5.low = kline1Min.low
                    kline5.close = kline1Min.close


            if kline15 == None:
                kline15 = KLine(kline1Min,"copy")
                dt = datetime.fromtimestamp(kline1Min.time)
                kline15.time = dt - timedelta(minutes=dt.minute % 15)
            elif kline15 != None:
                dt = datetime.fromtimestamp(kline1Min.time)
                if dt.minute % 15 == 0:
                    kline15 = KLine(kline1Min,"copy")
                    kline15.time = dt - timedelta(minutes=dt.minute % 15)
                else:
                    if kline15.high < kline1Min.high:
                        kline15.high = kline1Min.high
                    if kline15.low > kline1Min.low:
                        kline15.low = kline1Min.low
                    kline15.close = kline1Min.close

            stock1Min.on_kline(kline1Min)
            stock5Min.on_kline(kline5)
            stock15Min.on_kline(kline15)
            okcoin_websocket.go()
