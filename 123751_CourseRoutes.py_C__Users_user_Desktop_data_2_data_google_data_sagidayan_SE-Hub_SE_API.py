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
from models.Course import Course
from models.Campus import Campus
from models.Message import Message

#Validation Utils Libs
from SE_API.Validation_Utils import *
from SE_API.Respones_Utils import *



course_routes = Blueprint("course_routes", __name__)
auto = Autodoc()



#----------------------------------------------------------
#                     POST
#----------------------------------------------------------
@course_routes.route('/api/courses/create/<string:token>', methods=['POST'])
@auto.doc()
def create_course(token):
    """
    <span class="card-title">This call will create a new course in the DB</span>
    <br>
    <b>Route Parameters</b><br>
        - seToken: 'seToken'
    <br>
    <br>
    <b>Payload</b><br>
     - JSON Object, Example: <br>
         {<br>
         'courseName': 'Advance Math',<br>
         'campusId': 1234567890,<br>
         'startDate': {'year': 2015, 'month' : 4, 'day' : 3},<br>
         'endDate': {'year': 2016, 'month' : 5, 'day' : 14}<br>
        }<br>
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
        return bad_request("no data")
    if not is_lecturer(token):  #todo: change to lecturer id
        return forbidden("Invalid token or not a lecturer!")

    user = get_user_by_token(token)

    #try to parse payload
    try:
        payload = json.loads(request.data)
    except Exception as e:
        return bad_request("incorrect JSON format")

    try:
        start_date = datetime.date(payload['startDate']['year'],payload['startDate']['month'],payload['startDate']['day'])
        end_date = datetime.date(payload['endDate']['year'],payload['endDate']['month'],payload['endDate']['day'])

        if end_date <= start_date:
            return bad_request("end date cant be before (or same day) start date")

        course = Course(courseName=payload['courseName'], campusId=payload['campusId'], master_id=user.key().id(),
                        startDate=start_date, endDate=end_date)
        #check if name already exists
        try:
            query = Course.all()
            query.filter('campusId = ', payload['campusId'])
            query.filter("courseName = ", payload['courseName'])
            for c in query.run(limit=1):
                return forbidden("Course with same name already exists")
        except Exception as e:
            print e


    except Exception as e:
        print e
        return bad_request(2)

    #add user to course membersId list
    course.membersId.append(str(user.key().id()))
    db.put(course)

    #add course to user course list
    user.courses_id_list.append(str(course.key().id()))
    db.put(user)

    db.save
    return Response(response=course.to_JSON(),
                                status=201,
                                mimetype="application/json")


#----------------------------------------------------------
#                     PUT
#----------------------------------------------------------

@course_routes.route('/api/courses/joinCourse/<string:token>/<string:courseId>', methods=["PUT"])
@auto.doc()
def joinCourse(token, courseId):
    """
    <span class="card-title">This call will add the user (by token) to a specific course</span>
    <br>
    <b>Route Parameters</b><br>
        - seToken: 'seToken'<br>
        - courseId: 123456789
    <br>
    <br>
    <b>Payload</b><br>
     - None <br>
    <br>
    <b>Response</b>
    <br>
    202 - Accepted
    <br>
    400 - Bad Request
    <br>
    403 - Invalid token or not a lecturer
    """

    user = get_user_by_token(token)
    if user is None:
        return bad_request("Wrong user Token")

    try:
        course = Course.get_by_id(int(courseId))
    except Exception as e:
        return bad_request("Bad id format")

    if course is None:
        return bad_request("No such course")

    if str(user.key().id()) in course.membersId:
        return bad_request("User is already member in Course")

    course.membersId.append(str(user.key().id()))
    user.courses_id_list.append(str(course.key().id()))

    db.put(course)
    db.put(user)
    db.save

    return Response(response=course.to_JSON(),
                        status=202,
                        mimetype="application/json")


#----------------------------------------------------------
#                     GET
#----------------------------------------------------------


@course_routes.route('/api/courses/getAllCoursesByCampus/<string:token>/<string:campusId>', methods=["GET"])
@auto.doc()
def getAllCoursesByCampus(token, campusId):
    """
    <span class="card-title">>This Call will return an array of all courses in a given campus</span>
    <br>
    <b>Route Parameters</b><br>
        - campusId: 1234567890
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
        'courseName': 'Advance Math',<br>
        'campusId': 1234567890,<br>
        'startDate': '2015-14-3'<br>
        'endDate': '2015-29-6'<br>
        'taskFlag': 'False'<br>
        'id' : 1234567890<br>

        }
    </code>
    <br>
    """

    if get_user_by_token(token) is None:
        return bad_request("Bad User Token")

    arr = []
    query = Course.all()

    try:
        query.filter("campusId = ", int(campusId))
    except Exception as e:
        return bad_request("Bad id format")


    for c in query.run():
        arr.append(dict(json.loads(c.to_JSON())))
    print arr
    if len(arr) != 0:
        return Response(response=json.dumps(arr),
                        status=200,
                        mimetype="application/json")
    else:
        return Response(response=[],
                        status=200,
                        mimetype="application/json")

@course_routes.route('/api/courses/getUserCoursesByCampus/<string:token>/<string:campusId>', methods=['GET'])
@auto.doc()
def getUserCoursesByCampus(token, campusId):
    """
    <span class="card-title">This Call will return an array of all Courses of a certain User in a specific Campus</span>
    <br>
    <b>Route Parameters</b><br>
        - seToken: 'seToken'<br>
        - campusId: 1234354543<br>
    <br>
    <br>
    <b>Payload</b><br>
     - NONE <br>
    <br>
    <br>
    <b>Response</b>
    <br>
    200 - JSON Array, Example:<br>
    [<br>
    {
                'title': 'JCE',<br>
                'email_ending': '@post.jce.ac.il',<br>
                'master_user_id': 123453433341, (User that created the campus)<br>
                'avatar_url': 'http://some.domain.com/imagefile.jpg',<br>
                'id' : 1234567890<br>
    },<br>
    ....<br>
    {<br>
    ...<br>
    }req<br>
    ]<br>
    <br>
    403 - Invalid Token<br>
    """

    user = get_user_by_token(token)
    if user is None:
        return bad_request("Bad user Token")

    try:
        campus = Campus.get_by_id(int(campusId))
    except Exception as e:
        return bad_request("Bad id format")

    if campus is None:
        return bad_request("No such Campus")


    arr = []
    for i in user.courses_id_list:
        course = Course.get_by_id(int(i))
        if course.campusId == campus.key().id():
            arr.append(dict(json.loads(course.to_JSON())))

    if len(arr) != 0:
        return Response(response=json.dumps(arr),
                        status=200,
                        mimetype="application/json")
    else:
        return Response(response='[]',
                        status=200,
                        mimetype="application/json")


@course_routes.route('/api/courses/getCoursesByUser/<string:token>/<string:userId>', methods=['GET'])
@auto.doc()
def getCoursesByUser(token, userId):
    """
    <span class="card-title">This Call will return an array of all Courses of a certain User</span>
    <br>
    <b>Route Parameters</b><br>
        - seToken: 'seToken'<br>
        - userId: 1234354543<br>
    <br>
    <br>
    <b>Payload</b><br>
     - NONE <br>
    <br>
    <br>
    <b>Response</b>
    <br>
    200 - JSON Array, Example:<br>
    [<br>
    {
                'title': 'JCE',<br>
                'email_ending': '@post.jce.ac.il',<br>
                'master_user_id': 123453433341, (User that created the campus)<br>
                'avatar_url': 'http://some.domain.com/imagefile.jpg',<br>
                'id' : 1234567890<br>
    },<br>
    ....<br>
    {<br>
    ...<br>
    }req<br>
    ]<br>
    <br>
    403 - Invalid Token<br>
    """

    user = get_user_by_token(token)
    if user is None:
        return bad_request("Bad user Token")

    try:
        otherUser = User.get_by_id(int(userId))
    except Exception as e:
        return bad_request("Bad id format")

    otherUser = User.get_by_id(int(userId))
    if otherUser is None:
        return bad_request("Bad user Id")

    arr = []
    for i in otherUser.courses_id_list:
        print i
        course = Course.get_by_id(int(i))
        arr.append(dict(json.loads(course.to_JSON())))

    if len(arr) != 0:
        return Response(response=json.dumps(arr),
                        status=200,
                        mimetype="application/json")
    else:
        return Response(response='[]',
                        status=200,
                        mimetype="application/json")

@course_routes.route('/api/courses/getCoursesById/<string:token>/<string:courseId>', methods=['GET'])
@auto.doc()
def getCoursesByID(token, courseId):
    """
    <span class="card-title">This Call will return A Course By ID</span>
    <br>
    <b>Route Parameters</b><br>
        - seToken: 'seToken'<br>
        - courseId: 1234354543<br>
    <br>
    <br>
    <b>Payload</b><br>
     - NONE <br>
    <br>
    <br>
    <b>Response</b>
    <br>
    200 - JSON Array, Example:<br>
    { <br>
                'title': 'JCE',<br>
                'email_ending': '@post.jce.ac.il',<br>
                'master_user_id': 123453433341, (User that created the campus)<br>
                'avatar_url': 'http://some.domain.com/imagefile.jpg',<br>
                'id' : 1234567890<br>
    }<br>
    <br>
    403 - Invalid Token<br>
    """

    user = get_user_by_token(token)
    if user is None:
        return bad_request("Bad user Token")

    try:
        course = Course.get_by_id(int(courseId))
    except Exception as e:
        return bad_request("Bad id format")

    if course is None:
        return bad_request("Bad Course Id")

    return Response(response=course.to_JSON(),
                    status=200,
                    mimetype="application/json")



#----------------------------------------------------------
#                     DELETE
#----------------------------------------------------------



@course_routes.route('/api/courses/deleteCourse/<string:token>/<string:courseId>', methods=['DELETE'])
@auto.doc()
def deleteCourse(token, courseId):
    """
    <span class="card-title">This Call will delete a specific Course</span>
    <br>
    <b>Route Parameters</b><br>
        - seToken: 'seToken'<br>
        - courseid: 'courseid'
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

    if not is_lecturer(token):  #todo: change to lecturer id
        return forbidden("Invalid token or not a lecturer!")

    user = get_user_by_token(token)

    try:
        c = Course.get_by_id(int(courseId))
    except Exception as e:
        return bad_request("Bad id format")

    if c is None:
        return bad_request("no such course")


    if c.master_id == user.key().id():
        db.delete(c)
        db.save
        return accepted("course deleted")

    return forbidden("lecturer is not owner of course")


# @course_routes.route('/api/courses/deleteCoursesByCampus/<string:token>/<string:campusid>', methods=['DELETE'])
# @auto.doc()
# def deleteCoursesByCampus(token,campusName):
#     """
#     <span class="card-title">This Call will delete a specific campus's courses</span>
#     <br>
#     <b>Route Parameters</b><br>
#         - seToken: 'seToken'
#         - title: 'campusName'
#     <br>
#     <br>
#     <b>Payload</b><br>
#      - NONE <br>
#     <br>
#     <br>
#     <b>Response</b>
#     <br>
#     202 - Deleted campus
#     <br>
#     204 - No Matching Campus Found
#     <br>
#     ....<br>
#     {<br>
#     ...<br>
#     }req<br>
#
#     ]<br>
#     400 - Bad Request
#     <br>
#     403 - Invalid token or not a lecturer!<br>
#     """
#
#     if not is_lecturer(token):  #todo: change to lecturer id
#         return forbidden("Invalid token or not a lecturer!")
#
#
#     user = get_user_by_token(token)
#     campus = get_campus_by_campusName(campusName)
#     if campus is None:
#         return bad_request("Not a campus!")
#
#     #check user is owner of campus
#     if campus.master_user_id != user.key().id():
#         return forbidden("lecturer is not owner of campus!")
#
#     query = Course.all()
#
#     try:
#         query.filter('campusName =', campusName)
#     except Exception as e:
#         print e
#         return bad_request("invalid course title attribute")
#
#     for c in query.run():
#         db.delete(c)
#         db.save
#
#     return no_content()



#----------------------------------------------------------
#                     DOCUMENTATION
#----------------------------------------------------------

@course_routes.route('/api/courses/help')
def documentation():
    return auto.html()