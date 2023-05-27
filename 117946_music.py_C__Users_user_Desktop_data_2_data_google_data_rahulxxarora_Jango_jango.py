import random
import os
import sys
import ConfigParser
import jangopath

Config = ConfigParser.ConfigParser()

try:
   Config.read(jangopath.CONFIG_PATH)
except:
   print "Couldn't read config file."

music = Config.get('Directory', 'music')

flag = 0
for arg in sys.argv:
   if flag==1:
      check = music + "/" + arg
      break
   if arg.lower()=="a" or arg.lower()=="some":
      flag = 1 

try:
   files = os.listdir(check)

   ans = files[random.randrange(len(files))]
   check = check + "/" + ans
   check = check.strip()
   print "Playing " + ans

   f = open('.Jango_temp.txt','w')
   f.write(check)
   f.close()

   path = jangopath.MODULE_PATH + "/music_helper.py"
   os.system('python ' + path + " &")

except:
   print "No such directory exists"





      
