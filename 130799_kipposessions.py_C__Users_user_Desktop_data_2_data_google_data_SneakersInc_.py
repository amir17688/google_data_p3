#!/usr/bin/env python

from common.dbconnect import db_connect
from common.entities import KippoSession
from canari.maltego.entities import IPv4Address
from canari.maltego.message import Field, UIMessage
from canari.framework import configure

__author__ = 'catalyst256'
__copyright__ = 'Copyright 2014, Honeymalt Project'
__credits__ = []

__license__ = 'GPL'
__version__ = '0.1'
__maintainer__ = 'catalyst256'
__email__ = 'catalyst256@gmail.com'
__status__ = 'Development'

__all__ = [
    'dotransform'
]

#@superuser
@configure(
    label='HoneyMalt: Kippo Sessions',
    description='Connects to Kippo Honeypots via MYSQL db',
    uuids=['HoneyMalt.v2.Kippo_to_Session'],
    inputs=[('HoneyMalt', IPv4Address)],
    debug=False
)
def dotransform(request, response):
    host = request.fields['kippodatabase']
    ip = request.value
    x = db_connect(host)
    try:
        cursor = x.cursor()
        query = "select * from sessions where ip like %s"
        cursor.execute(query, (ip, ))
        for (id, starttime, endtime, sensor, ip, termsize, client) in cursor:
            e = KippoSession('%s' %(id))
            e.starttime = ('%s' %(starttime))
            e.endtime = ('%s' %(endtime))
            e.sensor = ('%s' %(sensor))
            e.ipaddr = ('%s' %(ip))
            e.termsize = ('%s' %(termsize))
            e.client = ('%s' %(client))
            e += Field('kippodatabase', host, displayname='Kippo Database')
            response += e
        return response
    except Exception as e:
        return response + UIMessage(str(e))

