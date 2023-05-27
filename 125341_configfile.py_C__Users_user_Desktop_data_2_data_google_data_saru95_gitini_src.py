#! /usr/bin/python

import sys
import os

def readname():
	with open('/usr/bin/src/cfg.txt', 'r') as file:
		datas = file.readlines()
	name = str(datas[0])
	return name

def reademail():
	with open('/usr/bin/src/cfg.txt', 'r') as file:
		datas = file.readlines()
	email = str(datas[1])
	return email