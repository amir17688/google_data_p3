import urllib2

def connection():
    try:
       response=urllib2.urlopen('https://www.google.co.in/?gfe_rd=cr&ei=wZp5VPObK8vDuASSqIDoDw&gws_rd=ssl')
       return True
    except urllib2.URLError as err: 
       return False
