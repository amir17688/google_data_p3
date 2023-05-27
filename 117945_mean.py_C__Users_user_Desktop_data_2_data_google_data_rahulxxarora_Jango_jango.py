import sys
import requests
from bs4 import BeautifulSoup
import re

def handle(query):
    flag = 0
    url = "http://www.merriam-webster.com/dictionary/"
    url = url + query
    page = requests.get(url)
    src = page.text
    ob = BeautifulSoup(src, "lxml")

    results = []
    for info in ob.findAll('div',{'class':'ld_on_collegiate'}):
        word = info.text
        word = word.split(':')
        for i in word:
            if i.strip():
                flag = 1
                results.append(i.strip())

    if flag==0:
        results.append("No result found")
    return results

query = ""
flag = 0

for arg in sys.argv:
   if flag==1:
      query = arg
      break
   if arg=='of':
      flag = 1

try:
   ans = handle(query)
   for i in ans:
      print i
except:
   print "Something went wrong."

