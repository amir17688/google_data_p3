__author__ = 'etye'
import unittest
import requests
import json
#import logging
import datetime

from Testing.config import __CONFIG__
class TaskTestPlan(unittest.TestCase):
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
        /api/tasks/create/<string:token>
        POST OPTIONS


    '''
    def test_tasks_create_LectureToken(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        headers = {'content-type': 'application/json'}
        url = self.__class__.url_+'api/tasks/create/_QA_TOKEN_TEST_LECTURER'
        #params = {'seToken': 'seToken' }

        data = {
            'title':'task1',
		    'courseId':1234567890,
		    'description':'pls fddfsdfdsk',
		    'dueDate':{'year':2010,
		    'month':2,
		    'day':4
		    }, 'isPersonal':True,
		    'components':[
		    {
		    'type' : 'should be type1',
		    'label' : 'should be label1',
		    'isMandatory' : True,
		    'order' : 1
		    },
		    {
		    'type' : 'should be type2',
		    'label' : 'should be label2',
		    'isMandatory' : True,
		    'order' : 2
		    },
		    {
		    'type' : 'should be type3',
		    'label' : 'should be label3',
		    'isMandatory' : False,
		    'order' : 3
		    }
            ]
        }
        #r = requests.post(self.__class__.url_+'api/courses/create/'+__CONFIG__['TOKENS']['STUDENT'],data=payload)
        r = requests.post(url, data=json.dumps(data), headers=headers)
        self.assertEquals(r.status_code, 201, 'message: ' + r.json()['message'])
        print("***********************************************")
        print(self._testMethodName+"Has finished Successfully")
        print("***********************************************")

    def test_tasks_create_Student_Token(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        headers = {'content-type': 'application/json'}
        url = self.__class__.url_+'api/tasks/create/_QA_TOKEN_TEST_STUDENT'
        #params = {'seToken': 'seToken' }

        data = {
            'title':'task1',
		    'courseId':1234567890,
		    'description':'pls fddfsdfdsk',
		    'dueDate':{'year':2010,
		    'month':2,
		    'day':4
		    }, 'isPersonal':True,
		    'components':[
		    {
		    'type' : 'should be type1',
		    'label' : 'should be label1',
		    'isMandatory' : True,
		    'order' : 1
		    },
		    {
		    'type' : 'should be type2',
		    'label' : 'should be label2',
		    'isMandatory' : True,
		    'order' : 2
		    },
		    {
		    'type' : 'should be type3',
		    'label' : 'should be label3',
		    'isMandatory' : False,
		    'order' : 3
		    }
            ]
        }
        #r = requests.post(self.__class__.url_+'api/courses/create/'+__CONFIG__['TOKENS']['STUDENT'],data=payload)
        r = requests.post(url, data=json.dumps(data), headers=headers)
        self.assertEquals(r.status_code, 201, 'message: ' + r.json()['message'])
        print("***********************************************")
        print(self._testMethodName+"Has finished Successfully")
        print("***********************************************")

    def test_tasks_create_Student_Token(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        headers = {'content-type': 'application/json'}
        url = self.__class__.url_+'api/tasks/create/INVALIDTOKEN'
        #params = {'seToken': 'seToken' }

        data = {
        'title':'task1',
		'courseId':1234567890,
		'description':'pls fddfsdfdsk',
		'dueDate':{'year':2010,
		'month':2,
		'day':4
		}, 'isPersonal':True,
		'components':[
		{
		'type' : 'should be type1',
		'label' : 'should be label1',
		'isMandatory' : True,
		'order' : 1
		},
		{
		'type' : 'should be type2',
		'label' : 'should be label2',
		'isMandatory' : True,
		'order' : 2
		},
		{
		'type' : 'should be type3',
		'label' : 'should be label3',
		'isMandatory' : False,
		'order' : 3
		}
        ]
        }
        #r = requests.post(self.__class__.url_+'api/courses/create/'+__CONFIG__['TOKENS']['STUDENT'],data=payload)
        r = requests.post(url, data=json.dumps(data), headers=headers)
        self.assertEquals(r.status_code, 201, 'message: ' + r.json()['message'])
        print("***********************************************")
        print(self._testMethodName+"Has finished Successfully")
        print("***********************************************")

    '''
    /api/tasks/submitGrade/<string:token>/<string:taskId>/<string:projectname>
    '''

    def test_submitGrade_Lecturer(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        headers = {'content-type': 'application/json'}
        url = self.__class__.url_ +'api/tasks/submitGrade/_QA_TOKEN_TEST_LECTURER/_QA__TEST_PROJECT/QA_TEST_PROJECT_NAME'
        #params = {'seToken': 'seToken' }
        data = {
	        'title': 'task1',
	        'courseId': 1234567890,
	        'description': 'plsfddfsdfdsk',
        	'dueDate': {
	        	'year': 2010,
	        	'month': 2,
	        	'day': 4
	        },
        	'isPersonal': True,
        	'components': [{
        		'type': 'shouldbetype1',
        		'label': 'shouldbelabel1',
        		'isMandatory': True,
        		'order': 1
        	},
        	{
        		'type': 'shouldbetype2',
        		'label': 'shouldbelabel2',
        		'isMandatory': True,
        		'order': 2
        	},
        	{
        		'type': 'shouldbetype3',
        		'label': 'shouldbelabel3',
        		'isMandatory': False,
        		'order': 3
        	}]
        }


        r = requests.post(url, data=json.dumps(data), headers=headers)

        print(r._content)

        if(r.status_code!=201):print("_____"+self._testMethodName+" has Failed"+"_____" + r._content)
        self.assertEquals(r.status_code, 201)
        self.assertEquals(r.status_code, 201, 'message: ' + r.json()['message'])

    def test_submitGrade_Student(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        headers = {'content-type': 'application/json'}
        url = self.__class__.url_ +'api/tasks/submitGrade/_QA_TOKEN_TEST_STUDENT/_QA__TEST_PROJECT/QA_TEST_PROJECT_NAME'
        #params = {'seToken': 'seToken' }
        data = {
	        'title': 'task1',
	        'courseId': 1234567890,
	        'description': 'plsfddfsdfdsk',
        	'dueDate': {
	        	'year': 2010,
	        	'month': 2,
	        	'day': 4
	        },
        	'isPersonal': True,
        	'components': [{
        		'type': 'shouldbetype1',
        		'label': 'shouldbelabel1',
        		'isMandatory': True,
        		'order': 1
        	},
        	{
        		'type': 'shouldbetype2',
        		'label': 'shouldbelabel2',
        		'isMandatory': True,
        		'order': 2
        	},
        	{
        		'type': 'shouldbetype3',
        		'label': 'shouldbelabel3',
        		'isMandatory': False,
        		'order': 3
        	}]
        }


        r = requests.post(url, data=json.dumps(data), headers=headers)

        print(r._content)
        if(r.status_code!=201):print("_____"+self._testMethodName+" has Failed"+"_____" + r._content)
        self.assertEquals(r.status_code, 404)
       #self.assertEquals(r.status_code, 400, 'message: ' + r.json()['message'])

    def test_submitGrade_INVALIDTOKEN(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        headers = {'content-type': 'application/json'}
        url = self.__class__.url_ +'api/tasks/submitGrade/InvalidToken/invalidId/InvalidProject'
        #params = {'seToken': 'seToken' }
        data = {
	        'title': 'task1',
	        'courseId': 1234567890,
	        'description': 'fun course',
        	'dueDate': {
	        	'year': 2010,
	        	'month': 2,
	        	'day': 4
	        },
        	'isPersonal': True,
        	'components': [{
        		'type': 'shouldbetype1',
        		'label': 'shouldbelabel1',
        		'isMandatory': True,
        		'order': 1
        	},
        	{
        		'type': 'shouldbetype2',
        		'label': 'shouldbelabel2',
        		'isMandatory': True,
        		'order': 2
        	},
        	{
        		'type': 'shouldbetype3',
        		'label': 'shouldbelabel3',
        		'isMandatory': False,
        		'order': 3
        	}]
        }


        r = requests.post(url, data=json.dumps(data), headers=headers)

        print(r._content)
        if(r.status_code!=201):print("_____"+self._testMethodName+" has Failed"+"_____" + r._content)
        self.assertEquals(r.status_code, 404)

    '''
    /api/tasks/submitTask/<string:token>/<string:taskId>/<stringProjectName>
    '''
    def test_submitTask_LECTURER(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        headers = {'content-type': 'application/json'}
        url = self.__class__.url_ +'api/tasks/submitTask/_QA_TOKEN_TEST_LECTURER/_QA__TEST_PROJECT/QA_TEST_PROJECT_NAME'
        #params = {'seToken': 'seToken' }
        data = {
	'title': 'task1',
	'courseId': 1234567890,
	'description': 'plsfddfsdfdsk',
	'dueDate': {
		'year': 2010,
		'month': 2,
		'day': 4
	},
	'isPersonal': True,
	'components': [{
		'type': 'shouldbetype1',
		'label': 'shouldbelabel1',
		'isMandatory': True,
		'order': 1
	},
	{
		'type': 'shouldbetype2',
		'label': 'shouldbelabel2',
		'isMandatory': True,
		'order': 2
	},
	{
		'type': 'shouldbetype3',
		'label': 'shouldbelabel3',
		'isMandatory': False,
		'order': 3
	}]
}


        r = requests.post(url, data=json.dumps(data), headers=headers)

        print(r._content)
        if(r.status_code!=201):print("_____"+self._testMethodName+" has Failed"+"_____" + r._content)
        self.assertEquals(r.status_code, 500)

    def test_submitTask_STUDENT(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        headers = {'content-type': 'application/json'}
        url = self.__class__.url_ +'api/tasks/submitTask/_QA_TOKEN_TEST_STUDENT/_QA__TEST_PROJECT/QA_TEST_PROJECT_NAME'
        #params = {'seToken': 'seToken' }
        data = {
	        'title': 'task1',
	        'courseId': 1234567890,
	        'description': 'plsfddfsdfdsk',
	        'dueDate': {
		        'year': 2010,
		        'month': 2,
		        'day': 4
	        },
	        'isPersonal': True,
	        'components': [{
	        	'type': 'shouldbetype1',
	        	'label': 'shouldbelabel1',
	        	'isMandatory': True,
	        	'order': 1
        	},
        	{
        		'type': 'shouldbetype2',
        		'label': 'shouldbelabel2',
        		'isMandatory': True,
	        	'order': 2
        	},
        	{
        		'type': 'shouldbetype3',
        		'label': 'shouldbelabel3',
        		'isMandatory': False,
        		'order': 3
        	}]
        }


        r = requests.post(url, data=json.dumps(data), headers=headers)

        print(r._content)
        if(r.status_code!=201):print("_____"+self._testMethodName+" has Failed"+"_____" + r._content)
        self.assertEquals(r.status_code, 500)