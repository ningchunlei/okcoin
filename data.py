import Client
from datetime import datetime
import time

store_dir="/tmp"

while True:
    klines = Client.fetchKline("btc_cny","1min",500)
    for kline in klines:
        ktime = datetime.fromtimestamp(kline.time)
        fname = ktime.strftime("%y-%m-%d")
        tday = datetime.strptime(fname,"%y-%m-%d")
        tdaytime = time.mktime(tday.timetuple())
        ktimestr = ktime.strftime("%y-%m-%d %H:%M")
        fwriter = open(store_dir+"/"+fname,"wa+")
        offset = kline.time-tdaytime/24*60*60
        print offset
        fwriter.seek(offset)
        #32 + 16 + 2 = 50 + close open high low,time
        fwriter.write("%6.2f,%6.2f,%6.2f,%6.2f,%s\r\n" % (kline.close,kline.open,kline.high,kline.low,ktimestr))
    break


