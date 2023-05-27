__author__ = 'etye'
import unittest
import requests
import json
#import logging
import datetime

from Testing.config import __CONFIG__
class MessagesTestPlan(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        debug = __CONFIG__['DEBUG']
        if debug:
            url = __CONFIG__['PATHS']['DEBUG']
        else:
            url = __CONFIG__['PATHS']['PRODUCTION']
        cls.url_ = url
        request = requests.get(url+'api/qa/init')
        if 200 <= request.status_code <= 299:
            print 'Initialized'
    '''
    /api/messages/create/<string:token>
    POST OPTIONS
    token  user  payload  e  msg
    This call will create a new Message in the DB
    '''
    def test_messageCreate_Student(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        headers = {'content-type': 'application/json'}
        url = self.__class__.url_+'api/messages/create/_QA_TOKEN_TEST_STUDENT'
        #params = {'seToken': 'seToken' }
        data = {
            'groupId' : 123456789,
            'message' : 'Class is canceled',
            'isProject' : True
        }

        #r = requests.post(self.__class__.url_+'api/courses/create/'+__CONFIG__['TOKENS']['STUDENT'],data=payload)
        r = requests.post(url, data=json.dumps(data), headers=headers)
        self.assertEquals(r.status_code, 403, 'message: ' + r.json()['message'])
        print("***********************************************")
        print(self._testMethodName+"Has finished Successfully")
        print("***********************************************")

    def test_messageCreate_Lecturer(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        headers = {'content-type': 'application/json'}
        url = self.__class__.url_+'api/messages/create/_QA_TOKEN_TEST_LECTURER'
        #params = {'seToken': 'seToken' }
        data = {
            'groupId' : 123456789,
            'message' : 'Class is canceled',
            'isProject' : True
        }

        #r = requests.post(self.__class__.url_+'api/courses/create/'+__CONFIG__['TOKENS']['STUDENT'],data=payload)
        r = requests.post(url, data=json.dumps(data), headers=headers)
        self.assertEquals(r.status_code, 403, 'message: ' + r.json()['message'])
        print("***********************************************")
        print(self._testMethodName+"Has finished Successfully")
        print("***********************************************")

    def test_messageCreate_INVALIDTOKEN(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        headers = {'content-type': 'application/json'}
        url = self.__class__.url_+'api/messages/create/invlaidToken'
        #params = {'seToken': 'seToken' }
        data = {
            'groupId' : 123456789,
            'message' : 'Class is canceled',
            'isProject' : True
        }

        #r = requests.post(self.__class__.url_+'api/courses/create/'+__CONFIG__['TOKENS']['STUDENT'],data=payload)
        r = requests.post(url, data=json.dumps(data), headers=headers)
        self.assertEquals(r.status_code, 403, 'message: ' + r.json()['message'])
        print("***********************************************")
        print(self._testMethodName+"Has finished Successfully")
        print("***********************************************")

    '''
    /api/messages/deleteMessage/<string:token>/<string:msgId>
    OPTIONS DELETE
    token  msgId  user  msg  e
    >This Call will delete a message by owner token
    Route Parameters
    - SeToken: token - msgId: 1234567890

    Payload
    - NONE
    '''
    def test_deleteMessage_Student(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        #create Message and get the id to call delete message API REST
        r = requests.delete(self.__class__.url_+'api/messages/deleteMessage/_QA_TOKEN_TEST_STUDENT/<string:msgID')
        self.assertEquals(r.status_code, 204)
        print("***********************************************")
        print(self._testMethodName+"Has finished Successfully")
        print("***********************************************")

    def test_deleteMessage_Lecturer(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        #create Message and get the id to call delete message API REST
        r = requests.delete(self.__class__.url_+'api/messages/deleteMessage/_QA_TOKEN_TEST_LECTURER/<string:msgID')
        self.assertEquals(r.status_code, 204)
        print("***********************************************")
        print(self._testMethodName+"Has finished Successfully")
        print("***********************************************")

    def test_deleteMessage_invalidToken(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        #create Message and get the id to call delete message API REST
        r = requests.delete(self.__class__.url_+'api/messages/deleteMessage/InvalidToken/<string:msgID')
        self.assertEquals(r.status_code, 204)
        print("***********************************************")
        print(self._testMethodName+"Has finished Successfully")
        print("***********************************************")

    '''
    /api/messages/getAllUserMessages/<string:token>
    HEAD OPTIONS GET
        token  user  arr  allMsgs  projectMsgs  m  msgDic  msgTime  i
    >This Call will return an array of all messages (sorted by date),

    Route Parameters
    - SeToken: token
    - groupId: 1234567890

        Payload
    - NONE

    '''
    def test_getAllUserMessages_Lecturer(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        #create Message and get the id to call delete message API REST
        r = requests.get(self.__class__.url_+'api/messages/getAllUserMessages/_QA_TOKEN_TEST_LECTURER')
        self.assertEquals(r.status_code, 200)
        print("***********************************************")
        print(self._testMethodName+"Has finished Successfully")
        print("***********************************************")

    def test_getAllUserMessages_STUDENT(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        #create Message and get the id to call delete message API REST
        r = requests.get(self.__class__.url_+'api/messages/getAllUserMessages/_QA_TOKEN_TEST_STUDENT')
        self.assertEquals(r.status_code, 200)
        print("***********************************************")
        print(self._testMethodName+"Has finished Successfully")
        print("***********************************************")

'''
/api/messages/create/<string:token>
POST OPTIONS
token  user  payload  e  msg
This call will create a new Message in the DB
Route Parameters
- seToken: 'seToken'

Payload
- JSON Object, Example:
{
'groupId' : 123456789,
'message' : 'Class is canceled',
'isProject' : true
}
'''

