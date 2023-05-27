__author__ = 'Aran'

from flask import Blueprint
import json
from GithubAPI.GithubAPI import GitHubAPI_Keys

from google.appengine.ext import db
import requests
import datetime
from operator import itemgetter

from flask import Flask, request, render_template, redirect, abort, Response

from flask.ext.github import GitHub
from flask.ext.cors import CORS, cross_origin
from flask.ext.autodoc import Autodoc

# DB Models
from models.Task import Task
from models.Course import Course
from models.TaskComponent import TaskComponent
from models.TaskGrade import TaskGrade
from models.Project import Project

#Validation Utils Libs
from SE_API.Validation_Utils import *
from SE_API.Respones_Utils import *
from Email_Utils import *


task_routes = Blueprint("task_routes", __name__)
auto = Autodoc()



#----------------------------------------------------------
#                     POST
#----------------------------------------------------------

@task_routes.route('/api/tasks/create/<string:token>', methods=['POST'])
@auto.doc()
def create_task(token):
    """
    <span class="card-title">This call will create a new Task in the DB</span>
    <br>
    <b>Route Parameters</b><br>
        - seToken: 'seToken'
    <br>
    <br>
    <b>Payload</b><br>
     - JSON Object, Example: <br>
    {<br>
        "title":"task1",<br>
        "courseId":1234567890,<br>
        "description":"pls fddfsdfdsk",<br>
        "dueDate":{"year":2010,<br>
                    "month":2,<br>
                    "day":4<br>
                    },
        "isPersonal":true,<br>
        "components":[<br>
                {<br>
                "type" : "should be type1",<br>
                "label" : "should be label1",<br>
                "isMandatory" : true,<br>
                "order" : 1<br>
                },<br>
                {<br>
                "type" : "should be type2",<br>
                "label" : "should be label2",<br>
                "isMandatory" : true,<br>
                "order" : 2<br>
                },<br>
                {<br>
                "type" : "should be type3",<br>
                "label" : "should be label3",<br>
                "isMandatory" : false,<br>
                "order" : 3<br>
                }<br>
        ]<br>
}
    <br>
    <br>
    <b>Response</b>
    <br>
    201 - Created
    <br>
    400 - Bad Request
    <br>
    403 - Invalid token or not a lecturer
    """
    if not request.data:
        return bad_request("no payload")
    payload = json.loads(request.data)
    if not is_lecturer(token):  #todo: change to lecturer id
        return forbidden("Invalid token or not a lecturer!")

    user = get_user_by_token(token)

    #check lecturer is owner of course
    try:
        courseId = payload['courseId']
    except Exception as e:
        print e
        return bad_request("invalid courseId format")

    course = Course.get_by_id(int(courseId))
    if course is None:
        return bad_request("No such Course")

    if course.master_id != user.key().id():
        return forbidden("Lecturer is not owner of Course")

    #parse dueDate
    try:
        date = datetime.date(payload['dueDate']['year'],payload['dueDate']['month'],payload['dueDate']['day'])
    except Exception:
        return bad_request("invalid dueDate format")
    #create Task object
    try:
        task = Task(title=payload['title'], courseId=payload['courseId'], description=payload['description'], dueDate=date)
    except Exception as e:
        print e
        return bad_request("bad")
    try:
        task.isPersonal = payload['isPersonal']
    except Exception:
        pass


    db.put(task)
    db.save

    #create components
    for c in payload['components']:
        try:
            component = TaskComponent(taskId=task.key().id(), userId=-1, type=c['type'], label=c['label'], isMandatory=c['isMandatory'], order=c['order'])
        except Exception as e:
            print e
            return bad_request("Bad component")
        db.put(component)
        db.save

    return Response(response=task.to_JSON(),
                                status=200,
                                mimetype="application/json")

@task_routes.route('/api/tasks/submitTask/<string:token>/<string:taskId>/<string:ownerId>', methods=['POST'])
@auto.doc()
def submitTask(token, taskId, ownerId):
    """
    <span class="card-title">This call will create a new Task in the DB</span>
    <br>
    <b>Route Parameters</b><br>
        - seToken: 'seToken'
    <br>
    <br>
    <b>Payload</b><br>
     - JSON Object, Example: <br>
    {<br>
        "title":"task1",<br>
        "courseId":1234567890,<br>
        "description":"pls fddfsdfdsk",<br>
        "dueDate":{"year":2010,<br>
                    "month":2,<br>
                    "day":4<br>
                    },
        "isPersonal":true,<br>
        "components":[<br>
                {<br>
                "type" : "should be type1",<br>
                "label" : "should be label1",<br>
                "isMandatory" : true,<br>
                "order" : 1<br>
                },<br>
                {<br>
                "type" : "should be type2",<br>
                "label" : "should be label2",<br>
                "isMandatory" : true,<br>
                "order" : 2<br>
                },<br>
                {<br>
                "type" : "should be type3",<br>
                "label" : "should be label3",<br>
                "isMandatory" : false,<br>
                "order" : 3<br>
                }<br>
        ]<br>
}
    <br>
    <br>
    <b>Response</b>
    <br>
    201 - Created
    <br>
    400 - Bad Request
    <br>
    403 - Invalid token or not a lecturer
    """
    if not request.data:
        return bad_request("no payload")
    payload = json.loads(request.data)

    user = get_user_by_token(token)
    if user is None:
        bad_request("bad user Token")

    task = Task.get_by_id(int(taskId))
    if task is None:
        bad_request("bad Task id")

    if task.isPersonal:
        if User.get_by_id(int(ownerId)) is None:
            return bad_request("no such user")
    else:
        if Project.get_by_id(int(ownerId)) is None:
            return bad_request("no such project")


    #create components
    for c in payload:
        try:
            component = TaskComponent(taskId=task.key().id(), userId=(int(ownerId)), type=c['type'], label=c['label'], value=c['value'], isMandatory=c['isMandatory'], order=c['order'])
        except Exception as e:
            print e
            return bad_request("Bad component")
        db.put(component)
        db.save

    return Response(response=task.to_JSON(),
                                status=200,
                                mimetype="application/json")


@task_routes.route('/api/tasks/submitGrade/<string:token>/<string:taskId>/<string:ownerId>/<string:grade>', methods=['POST'])
@auto.doc()
def submitGrade(token, taskId, ownerId, grade):
    """
    <span class="card-title">This call will create a new Task in the DB</span>
    <br>
    <b>Route Parameters</b><br>
        - seToken: 'seToken'
    <br>
    <br>
    <b>Payload</b><br>
     - JSON Object, Example: <br>
    {<br>
        "title":"task1",<br>
        "courseId":1234567890,<br>
        "description":"pls fddfsdfdsk",<br>
        "dueDate":{"year":2010,<br>
                    "month":2,<br>
                    "day":4<br>
                    },
        "isPersonal":true,<br>
        "components":[<br>
                {<br>
                "type" : "should be type1",<br>
                "label" : "should be label1",<br>
                "isMandatory" : true,<br>
                "order" : 1<br>
                },<br>
                {<br>
                "type" : "should be type2",<br>
                "label" : "should be label2",<br>
                "isMandatory" : true,<br>
                "order" : 2<br>
                },<br>
                {<br>
                "type" : "should be type3",<br>
                "label" : "should be label3",<br>
                "isMandatory" : false,<br>
                "order" : 3<br>
                }<br>
        ]<br>
}
    <br>
    <br>
    <b>Response</b>
    <br>
    201 - Created
    <br>
    400 - Bad Request
    <br>
    403 - Invalid token or not a lecturer
    """
    user = get_user_by_token(token)
    if user is None:
        bad_request("bad user Token")

    task = Task.get_by_id(int(taskId))
    if task is None:
        bad_request("bad Task id")


    if task.isPersonal:
        if User.get_by_id(int(ownerId)) is None:
            return bad_request("no such user")
    else:
        if Project.get_by_id(int(ownerId)) is None:
            return bad_request("no such project")

    try:
        tg = TaskGrade.all().filter("taskId = ", int(taskId)).filter("userId = ", int(ownerId))
        if tg.count() == 0:
            grade = TaskGrade(taskId=int(taskId), userId=int(ownerId), grade=int(grade))
            db.put(grade)

        else:
            for g in tg.run():
                g.grade=int(grade)
                g.taskId=int(taskId)
                g.userId=int(ownerId)
                db.put(g)
        db.save
        return accepted()
    except Exception as e:
        print e.message
        return bad_request("wrong format")


#----------------------------------------------------------
#                     PUT
#----------------------------------------------------------

#----------------------------------------------------------
#                     GET
#----------------------------------------------------------


@task_routes.route('/api/tasks/getAllTasksByCourse/<string:token>/<string:courseId>', methods=["GET"])
@auto.doc()
def getAllTasksByCourse(token, courseId):
    """
    <span class="card-title">>This Call will return an array of all Tasks in a course ordered by date</span>
    <br>
    <b>Route Parameters</b><br>
        - SeToken: token<br>
        - courseId: 1234567890
    <br>
    <br>
    <b>Payload</b><br>
     - NONE
    <br>
    <br>
    <b>Response</b>
    <br>
    200 - JSON Example:<br>
    <code>
        {<br>
        'title' : 'Task1',<br>
        'courseId' : 12345678,<br>
        'description' : 'prepare by sunday',<br>
        'dueDate' : {
                    'year' : 2015,
                    'month' : 12,
                    'day' : 23
                    }<br>
        'isPersonal' : true,<br>
        'task_id' : 589689456894<br>
    }<br>
    </code>
    <br>
    """
    if get_user_by_token(token) is None:
        return bad_request("Bad User Token")

    arr = []
    query = Task.all()

    try:
        query.filter("courseId = ", int(courseId))
    except Exception as e:
        return bad_request("Bad id format")

    for t in query.run():
        taskDic =dict(json.loads(t.to_JSON()))
        #add a key 'forSortDate' for sorting dates
        taskTime = datetime.datetime(taskDic['dueDate']['year'], taskDic['dueDate']['month'], taskDic['dueDate']['day'])
        taskDic['forSortDate'] = taskTime
        arr.append(taskDic)

    #sort array by date, and remove added key
    arr = sorted(arr, key=itemgetter('forSortDate'), reverse=False)
    for i in arr:
        del i['forSortDate']

    if len(arr) != 0:
        return Response(response=json.dumps(arr),
                        status=200,
                        mimetype="application/json")
    else:
        return no_content()


@task_routes.route('/api/tasks/getAllFutureCampusTasks/<string:token>/<string:courseId>', methods=["GET"])
@auto.doc()
def getAllFutureCampusTasks(token, courseId):
    """
    <span class="card-title">>This Call will return an array of all Future Tasks in a course, ordered by date</span>
    <br>
    <b>Route Parameters</b><br>
         - SeToken: token<br>
        - courseId: 1234567890
    <br>
    <br>
    <b>Payload</b><br>
     - NONE
    <br>
    <br>
    <b>Response</b>
    <br>
    200 - JSON Example:<br>
    <code>
        {<br>
        'title' : 'Task1',<br>
        'courseName' : 'advance Math',<br>
        'description' : 'prepare by sunday',<br>
        'dueDate' : {
                    'year' : 2015,
                    'month' : 12,
                    'day' : 23
                    }<br>
        'isPersonal' : true,<br>
        'task_id' : 589689456894<br>
    }<br>
    </code>
    <br>
    """

    if get_user_by_token(token) is None:
        return bad_request("Bad User Token")

    arr = []
    query = Task.all()

    try:
        query.filter("courseId = ", int(courseId))
    except Exception as e:
        return bad_request("Bad id format")

    for t in query.run():
        taskDic =dict(json.loads(t.to_JSON()))
        #add a key 'forSortDate' for sorting dates
        taskTime = datetime.date(taskDic['dueDate']['year'], taskDic['dueDate']['month'], taskDic['dueDate']['day'])
        if taskTime >= datetime.date.today():
            taskDic['forSortDate'] = taskTime
            arr.append(taskDic)

    #sort array by date, and remove added key
    arr = sorted(arr, key=itemgetter('forSortDate'), reverse=False)
    for i in arr:
        del i['forSortDate']

    if len(arr) != 0:
        return Response(response=json.dumps(arr),
                        status=200,
                        mimetype="application/json")
    else:
        return no_content()

@task_routes.route('/api/tasks/getAllFutureTasks/<string:token>', methods=["GET"])
@auto.doc()
def getAllFutureTasks(token):
    """
    <span class="card-title">>This Call will return an array of all Future Tasks ordered by date</span>
    <br>
    <b>Route Parameters</b><br>
         - SeToken: token<br>
    <br>
    <br>
    <b>Payload</b><br>
     - NONE
    <br>
    <br>
    <b>Response</b>
    <br>
    200 - JSON Example:<br>
    <code>
        {<br>
        'title' : 'Task1',<br>
        'courseName' : 'advance Math',<br>
        'description' : 'prepare by sunday',<br>
        'dueDate' : {
                    'year' : 2015,
                    'month' : 12,
                    'day' : 23
                    }<br>
        'isPersonal' : true,<br>
        'task_id' : 589689456894<br>
    }<br>
    </code>
    <br>
    """

    user = get_user_by_token(token)
    if user is None:
        return bad_request("Bad User Token")

    arr = []

    for courseId in user.courses_id_list:
        query = Task.all()

        try:
            query.filter("courseId = ", int(courseId))
        except Exception as e:
            return bad_request("Bad id format")

        for t in query.run():
            taskDic =dict(json.loads(t.to_JSON()))
            #add a key 'forSortDate' for sorting dates
            taskTime = datetime.date(taskDic['dueDate']['year'], taskDic['dueDate']['month'], taskDic['dueDate']['day'])
            if taskTime >= datetime.date.today():
                taskDic['forSortDate'] = taskTime
                arr.append(taskDic)

    #sort array by date, and remove added key
    arr = sorted(arr, key=itemgetter('forSortDate'), reverse=False)
    for i in arr:
        del i['forSortDate']

    if len(arr) != 0:
        return Response(response=json.dumps(arr),
                        status=200,
                        mimetype="application/json")
    else:
        return no_content()


@task_routes.route('/api/tasks/getTaskComponents/<string:token>/<string:taskId>', methods=["GET"])
@auto.doc()
def getTaskComponents(token, taskId):
    """
    <span class="card-title">>This Call will return an array of all components for a given task</span>
    <br>
    <b>Route Parameters</b><br>
         - SeToken: token<br>
        - taskId: 1234567890
    <br>
    <br>
    <b>Payload</b><br>
     - NONE
    <br>
    <br>
    <b>Response</b>
    <br>
    200 - JSON Example:<br>
    <code>
    [
        {<br>
            'taskId' : 7589454894,
            'userId' : -1,
            'type' : 'kindOfType',
            'label' : 'kindOfLabel',
            'isMandatory' : true,
            'order' : 2
        }<br>
        {<br>
            'taskId' : 7589454894,
            'userId' : yossi,
            'type' : 'otherKindOfType',
            'label' : 'otherKindOfLabel',
            'isMandatory' : false,
            'order' : 4
        }<br>
    ]
    </code>
    <br>
    """

    if get_user_by_token(token) is None:
        return bad_request("Bad User Token")

    arr = []
    query = TaskComponent.all()

    try:
        query.filter("taskId = ", int(taskId))
    except Exception as e:
        return bad_request("Bad id format")

    for tc in query.run():
        arr.append(dict(json.loads(tc.to_JSON())))

    #sort array by order, and remove added key
    arr = sorted(arr, key=itemgetter('order'), reverse=False)

    if len(arr) != 0:
        return Response(response=json.dumps(arr),
                        status=200,
                        mimetype="application/json")
    else:
        return no_content()

@task_routes.route('/api/tasks/getAllUserTasks/<string:token>', methods=["GET"])
@auto.doc()
def getAllUserTasks(token):
    """
    <span class="card-title">>This Call will return an array of all of the User's Tasks</span>
    <br>
    <b>Route Parameters</b><br>
        - SeToken: token<br>
    <br>
    <br>
    <b>Payload</b><br>
     - NONE
    <br>
    <br>
    <b>Response</b>
    <br>
    200 - JSON Example:<br>
    <code>[<br>
              {<br>
                "courseName": "Advance Math",<br>
                "courseId": 4762397176758272,<br>
                "PersonalTasks": [<br>
                  {<br>
                    "grade": 12,<br>
                    "isPersonal": true,<br>
                    "dueDate": {<br>
                      "year": 2010,<br>
                      "day": 4,<br>
                      "month": 2<br>
                    },<br>
                    "courseId": 4762397176758272,<br>
                    "title": "task1",<br>
                    "description": "pls fddfsdfdsk",<br>
                    "id": 5888297083600896<br>
                  }<br>
                ],<br>
                "projectTasks": []<br>
              },<br>
              {<br>
                "courseName": "Bad Math",<br>
                "courseId": 5659598665023488,<br>
                "PersonalTasks": [<br>
                  {<br>
                    "grade": 12,<br>
                    "isPersonal": true,<br>
                    "dueDate": {<br>
                      "year": 2010,<br>
                      "day": 4,<br>
                      "month": 2<br>
                    },<br>
                    "courseId": 5659598665023488,<br>
                    "title": "new task1",<br>
                    "description": "pls fddfsdfdsk",<br>
                    "id": 5096648711602176<br>
                  },<br>
                  {<br>
                    "grade": 12,<br>
                    "isPersonal": true,<br>
                    "dueDate": {<br>
                      "year": 2010,<br>
                      "day": 4,<br>
                      "month": 2<br>
                    },<br>
                    "courseId": 5659598665023488,<br>
                    "title": "new task4",<br>
                    "description": "pls fddfsdfdsk",<br>
                    "id": 5167017455779840<br>
                  }<br>
                ],<br>
                "projectTasks": [<br>
                  {<br>
                    "grade": 12,<br>
                    "isPersonal": false,<br>
                    "dueDate": {<br>
                      "year": 2010,<br>
                      "day": 4,<br>
                      "month": 2<br>
                    },<br>
                    "courseId": 5659598665023488,<br>
                    "title": "new task3",<br>
                    "description": "pls fddfsdfdsk",<br>
                    "id": 5237386199957504<br>
                  }<br>
                ]<br>
              }<br>
    ]<br>
    </code>
    <br>
    """
    user = get_user_by_token(token)
    if user is None:
        return bad_request("Bad User Token")

    arr = []
    for c in user.courses_id_list:

        dic = {}
        course = Course.get_by_id(int(c))
        dic['courseName'] = course.courseName
        dic['courseId'] = course.key().id()
        dic['master_id'] = course.master_id
        courseTasks = Task.all().filter("courseId = ", course.key().id())
        taskArr = []
        for t in courseTasks.run():
            taskDic =dict(json.loads(t.to_JSON()))
            #add a key 'forSortDate' for sorting dates
            taskTime = datetime.datetime(taskDic['dueDate']['year'], taskDic['dueDate']['month'], taskDic['dueDate']['day'])
            taskDic['forSortDate'] = taskTime



            ownerId = user.key().id()
            if not t.isPersonal:
                project = Project.all().filter("courseId = ", course.key().id())
                for p in project.run():
                    if str(p.key().id()) in user.projects_id_list:
                        ownerId = p.key().id()

            grade = TaskGrade.all().filter("taskId = ", t.key().id()).filter("userId = ", ownerId)
            for g in grade.run():
                taskDic['grade'] = json.loads(g.to_JSON())
            if grade.count() == 0:
                taskDic['grade'] = {'taskId': t.key().id(), 'userId': ownerId, 'grade': None}

            taskDic['submitted'] = {}
            if t.isPersonal:
                total = len(course.membersId)
            else:
                total = Project.all().filter("courseId = ", course.key().id()).count()
            taskDic['submitted']['total'] = total

            basicTC = TaskComponent.all().filter("taskId = ", t.key().id()).filter("userId = ", -1).count()
            allTC = TaskComponent.all().filter("taskId = ", t.key().id()).count()
            if basicTC != 0:
                done = (allTC/basicTC) - 1
            else:
                done = 0
            taskDic['submitted']['done'] = done

            taskArr.append(taskDic)


        taskArr = sorted(taskArr, key=itemgetter('forSortDate'), reverse=False)
        for i in taskArr:
            del i['forSortDate']

        userTaskArr = []
        projectTaskArr = []
        for t in taskArr:
            if t['isPersonal']:
                userTaskArr.append(t)
            else:
                projectTaskArr.append(t)


        dic['PersonalTasks'] = userTaskArr
        dic['projectTasks'] = projectTaskArr
        arr.append(dic)

    #sort array by date, and remove added key


    return Response(response=json.dumps(arr),
                        status=200,
                        mimetype="application/json")

@task_routes.route('/api/tasks/getUsersStateByTask/<string:token>/<string:taskId>', methods=["GET"])
@auto.doc()
def getUsersStateByTask(token, taskId):
    """
    <span class="card-title">>This Call will return an array of all of the User's Tasks</span>
    <br>
    <b>Route Parameters</b><br>
        - SeToken: token<br>
    <br>
    <br>
    <b>Payload</b><br>
     - NONE
    <br>
    <br>
    <b>Response</b>
    <br>
    200 - JSON Example:<br>
    <code>[<br>
              {<br>
                "courseName": "Advance Math",<br>
                "courseId": 4762397176758272,<br>
                "PersonalTasks": [<br>
                  {<br>
                    "grade": 12,<br>
                    "isPersonal": true,<br>
                    "dueDate": {<br>
                      "year": 2010,<br>
                      "day": 4,<br>
                      "month": 2<br>
                    },<br>
                    "courseId": 4762397176758272,<br>
                    "title": "task1",<br>
                    "description": "pls fddfsdfdsk",<br>
                    "id": 5888297083600896<br>
                  }<br>
                ],<br>
                "projectTasks": []<br>
              },<br>
              {<br>
                "courseName": "Bad Math",<br>
                "courseId": 5659598665023488,<br>
                "PersonalTasks": [<br>
                  {<br>
                    "grade": 12,<br>
                    "isPersonal": true,<br>
                    "dueDate": {<br>
                      "year": 2010,<br>
                      "day": 4,<br>
                      "month": 2<br>
                    },<br>
                    "courseId": 5659598665023488,<br>
                    "title": "new task1",<br>
                    "description": "pls fddfsdfdsk",<br>
                    "id": 5096648711602176<br>
                  },<br>
                  {<br>
                    "grade": 12,<br>
                    "isPersonal": true,<br>
                    "dueDate": {<br>
                      "year": 2010,<br>
                      "day": 4,<br>
                      "month": 2<br>
                    },<br>
                    "courseId": 5659598665023488,<br>
                    "title": "new task4",<br>
                    "description": "pls fddfsdfdsk",<br>
                    "id": 5167017455779840<br>
                  }<br>
                ],<br>
                "projectTasks": [<br>
                  {<br>
                    "grade": 12,<br>
                    "isPersonal": false,<br>
                    "dueDate": {<br>
                      "year": 2010,<br>
                      "day": 4,<br>
                      "month": 2<br>
                    },<br>
                    "courseId": 5659598665023488,<br>
                    "title": "new task3",<br>
                    "description": "pls fddfsdfdsk",<br>
                    "id": 5237386199957504<br>
                  }<br>
                ]<br>
              }<br>
    ]<br>
    </code>
    <br>
    """
    user = get_user_by_token(token)
    if user is None:
        return bad_request("Bad User Token")

    task = Task.get_by_id(int(taskId))
    if task is None:
        return bad_request("Bad task id")

    course = Course.get_by_id(task.courseId)

    arr = []
    if task.isPersonal:
        for u in course.membersId:
            user = User.get_by_id(int(u))
            if user.key().id() == course.key().id():
                continue
            userDic = dict(json.loads(user.to_JSON()))
            grade = TaskGrade.all().filter("taskId = ", task.key().id()).filter("userId = ", user.key().id())
            for g in grade.run():
                userDic['grade'] = json.loads(g.to_JSON())
            if grade.count() == 0:
                userDic['grade'] = {'taskId': taskId, 'userId': user.key().id(), 'grade': None}
            arr.append(userDic)

    else:
        projects = Project.all().filter("courseId = ", course.key().id())
        for project in projects.run():
            projDic = dict(json.loads(project.to_JSON()))
            grade = TaskGrade.all().filter("taskId = ", task.key().id()).filter("userId = ", project.key().id())
            for g in grade.run():
                projDic['grade'] = json.loads(g.to_JSON())
            if grade.count() == 0:
                projDic['grade'] = {'taskId': taskId, 'userId': user.key().id(), 'grade': None}
            arr.append(projDic)

    if len(arr) != 0:
            return Response(response=json.dumps(arr),
                            status=200,
                            mimetype="application/json")
    else:
        return Response(response=[],
                        status=200,
                        mimetype="application/json")

@task_routes.route('/api/tasks/isTaskSubmitted/<string:token>/<string:taskId>/<string:groupId>', methods=["GET"])
@auto.doc()
def isTaskSubmitted(token, taskId, groupId):
    """
    <span class="card-title">>This Call will return an array of all of the User's Tasks</span>
    <br>
    <b>Route Parameters</b><br>
        - SeToken: token<br>
    <br>
    <br>
    <b>Payload</b><br>
     - NONE
    <br>
    <br>
    <b>Response</b>
    <br>
    200 - JSON Example:<br>
    <code>[<br>
              {<br>
                "courseName": "Advance Math",<br>
                "courseId": 4762397176758272,<br>
                "PersonalTasks": [<br>
                  {<br>
                    "grade": 12,<br>
                    "isPersonal": true,<br>
                    "dueDate": {<br>
                      "year": 2010,<br>
                      "day": 4,<br>
                      "month": 2<br>
                    },<br>
                    "courseId": 4762397176758272,<br>
                    "title": "task1",<br>
                    "description": "pls fddfsdfdsk",<br>
                    "id": 5888297083600896<br>
                  }<br>
                ],<br>
                "projectTasks": []<br>
              },<br>
              {<br>
                "courseName": "Bad Math",<br>
                "courseId": 5659598665023488,<br>
                "PersonalTasks": [<br>
                  {<br>
                    "grade": 12,<br>
                    "isPersonal": true,<br>
                    "dueDate": {<br>
                      "year": 2010,<br>
                      "day": 4,<br>
                      "month": 2<br>
                    },<br>
                    "courseId": 5659598665023488,<br>
                    "title": "new task1",<br>
                    "description": "pls fddfsdfdsk",<br>
                    "id": 5096648711602176<br>
                  },<br>
                  {<br>
                    "grade": 12,<br>
                    "isPersonal": true,<br>
                    "dueDate": {<br>
                      "year": 2010,<br>
                      "day": 4,<br>
                      "month": 2<br>
                    },<br>
                    "courseId": 5659598665023488,<br>
                    "title": "new task4",<br>
                    "description": "pls fddfsdfdsk",<br>
                    "id": 5167017455779840<br>
                  }<br>
                ],<br>
                "projectTasks": [<br>
                  {<br>
                    "grade": 12,<br>
                    "isPersonal": false,<br>
                    "dueDate": {<br>
                      "year": 2010,<br>
                      "day": 4,<br>
                      "month": 2<br>
                    },<br>
                    "courseId": 5659598665023488,<br>
                    "title": "new task3",<br>
                    "description": "pls fddfsdfdsk",<br>
                    "id": 5237386199957504<br>
                  }<br>
                ]<br>
              }<br>
    ]<br>
    </code>
    <br>
    """
    user = get_user_by_token(token)
    if user is None:
        return bad_request("Bad User Token")

    task = Task.get_by_id(int(taskId))
    if task is None:
        return bad_request("Bad task id")

    res = {}

    grade = TaskGrade.all().filter("taskId = ", task.key().id()).filter("userId = ", int(groupId))
    if grade.count() == 0:
        res['submitted'] = False
    else:
        res['submitted'] = True



    return Response(response=res,
                    status=200,
                    mimetype="application/json")


@task_routes.route('/api/tasks/getAllUnsubmittedTasks/<string:token>', methods=["GET"])
@auto.doc()
def getAllUnsubmittedTasks(token):
    """
    <span class="card-title">>This Call will return an array of all of the User's Tasks</span>
    <br>
    <b>Route Parameters</b><br>
        - SeToken: token<br>
    <br>
    <br>
    <b>Payload</b><br>
     - NONE
    <br>
    <br>
    <b>Response</b>
    <br>
    200 - JSON Example:<br>
    <code>[<br>
              {<br>
                "courseName": "Advance Math",<br>
                "courseId": 4762397176758272,<br>
                "PersonalTasks": [<br>
                  {<br>
                    "grade": 12,<br>
                    "isPersonal": true,<br>
                    "dueDate": {<br>
                      "year": 2010,<br>
                      "day": 4,<br>
                      "month": 2<br>
                    },<br>
                    "courseId": 4762397176758272,<br>
                    "title": "task1",<br>
                    "description": "pls fddfsdfdsk",<br>
                    "id": 5888297083600896<br>
                  }<br>
                ],<br>
                "projectTasks": []<br>
              },<br>
              {<br>
                "courseName": "Bad Math",<br>
                "courseId": 5659598665023488,<br>
                "PersonalTasks": [<br>
                  {<br>
                    "grade": 12,<br>
                    "isPersonal": true,<br>
                    "dueDate": {<br>
                      "year": 2010,<br>
                      "day": 4,<br>
                      "month": 2<br>
                    },<br>
                    "courseId": 5659598665023488,<br>
                    "title": "new task1",<br>
                    "description": "pls fddfsdfdsk",<br>
                    "id": 5096648711602176<br>
                  },<br>
                  {<br>
                    "grade": 12,<br>
                    "isPersonal": true,<br>
                    "dueDate": {<br>
                      "year": 2010,<br>
                      "day": 4,<br>
                      "month": 2<br>
                    },<br>
                    "courseId": 5659598665023488,<br>
                    "title": "new task4",<br>
                    "description": "pls fddfsdfdsk",<br>
                    "id": 5167017455779840<br>
                  }<br>
                ],<br>
                "projectTasks": [<br>
                  {<br>
                    "grade": 12,<br>
                    "isPersonal": false,<br>
                    "dueDate": {<br>
                      "year": 2010,<br>
                      "day": 4,<br>
                      "month": 2<br>
                    },<br>
                    "courseId": 5659598665023488,<br>
                    "title": "new task3",<br>
                    "description": "pls fddfsdfdsk",<br>
                    "id": 5237386199957504<br>
                  }<br>
                ]<br>
              }<br>
    ]<br>
    </code>
    <br>
    """
    user = get_user_by_token(token)
    if user is None:
        return bad_request("Bad User Token")

    arr = []

    courses = Course.all().filter("master_id = ", user.key().id())

    for course in courses.run():
        dic = {}
        dic['courseId'] = course.key().id()
        dic['courseName'] = course.courseName
        dic['tasks'] = []

        tasks = Task.all().filter("courseId = ", course.key().id())
        for task in tasks.run():
            taskDic = {}
            taskDic['title'] = task.title
            taskDic['isPersonal'] = task.isPersonal
            taskDic['usersToReview'] = []
            taskDic['projectsToReview'] = []
            taskDic['id'] = task.key().id()

            tgs = TaskGrade.all().filter("taskId = ", task.key().id())
            tcs = TaskComponent.all().filter("taskId = ", task.key().id()).filter("order = ", 0).filter("userId != ", -1)
            for tg in tgs.run():
                tcs.filter("userId != ", tg.userId)

            for tc in tcs.run():
                if task.isPersonal:
                    u = User.get_by_id(tc.userId)
                    taskDic['usersToReview'].append(json.loads(u.to_JSON()))
                else:
                    p = Project.get_by_id(tc.userId)
                    taskDic['projectsToReview'].append(json.loads(p.to_JSON()))

            dic['tasks'].append(taskDic)

        arr.append(dic)

    return Response(response=json.dumps(arr),
                            status=200,
                            mimetype="application/json")




# @task_routes.route('/api/tasks/getAllUngradedTasks/<string:token>/<string:taskId>/<string:ownerId>', methods=["GET"])
# @auto.doc()
# def getAllUngradedTasks(token, taskId, ownerId):
#     """
#     <span class="card-title">>This Call will return an array of all components for a given task</span>
#     <br>
#     <b>Route Parameters</b><br>
#          - SeToken: token<br>
#         - taskId: 1234567890
#         - ownerId: 123456789
#     <br>
#     <br>
#     <b>Payload</b><br>
#      - NONE
#     <br>
#     <br>
#     <b>Response</b>
#     <br>
#     200 - JSON Example:<br>
#     <code>
#     [
#         {<br>
#             'taskId' : 7589454894,
#             'userId' : -1,
#             'type' : 'kindOfType',
#             'label' : 'kindOfLabel',
#             'isMandatory' : true,
#             'order' : 2
#         }<br>
#         {<br>
#             'taskId' : 7589454894,
#             'userId' : yossi,
#             'type' : 'otherKindOfType',
#             'label' : 'otherKindOfLabel',
#             'isMandatory' : false,
#             'order' : 4
#         }<br>
#     ]
#     </code>
#     <br>
#     """
#     user = get_user_by_token(token)
#     if user is None:
#         return bad_request("Bad User Token")
#     arr = []
#
#     courses = Course.all().filter("master_id = ", user.key().id())
#     if courses.count() == 0:
#         return no_content("user is not lecturer of any course")
#     for course in courses.run():
#         tasks = Task.all().filter("courseId = ", course.key().id())
#         for task in tasks.run():
#
#
#
#
#     task = Task.get_by_id(int(taskId))
#     if task is None:
#         return bad_request("Bad Task id")
#
#     if task.isPersonal:
#         if User.get_by_id(int(ownerId)) is None:
#             return bad_request("no such user")
#     else:
#         if Project.get_by_id(int(ownerId)) is None:
#             return bad_request("no such project")
#
#     task = json.loads(task.to_JSON())
#     task['components'] = []
#     task['grade'] = {}
#
#     taskCompQuery = TaskComponent.all()
#     taskCompQuery.filter("taskId = ", int(taskId))
#
#     taskCompQuery.filter("userId = ", int(ownerId))
#     # if task.isPersonal:
#     #     taskCompQuery.filter("userId = ", user.key().id())
#     # else:
#     #     taskCompQuery.filter("userId = ", user.key().id())#TODO: fix to project
#
#     #check if never created a personalized task and if so, create it
#     if taskCompQuery.count() == 0:
#         taskCompQuery = TaskComponent.all().filter("taskId =", int(taskId)).filter("userId =", -1)
#     print "query count is: ", taskCompQuery.count()
#     for tc in taskCompQuery.run():
#         task['components'].append(dict(json.loads(tc.to_JSON())))
#
#         # for tc in taskCompQuery.run():
#         #     tcNew = TaskComponent(taskId=tc.taskId, userId=user.key().id(), type=tc.type, label=tc.label, isMandatory=tc.isMandatory, order=tc.order)
#         #     db.put(tcNew)
#
#         # grade = TaskGrade(grade=0, taskId=task.key().id(), userId=user.key().id())
#         # db.put(grade)
#     grade = TaskGrade.all().filter("taskId = ", int(taskId)).filter("userId = ", int(ownerId))
#     gradeFound = False
#     for g in grade.run():
#         task['grade'] = json.loads(g.to_JSON())
#         gradeFound = True
#     if not gradeFound:
#         task['grade'] = {'taskId': taskId, 'userId': ownerId, 'grade': None}
#
#
#     return Response(response=json.dumps(task),
#                         status=200,
#                         mimetype="application/json")


@task_routes.route('/api/tasks/getTaskById/<string:token>/<string:taskId>/<string:ownerId>', methods=["GET"])
@auto.doc()
def getTaskById(token, taskId, ownerId):
    """
    <span class="card-title">>This Call will return an array of all components for a given task</span>
    <br>
    <b>Route Parameters</b><br>
         - SeToken: token<br>
        - taskId: 1234567890
        - ownerId: 123456789
    <br>
    <br>
    <b>Payload</b><br>
     - NONE
    <br>
    <br>
    <b>Response</b>
    <br>
    200 - JSON Example:<br>
    <code>
    [
        {<br>
            'taskId' : 7589454894,
            'userId' : -1,
            'type' : 'kindOfType',
            'label' : 'kindOfLabel',
            'isMandatory' : true,
            'order' : 2
        }<br>
        {<br>
            'taskId' : 7589454894,
            'userId' : yossi,
            'type' : 'otherKindOfType',
            'label' : 'otherKindOfLabel',
            'isMandatory' : false,
            'order' : 4
        }<br>
    ]
    </code>
    <br>
    """
    user = get_user_by_token(token)
    if user is None:
        return bad_request("Bad User Token")

    task = Task.get_by_id(int(taskId))
    if task is None:
        return bad_request("Bad Task id")
    if task.isPersonal:
        if User.get_by_id(int(ownerId)) is None:
            return bad_request("no such user")
    else:
        if Project.get_by_id(int(ownerId)) is None:
            return bad_request("no such project")

    task = json.loads(task.to_JSON())
    task['components'] = []
    task['grade'] = {}

    taskCompQuery = TaskComponent.all()
    taskCompQuery.filter("taskId = ", int(taskId))

    taskCompQuery.filter("userId = ", int(ownerId))
    # if task.isPersonal:
    #     taskCompQuery.filter("userId = ", user.key().id())
    # else:
    #     taskCompQuery.filter("userId = ", user.key().id())#TODO: fix to project

    #check if never created a personalized task and if so, create it
    if taskCompQuery.count() == 0:
        taskCompQuery = TaskComponent.all().filter("taskId =", int(taskId)).filter("userId =", -1)
    print "query count is: ", taskCompQuery.count()
    for tc in taskCompQuery.run():
        task['components'].append(dict(json.loads(tc.to_JSON())))

        # for tc in taskCompQuery.run():
        #     tcNew = TaskComponent(taskId=tc.taskId, userId=user.key().id(), type=tc.type, label=tc.label, isMandatory=tc.isMandatory, order=tc.order)
        #     db.put(tcNew)

        # grade = TaskGrade(grade=0, taskId=task.key().id(), userId=user.key().id())
        # db.put(grade)
    grade = TaskGrade.all().filter("taskId = ", int(taskId)).filter("userId = ", int(ownerId))
    gradeFound = False
    for g in grade.run():
        task['grade'] = json.loads(g.to_JSON())
        gradeFound = True
    if not gradeFound:
        task['grade'] = {'taskId': taskId, 'userId': ownerId, 'grade': None}


    return Response(response=json.dumps(task),
                        status=200,
                        mimetype="application/json")



#----------------------------------------------------------
#                     DELETE
#----------------------------------------------------------



@task_routes.route('/api/tasks/deleteTask/<string:token>/<string:taskId>', methods=['DELETE'])
@auto.doc()
def deleteTask(token, taskId):
    """
    <span class="card-title">This Call will delete a specific Task</span>
    <br>
    <b>Route Parameters</b><br>
        - seToken: 'seToken'
        - taskId: 'taskid'
    <br>
    <br>
    <b>Payload</b><br>
     - NONE <br>
    <br>
    <br>
    <b>Response</b>
    <br>
    202 - Deleted Course
    <br>
    ....<br>
    {<br>
    ...<br>
    }req<br>

    ]<br>
    400 - no such Course
    <br>
    403 - Invalid token or not a lecturer or lecturer is not owner of Course!<br>
    """

    if not is_lecturer(token):
        return forbidden("Invalid token or not a lecturer!")

    #todo: check if lecturer is owner of course
    #return forbidden("lecturer is not owner of course")

    user = get_user_by_token(token)

    try:
        c = Task.get_by_id(int(taskId))
    except Exception as e:
        return bad_request("Bad id format")

    if c is None:
        return bad_request("no such Task")


    db.delete(c)
    db.save
    return accepted("Task deleted")


@task_routes.route('/api/tasks/deleteTaskComponents/<string:token>/<string:taskId>', methods=['DELETE'])
@auto.doc()
def deleteTaskComponents(token,taskId):
    """
    <span class="card-title">This Call will delete a specific Task's components</span>
    <br>
    <b>Route Parameters</b><br>
        - seToken: 'seToken'
        - taskId: 'taskid'
    <br>
    <br>
    <b>Payload</b><br>
     - NONE <br>
    <br>
    <br>
    <b>Response</b>
    <br>
    202 - Deleted Course
    <br>
    ....<br>
    {<br>
    ...<br>
    }req<br>

    ]<br>
    400 - no such Task
    <br>
    403 - Invalid token or not a lecturer or lecturer is not owner of Task!<br>
    """

    if not is_lecturer(token):
        return forbidden("Invalid token or not a lecturer!")

    #todo: check if lecturer is owner of course
    #return forbidden("lecturer is not owner of course")

    user = get_user_by_token(token)


    try:
        t = Task.get_by_id(int(taskId))
    except Exception as e:
        return bad_request("Bad id format")

    if t is None:
        return bad_request("no such Task")

    query = TaskComponent.all()
    query.filter('taskId = ', t.key().id())

    for tc in query.run():
        db.delete(tc)

    db.save
    return accepted("Task deleted")




#----------------------------------------------------------
#                     DOCUMENTATION
#----------------------------------------------------------

@task_routes.route('/api/tasks/help')
def documentation():
    return auto.html()


@task_routes.route('/api/tasks/sendTaskReminder', methods=['GET'])
def sendTaskReminder():

    tasks = Task.all()

    try:
        for t in tasks.run():
            if t.dueDate == datetime.date.today() + datetime.timedelta(days=1):
                course = Course.get_by_id(int(t.courseId))
                if t.isPersonal:
                    for uId in course.membersId:
                        if int(uId) != course.master_id:
                            tc = TaskComponent.all().filter("taskId = ", t.key().id()).filter("userId = ", int(uId))
                            if tc.count() == 0:
                                user = User.get_by_id(int(uId))
                                send_task_reminder(user.email, user.name, t.title, course.courseName)
                                print ""

                else:
                    projects = Project.all().filter("courseId = ", course.key().id())
                    for p in projects.run():
                        tc = TaskComponent.all().filter("taskId = ", t.key().id()).filter("userId = ", p.key().id())
                        if tc.count() == 0:
                            for uId in p.membersId:
                                user = User.get_by_id(int(uId))
                                send_task_reminder(user.email, user.name, t.title, course.courseName)
        return accepted()

    except:
        return bad_request()









# @task_routes.route('/api/tasks/getClosestTask/<string:courseName>', methods=["GET"])
# @auto.doc()
# def getClosestTask(courseName):
#     """
#     <span class="card-title">>This Call will return an array of all projects in a given course</span>
#     <br>
#     <b>Route Parameters</b><br>
#         - name: 'course name'
#     <br>
#     <br>
#     <b>Payload</b><br>
#      - NONE
#     <br>
#     <br>
#     <b>Response</b>
#     <br>
#     200 - JSON Example:<br>
#     <code>
#         {<br>
#         'projectName': 'Advance Math',<br>
#         'courseName': 'JCE',<br>
#         'grade': 98,<br>
#         'logo_url': 'http://location.domain.com/image.jpg',<br>
#         'gitRepository': 'http://location.git.com/somthing',<br>
#         'membersId': ['bob', 'dylan', 'quentin', 'terentino']<br>
#         }
#     </code>
#     <br>
#     """
#     #get all tasks for a specific course
#     arr = []
#     query = Task.all()
#     query.filter("courseName =", courseName)
#     for t in query.run():
#         count+=1
#         if t.dueDate < closestDate:
#             closestDate = t.dueDate
#             index = count
#         arr.append(dict(json.loads(t.to_JSON())))
#
#     print arr
#     if len(arr) != 0:
#         return Response(response=json.dumps(arr[index]),
#                         status=200,
#                         mimetype="application/json")
#     else:
#         return no_content("no Tasks")
#
