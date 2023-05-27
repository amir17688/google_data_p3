import requests
from bs4 import BeautifulSoup

def strip_non_ascii(string):
    stripped = (c for c in string if 0 < ord(c) < 127)
    return ''.join(stripped)


while 1:
   url = "http://www.ajokeaday.com/ChisteAlAzar.asp?"
   page = requests.get(url)
   src = page.text
   ob = BeautifulSoup(src, "lxml")

   for info in ob.findAll('div',{'class':'chiste'}):
      joke = info.text.strip()
      joke = strip_non_ascii(joke)
         
   if len(joke)<=100:
      print joke
      break
   else:
      continue
      
