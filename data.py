import Client
from datetime import datetime
import time
import os

store_dir="/tmp"

def store(filetype,klines):
    for kline in klines:
        ktime = datetime.fromtimestamp(kline.time)
        fname = ktime.strftime("%y-%m-%d")
        tday = datetime.strptime(fname,"%y-%m-%d")
        tdaytime = time.mktime(tday.timetuple())
        ktimestr = ktime.strftime("%y-%m-%d %H:%M")

        fd = os.open(store_dir+"/"+fname+"."+filetype,os.O_CREAT)
        os.close(fd)

        fwriter = open(store_dir+"/"+fname+"."+filetype,"r+")
        offset = (kline.time-tdaytime)/24*60*60
        fwriter.seek(offset)
        #32 + 16 + 2 = 50 + close open high low,time
        fwriter.write("%6.2f,%6.2f,%6.2f,%6.2f,%s\r\n" % (kline.close,kline.open,kline.high,kline.low,ktimestr))
        fwriter.close()

while True:
    klines = Client.fetchKline("btc_cny","1min",500,None)
    store("1",klines)

    klines = Client.fetchKline("btc_cny","5min",500,None)
    store("5",klines)

    klines = Client.fetchKline("btc_cny","15min",500,None)
    store("15",klines)

    time.sleep(60)



