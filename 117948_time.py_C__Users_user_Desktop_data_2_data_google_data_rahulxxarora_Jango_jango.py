import time

def handle():
   localtime = time.asctime( time.localtime(time.time()) )
   date = localtime.split()
   print "Current time is : " + date[3]

handle()

