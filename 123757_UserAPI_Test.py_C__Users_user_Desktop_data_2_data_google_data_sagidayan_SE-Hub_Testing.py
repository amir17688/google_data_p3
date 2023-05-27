__author__ = 'etye'
import unittest
import requests
import json
import datetime
from Testing.config import __CONFIG__

class UserTestPlan(unittest.TestCase):
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

    def test_getUserByToken_invalid(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        r = requests.get(self.__class__.url_+'api/users/getUserByToken/invalidtoken')
        self.assertEquals(r.status_code, 204)
        print("***********************************************")
        print(self._testMethodName+"Has finished Successfully")
        print("***********************************************")



    def test_getUserByToken_valid(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        r = requests.get(self.__class__.url_+'api/users/getUserByToken/'+__CONFIG__['TOKENS']['STUDENT'])
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json()['username'], 'qa_student')
        print("***********************************************")
        print(self._testMethodName+"Has finished Successfully")
        print("***********************************************")

    def test_getUserByToken_empty(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        r = requests.get(self.__class__.url_+'api/users/getUserByToken/')
        self.assertEquals(r.status_code, 204)
        print("***********************************************")
        print(self._testMethodName+"Has finished Successfully")
        print("***********************************************")

    def test_isStudent_Student(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        r = requests.get(self.__class__.url_+'api/users/getUserByToken/'+__CONFIG__['TOKENS']['STUDENT'])
        self.assertEquals(r.status_code, 200)
        self.assertFalse(r.json()['isLecturer'])
        print("***********************************************")
        print(self._testMethodName+"Has finished Successfully")
        print("***********************************************")

    def test_isLecturer_Lecturer(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        r = requests.get(self.__class__.url_+'api/users/getUserByToken/'+__CONFIG__['TOKENS']['LECTURER'])
        self.assertEquals(r.status_code, 200)
        self.assertTrue(r.json()['isLecturer'])
        print("***********************************************")
        print(self._testMethodName+"Has finished Successfully")
        print("***********************************************")

    def  test_isFirstLogin_Student(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        r = requests.get(self.__class__.url_+'api/users/getUserByToken/'+__CONFIG__['TOKENS']['STUDENT'])
        self.assertEquals(r.status_code, 200)
        self.assertTrue(r.json()['isFirstLogin'])
        print("***********************************************")
        print(self._testMethodName+"Has finished Successfully")
        print("***********************************************")

    def test_isFirstLogin_Lecturer(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        r = requests.get(self.__class__.url_+'api/users/getUserByToken/'+__CONFIG__['TOKENS']['LECTURER'])
        self.assertEquals(r.status_code, 200)
        self.assertTrue(r.json()['isFirstLogin'])
        print("***********************************************")
        print(self._testMethodName+"Has finished Successfully")
        print("***********************************************")

    def test_isClassIdListEmpty_Student(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        r = requests.get(self.__class__.url_+'api/users/getUserByToken/'+__CONFIG__['TOKENS']['STUDENT'])
        self.assertEquals(r.status_code, 200)
        #self.assertEquals(r.json()['classes_id_list'],[])
        print("***********************************************")
        print(self._testMethodName+"Has finished Successfully")
        print("***********************************************")

    def test_campuses_id_list_Student(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        r = requests.get(self.__class__.url_+'api/users/getUserByToken/'+__CONFIG__['TOKENS']['STUDENT'])
        self.assertEquals(r.status_code, 200)
        #self.assertEquals(r.json()['campuses_id_list'],[])
        print("***********************************************")
        print(self._testMethodName+"Has finished Successfully")
        print("***********************************************")

    def test_Student_isLecturer(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        r = requests.get(self.__class__.url_+'api/users/getUserByToken/'+__CONFIG__['TOKENS']['STUDENT'])
        self.assertEquals(r.status_code, 200)
        self.assertFalse(r.json()['isLecturer'])
        print("***********************************************")
        print(self._testMethodName+"Has finished Successfully")
        print("***********************************************")

    def test_Lecturer_isLecturer(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        r = requests.get(self.__class__.url_+'api/users/getUserByToken/'+__CONFIG__['TOKENS']['LECTURER'])
        self.assertEquals(r.status_code, 200)
        self.assertTrue(r.json()['isLecturer'])
        print("***********************************************")
        print(self._testMethodName+"Has finished Successfully")
        print("***********************************************")

    def test_isClassIdListEmpty_Lecturer(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        r = requests.get(self.__class__.url_+'api/users/getUserByToken/'+__CONFIG__['TOKENS']['LECTURER'])
        self.assertEquals(r.status_code, 200)
        #self.assertEquals(r.json()['classes_id_list'],[])
        print("***********************************************")
        print(self._testMethodName+"Has finished Successfully")
        print("***********************************************")

    def test_campuses_id_list_Lecturer(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        r = requests.get(self.__class__.url_+'api/users/getUserByToken/'+__CONFIG__['TOKENS']['LECTURER'])
        self.assertEquals(r.status_code, 200)
        print("***********************************************")
        print(self._testMethodName+"Has finished Successfully")
        print("***********************************************")

    #/api/users/updateUser/<string:token>

    def test_updateUser_lecturer(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        url=self.__class__.url_+'api/users/updateUser/'+__CONFIG__['TOKENS']['LECTURER']
        data = {
            'name': 'new name',
            'isLecturer': True,
            'campusName': 'JCE'
        }
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        r = requests.put(url, data=json.dumps(data), headers=headers)
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r._content, '{"message": "User updated"}')
        print("***********************************************")
        print(self._testMethodName+"Has finished Successfully")
        print("***********************************************")

    def test_updateUser_student(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        url=self.__class__.url_+'api/users/updateUser/'+__CONFIG__['TOKENS']['STUDENT']
        data = {
            'name': 'new name',
            'isLecturer': True,
            'campusName': 'JCE'
        }
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        r = requests.put(url, data=json.dumps(data), headers=headers)
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r._content, '{"message": "User updated"}')
        print("***********************************************")
        print(self._testMethodName+"Has finished Successfully")
        print("***********************************************")

    def test_updateUser_INVALID_TOKEN(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        url=self.__class__.url_+'api/users/updateUser/invalidToken'
        data = {
            'name': 'new name',
            'isLecturer': True,
            'campusName': 'JCE'
        }
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        r = requests.put(url, data=json.dumps(data), headers=headers)
        self.assertEquals(r.status_code, 400)
        self.assertEquals(r._content, '{"message": "Not a user!"}')
        print("***********************************************")
        print(self._testMethodName+"Has finished Successfully")
        print("***********************************************")

    def test_updateUser_HEBREW_TOKEN(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        url=self.__class__.url_+'api/users/updateUser/?????'
        data = {
            'name': 'new name',
            'isLecturer': True,
            'campusName': 'JCE'
        }
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        r = requests.put(url, data=json.dumps(data), headers=headers)
        self.assertEquals(r.status_code, 404)
        print("***********************************************")
        print(self._testMethodName+"Has finished Successfully")
        print("***********************************************")

    #/api/users/addUserToCampus/<string:token>
    def test_addUserToCampus_lecturer(self):
        headers = {'content-type': 'application/json'}
        url = self.__class__.url_+'api/users/addUserToCampus/'+__CONFIG__['TOKENS']['LECTURER']
        #params = {'seToken': 'seToken' }
        data = {
            "campusId": 6736157987569664
        }
        #r = requests.post(self.__class__.url_+'api/courses/create/'+__CONFIG__['TOKENS']['STUDENT'],data=payload)
        r = requests.put(url, data=json.dumps(data), headers=headers)
        self.assertEquals(r.status_code, 200)

    def test_addUserToCampus_student(self):
        headers = {'content-type': 'application/json'}
        url = self.__class__.url_+'api/users/addUserToCampus/'+__CONFIG__['TOKENS']['STUDENT']
        #params = {'seToken': 'seToken' }
        data = {
            "campusId": 6736157987569664
        }
        #r = requests.post(self.__class__.url_+'api/courses/create/'+__CONFIG__['TOKENS']['STUDENT'],data=payload)
        r = requests.put(url, data=json.dumps(data), headers=headers)
        self.assertEquals(r.status_code, 404)

    def test_addUserToCampus_invalidToken(self):
        headers = {'content-type': 'application/json'}
        url = self.__class__.url_+'api/users/addUserToCampus/invalidToken'
        #params = {'seToken': 'seToken' }
        data = {
            "campusId": 6736157987569664
        }
        #r = requests.post(self.__class__.url_+'api/courses/create/'+__CONFIG__['TOKENS']['STUDENT'],data=payload)
        r = requests.put(url, data=json.dumps(data), headers=headers)
        self.assertEquals(r.status_code, 404)

    '''
    def test_addUserToCourse_invalidToken(self):
        headers = {'content-type': 'application/json'}
        url = self.__class__.url_+'api/users/addUserToCourse/invalidToken'
        #params = {'seToken': 'seToken' }
        data = {
            "campusId": 5522297150504960
        }
        #r = requests.post(self.__class__.url_+'api/courses/create/'+__CONFIG__['TOKENS']['STUDENT'],data=payload)
        r = requests.put(url, data=json.dumps(data), headers=headers)
        self.assertEquals(r.status_code, 400)

    def test_addUserToCourse_lecturer(self):
        headers = {'content-type': 'application/json'}
        url = self.__class__.url_+'api/users/addUserToCampus/'+__CONFIG__['TOKENS']['LECTURER']
        #params = {'seToken': 'seToken' }
        data = {
            "courseId": 5522297150504960
        }
        #r = requests.post(self.__class__.url_+'api/courses/create/'+__CONFIG__['TOKENS']['STUDENT'],data=payload)
        r = requests.put(url, data=json.dumps(data), headers=headers)
        self.assertEquals(r.status_code, )
'''
    def test_getUserById_student(self):
        #url = self.__class__.url_+'api/users/getUserById/'+__CONFIG__['TOKENS']['STUDENT'] + '/'+__CONFIG__['ID']['STUDENT_ID']
        url = 'http://localhost:8080/api/users/getUserById/_QA_TOKEN_TEST_STUDENT/6225984592281600'
        r = requests.get(url)
        self.assertEquals(r.status_code, 204)

    def test_getUserById_lecturer(self):
        #url = self.__class__.url_+'api/users/getUserById/'+__CONFIG__['TOKENS']['STUDENT'] + '/'+__CONFIG__['ID']['STUDENT_ID']
        url = 'http://localhost:8080/api/users/getUserById/_QA_TOKEN_TEST_LECTURER/6225984592281600'
        r = requests.get(url)
        self.assertEquals(r.status_code, 204)

    def test_getUserById_invalidToken(self):
        #url = self.__class__.url_+'api/users/getUserById/'+__CONFIG__['TOKENS']['STUDENT'] + '/'+__CONFIG__['ID']['STUDENT_ID']
        url = 'http://localhost:8080/api/users/getUserById/invalidToken/InvalidId'
        r = requests.get(url)
        self.assertEquals(r.status_code, 403)

    #/api/users/getUsersByCampus/<string:token>/<string:campusID
    def test_getUserByCampus_student(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        url=self.__class__.url_+'api/users/getUsersByCampus/'+__CONFIG__['TOKENS']['STUDENT']+'/6736157987569664'#campus id
        #url='http://localhost:8080/api/users/getUsersByCampus/_QA_TOKEN_TEST_STUDENT/6736157987569664'
        r = requests.get(url)
        self.assertEquals(r.status_code, 200)
        print("***********************************************")
        print(self._testMethodName+"Has finished Successfully")
        print("***********************************************")

    def test_getUserByCampus_lecturer(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        url=self.__class__.url_+'api/users/getUsersByCampus/'+__CONFIG__['TOKENS']['LECTURER']+'/6736157987569664'#campus id
        #url = 'http://localhost:8080/api/users/getUsersByCampus/_QA_TOKEN_TEST_STUDENT/6736157987569664'
        r = requests.get(url)
        self.assertEquals(r.status_code, 200)
        print("***********************************************")
        print(self._testMethodName+"Has finished Successfully")
        print("***********************************************")

    def test_getUserByCampus_student_invalidCampusId(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        url=self.__class__.url_+'api/users/getUsersByCampus/'+__CONFIG__['TOKENS']['STUDENT']+'/invalidId'#campus id
        r = requests.get(url)
        self.assertEquals(r.status_code, 400)
        print("***********************************************")
        print(self._testMethodName+"Has finished Successfully")
        print("***********************************************")

    def test_getUserByCampus_lecturer_invalidCampusId(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        url=self.__class__.url_+'api/users/getUsersByCampus/'+__CONFIG__['TOKENS']['LECTURER']+'/invalidId'#campus id
        r = requests.get(url)
        self.assertEquals(r.status_code, 400)
        print("***********************************************")
        print(self._testMethodName+"Has finished Successfully")
        print("***********************************************")

    #http://localhost:8080/api/users/getUsersByCampus/_QA_TOKEN_TEST_STUDENT/6736157987569664
    def test_getUserByCampus_invalidToken_validCampusId(self):
        print (datetime.datetime.now().time())
        print("***********************************************")
        print(self._testMethodName+"Has begun")
        print("***********************************************")
        #url=self.__class__.url_+'api/users/getUsersByCampus/invalidToken/6736157987569664'#campus id
        url='http://localhost:8080/api/users/getUsersByCampus/invalidToken/6736157987569664'
        r = requests.get(url)
        self.assertEquals(r.status_code, 400)
        print("***********************************************")
        print(self._testMethodName+"Has finished Successfully")
        print("***********************************************")

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(UserTestPlan)
    unittest.TextTestRunner(verbosity=2).run(suite)
    #unittest.main()