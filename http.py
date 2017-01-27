from flask import request
from flask import Flask
from flask import render_template

import sys
import time,os
from datetime import datetime,timedelta
import okcoin_websocket
from stock import stock,KLine
import time
from datetime import datetime
import logging

import json
app = Flask(__name__)


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

cacheM=None

@app.route('/api/klineData.do', methods=['GET'])
def kline():
    global cacheM
    market = request.args.get('marketFrom', '')
    ty = request.args.get('type', '')
    limit = request.args.get('limit', '1000')
    since = request.args.get('since', '')

    kx = since

    ty = sys.argv[2]
    since = sys.argv[1]

    if cacheM==None:
        if ty == "0":
            ret = stock1Min.readKlines(int(since),int(limit))
        elif ty=="1":
            ret = stock5Min.readKlines(int(since),int(limit))
        elif ty=="2":
            ret = stock15Min.readKlines(int(since),int(limit))

        ret.reverse()
        kk = []
        tk = None
        for k in ret:
            kk.append([int(k.time)*1000,k.open,k.high,k.low,k.close,6])
            tk = k
        kk.reverse()
        cacheM = kk
    if kx!="":
        #return json.dumps([[int(kx),tk.open,tk.high,tk.low,tk.close,tk.vol]])
        return json.dumps([cacheM[-1]])
    #return json.dumps([[1485358200000,6196.99,6198.99,6185.01,6185.01,10.186]])
    return json.dumps(cacheM)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0")
