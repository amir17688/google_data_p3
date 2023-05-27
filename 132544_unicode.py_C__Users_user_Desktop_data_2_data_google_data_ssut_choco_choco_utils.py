#-*- coding: utf-8 -*-

def u(string):
    try:
        return string.encode('utf-8')
    except Exception, e:
        return string