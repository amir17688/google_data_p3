#!/usr/bin/python
import sys
sys.path.append('../')
from nessrest import ness6rest

import getpass
user = getpass._raw_input('User: ')
password = getpass.getpass()

scan = ness6rest.Scanner(url="https://127.0.0.1:8834",login=user,password=password, insecure=True)
scan.action(action="scans", method="get")
for s in scan.res['scans']:
  scan.scan_name = s['name']
  scan.scan_id = s['id']
  xml_nessus = scan.download_scan(export_format='nessus')
  fp = open('%s_%s.nessus'%(scan.scan_name,scan.scan_id),"w")
  fp.write(xml_nessus)
  fp.close()

