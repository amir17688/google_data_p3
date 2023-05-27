#! /usr/bin/python

import sys
import os
import shutil
import configfile
from datetime import datetime

location = str(sys.argv[1])
pathf = location + "/LICENSE.txt"
os.system("touch "+pathf)
shutil.copyfile("/usr/bin/licenses/artistic.txt",pathf)

fullname = str(configfile.readname())
year = str(datetime.now().year)

with open(pathf, 'r') as file:
    data = file.readlines()

data[2] = year + "  " + fullname + '\n'

with open(pathf, 'w') as file:
    file.writelines( data )

(root,ext) = os.path.splitext(pathf)
os.rename(root + ".txt", root + ".md")