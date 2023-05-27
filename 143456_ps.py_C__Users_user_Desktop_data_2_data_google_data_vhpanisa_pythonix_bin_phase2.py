#!/usr/pkg/bin/python2.7
from __future__ import print_function
# ps: gives general info about process of the current user

import sys
import os
import argparse

def listprocs(tty=True, longformat=False, notty=False, endpoint=False, all=False):
    headers = ['psi_v','type','endpoint','name','state','blocked','priority',
        'utime','stime','execycleshi','execycleslo', 'tmemory', 'cmemory', 
        'smemory', 'sleep', 'parentpid', 'realuid', 'effectiveuid', 'procgrp',
        'nicevalue', 'vfsblock', 'blockproc', 'ctrltty', 'kipchi', 'kipclo', 
        'kcallhi', 'kcalllo']

    txtheader = ['pid','ctrltty','utime','name']

    procs = [id for id in os.listdir('/proc') if id.isdigit()]
    topdata = []    
    running = 0

    for proc in procs:
        with open('/proc/{}/psinfo'.format(proc), 'rb') as f:
          procdata = dict(zip(headers,f.read().split(' ')))
          procdata['pid'] = proc
          topdata.append(procdata)
        if procdata['state'] == 'R':
          running += 1
          
    print('{0: >5} {1: >3} {2: >5} {3}'.format('PID', 'TTY', 'TIME', 'CMD'))

    for proc in topdata:
        if not all:
          if tty and not notty and proc['ctrltty'] == '0': continue
          elif notty and not tty and proc['ctrltty'] != '0': continue
        for txt in txtheader:
            if txt == 'pid':
              s = '{0: >5}'
              if endpoint:
                value = proc['endpoint']
              else:
                value = proc[txt]
            elif txt == 'ctrltty':
              s = '{0: >3}'
              value = proc[txt]
            elif txt == 'utime':
              s = '{0: >5}'
              secs = int(proc[txt])
              mins = secs/60
              if mins >= 60:
                hours = mins//60
                mins = mins%60
              else:
                hours = 0
              value = str(hours)+':'+'{0:0>2}'.format(str(mins))
            else:
              s = '{0}'
              value = proc[txt]
            print(s.format(value), end=' ')
        print()

def main(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument('-a', action='store_true',
        help='Show only process with an attached tty')
    parser.add_argument('-e', action='store_true',
        help='Proccess Envirnoment after ps execution')
    parser.add_argument('-E', action='store_true',
        help='endpoint kernel instead of PID')
    parser.add_argument('-f', action='store_true',
        help='Long format')
    parser.add_argument('-l', action='store_true',
        help='Long format')
    parser.add_argument('-x', action='store_true',
        help='Adds processes with no attached tty')
    parser.add_argument('args', nargs=argparse.REMAINDER)

    argv = parser.parse_args()

    if argv.a or argv.e or argv.E or argv.f or argv.l or argv.x:
      listprocs(tty=argv.a, longformat=(argv.f or argv.l), notty=argv.x, endpoint=argv.E, all=argv.e)
    else:
      listprocs()

if __name__ == '__main__':
    main(sys.argv)
