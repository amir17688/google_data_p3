# The MIT License (MIT)
# 
# Copyright (c) 2010-2015 Carnegie Mellon University
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import base64
import json
import logging
import os
import struct

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

import member


class SyncUsers(webapp.RequestHandler):
   
    isJson = False
   
    def post(self):
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")
        
        header = self.request.headers['Content-Type']
        logging.debug("Content-Type: '%s'" % header)
        if (str(header).startswith('text/plain')):
            self.isJson = True
            # set response to json
            self.response.headers['Content-Type'] = 'text/plain'
            data_dict = json.loads(self.request.body)
        else:
            self.response.headers['Content-Type'] = 'application/octet-stream'
            
        STR_VERSERVER = '01060000'
        INT_VERCLIENT = 0x01060000
        STR_VERCLIENT = '1.6'
 
        if not os.environ.has_key('HTTPS'):
            self.resp_simple(0, 'HTTPS environment variable not found')
            return

        if not os.environ.has_key('CURRENT_VERSION_ID'):
            self.resp_simple(0, 'CURRENT_VERSION_ID environment variable not found')
            return

        HTTPS = os.environ.get('HTTPS', 'off')
        CURRENT_VERSION_ID = os.environ.get('CURRENT_VERSION_ID', STR_VERSERVER)
        
        # SSL must be enabled
        if HTTPS.__str__() != 'on':
            self.resp_simple(0, 'Secure socket required.')
            return

        minlen = 4 + 4 + 4 + 4 + 4
                
        # get the data from the post
        data = self.request.body
        logging.debug("in body '%s'" % data)
    
        size = str.__len__(data)
        logging.debug("in size %d" % size)

        if size < minlen:
            self.resp_simple(0, 'Request was formatted incorrectly.')
            return
         
        # unpack all incoming data
        server = int(CURRENT_VERSION_ID[0:8], 16)
 
        if self.isJson:
            client = int(data_dict['ver_client'], 10)
        else:
            client = (struct.unpack("!i", data[0:4]))[0]
        logging.debug("in client %d" % client)
 
        if self.isJson:
            usrid = int(data_dict['usrid'], 10)
        else:
            usrid = (struct.unpack("!i", data[4:8]))[0]
        logging.debug("in usrid %d" % usrid)
 
        if self.isJson:
            usridlink = int(data_dict['usridlink'], 10)
        else:
            usridlink = (struct.unpack("!i", data[8:12]))[0]
        logging.debug("in usridlink %d" % usridlink)

        if self.isJson:
            numEntry = data_dict['usrids'].__len__()
        else:
            numEntry = (struct.unpack("!i", data[12:16]))[0]
        logging.debug("in numEntry %d" % numEntry)
        pos = 16
 
        expectedsize = 4 + 4 + 4 + 4 + (4 * numEntry)

        # append enough entries to hold the expected data
        usrids = []
        i = 0
        while numEntry > len(usrids):
            if self.isJson:
                otherid = int(data_dict['usrids'][i], 10)
                i += 1
            else:
                otherid = struct.unpack("!i", data[pos:pos + 4])[0]
                pos += 4
            usrids.append(otherid)
            logging.debug("in usrid known %i" % otherid)

        postSelf = False
        if self.isJson:
            if 'commit_b64' in data_dict:
                commit = base64.decodestring(data_dict['commit_b64'])
                postSelf = True
        else:
            if size > expectedsize:
                commit = data[pos:]
                postSelf = True
        if postSelf:
            logging.debug("in commitment '%s'" % commit)
            
        # client version check
        if client < INT_VERCLIENT:
            self.resp_simple(0, ('Client version mismatch; %s required.  Download latest client release first.' % STR_VERCLIENT))
            return        
                    
        # verify you have an existing user
        query = member.Member.all()
        query.filter('usr_id =', usrid)
        num = query.count()
        
        # user exists
        if num == 1:
            mem = query.get()
            
            # commit to group number
            if postSelf:            
                mem.usr_id_link = usridlink
                mem.put()
                key = mem.key()
                if not key.has_id_or_name():
                    self.resp_simple(0, 'Unable to update user.')
                    return

            # not posting signature, one must exist
            else:
                if mem.commitment == None:
                    self.resp_simple(0, 'Request was formatted incorrectly.')
                    return

            # get the entries for the group
            query = member.Member.all()
            query.filter('usr_id_link =', usridlink)
            mems = query.fetch(1000)

            # version
            if not self.isJson:
                self.response.out.write('%s' % struct.pack('!i', server))
            logging.debug("out server %i" % server)

            # lowest client version
            q = member.Member.all()
            q.filter('usr_id_link =', usridlink)
            m = q.fetch(1000)
            low_client = self.getLowestVersion(m)
            if not self.isJson:
                self.response.out.write('%s' % struct.pack('!i', low_client))
            logging.debug("out low_client %i" % low_client)

            # grand total
            total = 0
            for mem in mems:
                if mem.commitment != None:
                    total = total + 1
            
            if not self.isJson:
                self.response.out.write('%s' % struct.pack('!i', total))
            logging.debug("out total commits %i" % total)
      
            # add delta ids total
            delta = 0
            for mem in mems:
                posted = False
                for known in usrids:
                    if known == mem.usr_id:
                        posted = True                    
                if (not posted) & (mem.commitment != None):
                    delta = delta + 1
            
            if not self.isJson:
                self.response.out.write('%s' % struct.pack('!i', delta))
            logging.debug("out delta commits %i" % delta)
    
            deltas = []
            for mem in mems:
                posted = False
                for known in usrids:
                    if known == mem.usr_id:
                        posted = True                    
                if (not posted) & (mem.commitment != None):
                    length = str.__len__(mem.commitment)
                    if self.isJson:            
                        deltas.append({'usrid' : str(mem.usr_id), 'commit_b64' : base64.encodestring(mem.commitment) })
                    else:
                        self.response.out.write('%s%s' % (struct.pack('!ii', mem.usr_id, length), mem.commitment))
                    logging.debug("out mem.usr_id %i" % mem.usr_id)
                    logging.debug("out mem.commitment length %i" % length)
                    logging.debug("out mem.commitment '%s'" % mem.commitment)
        
        else:
            self.resp_simple(0, 'user %i does not exist' % (usrid))
            return       
                
        if self.isJson:            
            json.dump({"ver_server":str(server), "ver_low_client":str(low_client), "com_total":str(total), "com_deltas":deltas }, self.response.out)


    def resp_simple(self, code, msg):
        if self.isJson:            
            json.dump({"err_code":str(code), "err_msg":str(msg)}, self.response.out)
        else:
            self.response.out.write('%s%s' % (struct.pack('!i', code), msg))
        if code == 0:
            logging.error(msg)
    

    def getLowestVersion(self, mems):
        # get lowest available version
        INT_VERCLIENT = 0x01060000
        lowest = 0
        for mem in mems:
            if mem.client_ver != None:    
                cur = mem.client_ver                                
            else:
                cur = INT_VERCLIENT  # default
                
            if lowest == 0:
                lowest = cur  # needs a starting point
            
            if cur < lowest:
                lowest = mem.client_ver                
                
        return lowest
    

def main():
    STR_VERSERVER = '01060000'
    CURRENT_VERSION_ID = os.environ.get('CURRENT_VERSION_ID', STR_VERSERVER)
    isProd = CURRENT_VERSION_ID[8:9] == 'p'
    # Set the logging level in the main function
    if isProd:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.DEBUG)

    application = webapp.WSGIApplication([('/syncUsers', SyncUsers),
                                     ],
                                     debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()

