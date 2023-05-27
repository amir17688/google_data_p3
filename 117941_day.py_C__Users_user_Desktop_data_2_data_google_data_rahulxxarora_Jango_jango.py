import time

def handle():
   localtime = time.asctime( time.localtime(time.time()) )
   date = localtime.split()
   print "Current day is : " + date[0]

handle()

