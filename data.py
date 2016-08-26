import Client
from datetime import datetime

store_dir=""

while True:
    try:
        klines = Client.fetchKline("btc","1min",500)
        for kline in klines:
            ktime = datetime.fromtimestamp(kline.time)
            fname = ktime.strftime("%y-%m-%d")
            ktimestr = ktime.strftime("%y-%m-%d %H:%M")
            fwriter = open(store_dir+"/"+fname,"wa+")

            #32 + 16 + 2 = 50 + close open high low,time
            fwriter.write("%6.2f,%6.2f,%6.2f,%6.2f,%s\r\n",kline.close,kline.open,kline.high,kline.low,ktimestr)

    except Exception as e:
        pass


