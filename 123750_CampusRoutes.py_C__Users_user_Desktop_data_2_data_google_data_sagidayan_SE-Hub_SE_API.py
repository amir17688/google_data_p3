__author__ = 'Aran'

from flask import Blueprint
import json
from GithubAPI.GithubAPI import GitHubAPI_Keys

from google.appengine.ext import db
import requests
import datetime

from flask import Flask, request, render_template, redirect, abort, Response

from flask.ext.github import GitHub
from flask.ext.cors import CORS, cross_origin
from flask.ext.autodoc import Autodoc

# DB Models
from models.Campus import Campus

#Validation Utils Libs
from SE_API.Validation_Utils import *
from SE_API.Respones_Utils import *
from SE_API.Email_Utils import *

campus_routes = Blueprint("campus_routes", __name__)
auto = Autodoc()


#----------------------------------------------------------
#                     POST
#----------------------------------------------------------

@campus_routes.route('/api/campuses/create/<string:token>', methods=['POST'])
@auto.doc()
def create_campus(token):
    """
    <span class="card-title">This call will create a new campus in the DB</span>
    <br>
    <b>Route Parameters</b><br>
        - seToken: 'seToken'
    <br>
    <br>
    <b>Payload</b><br>
     - JSON Object, Example: <br>
     {<br>
     'title': 'Campus name',<br>
     'email_ending': '@campus.ac.com',<br>
     'avatar_url': 'http://location.domain.com/image.jpg'<br>
    }<br>
    <br>
    <br>
    <b>Response</b>
    <br>
    200 - OK
    <br>
    403 - Invalid Token/Forbidden
    """
    if not request.data:
        return bad_request()
    if not is_lecturer(token):  #todo: change to lecturer id
        return forbidden("Invalid token or not a lecturer!")

    #try to parse payload
    try:
        payload = json.loads(request.data)
    except Exception as e:
        return bad_request(e)

    #check if name already exists
    try:
        query = Campus.all()
        query.filter("title =", payload['title'])
        for c in query.run(limit=1):
            return forbidden("Campus with same name already exists")
    except Exception as e:
        print e

    user = get_user_by_token(token)
    arr = []
    arr.append(str(user.key().id()))
    try:
        campus = Campus(title=payload['title'], email_ending=payload['email_ending'], master_user_id=user.key().id(), avatar_url=payload['avatar_url'], membersId=arr)
    except Exception:
        return bad_request()

    send_create_campus_request(user.email, user.name, campus.title)
    db.put(campus)
    notify_se_hub_campus_request(campus, campus.title)
    db.delete(campus)
    return ok()



#----------------------------------------------------------
#                     PUT
#----------------------------------------------------------

@campus_routes.route('/api/campuses/joinCampus/<string:token>/<string:campusId>', methods=["PUT"])
@auto.doc()
def joinCampus(token, campusId):
    """
    <span class="card-title">This call will add the user (by token) to a specific campus</span>
    <br>
    <b>Route Parameters</b><br>
        - seToken: 'seToken'<br>
        - campusId: 123456789
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

    if not is_lecturer(token):
        return forbidden("Invalid token or not a lecturer!")

    user = get_user_by_token(token)

    try:
        campus = Campus.get_by_id(int(campusId))
    except Exception as e:
        return bad_request("Bad id format")


    if campus is None:
        return bad_request("No such course")

    if str(user.key().id()) in campus.membersId:
        return bad_request("User is already member in Project")

    campus.membersId.append(str(user.key().id()))
    user.courses_id_list.append(str(campus.key().id()))

    db.put(campus)
    db.put(user)
    db.save

    return Response(response=campus.to_JSON(),
                        status=202,
                        mimetype="application/json")



#----------------------------------------------------------
#                     GET
#----------------------------------------------------------

@campus_routes.route('/api/campuses/getAll/<string:token>', methods=['GET'])
@auto.doc()
def get_campuses(token):
    """
    <span class="card-title">This Call will return an array of all Campuses available</span>
    <br>
    <b>Route Parameters</b><br>
        - seToken: 'seToken'
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
    if is_user_token_valid(token):
        arr = []
        query = Campus.all()
        for c in query.run():
            arr.append(dict(json.loads(c.to_JSON())))
        print "ARR:"
        print arr
        for c in arr:
            print"c:"
            print c
        if len(arr) != 0:
            return Response(response=json.dumps(arr),
                            status=200,
                            mimetype="application/json")
        else:
            return Response(response=[],
                            status=200,
                            mimetype="application/json")
    else:
        return forbidden("Invalid Token")


@campus_routes.route('/api/campuses/getCampusesByUser/<string:token>', methods=['GET'])
@auto.doc()
def getCampusesByUser(token):
    """
    <span class="card-title">This Call will return an array of all Campuses of a certain User</span>
    <br>
    <b>Route Parameters</b><br>
        - seToken: 'seToken'
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

    arr = []
    for i in user.campuses_id_list:
        campus = Campus.get_by_id(int(i))
        arr.append(dict(json.loads(campus.to_JSON())))

    if len(arr) != 0:
        return Response(response=json.dumps(arr),
                        status=200,
                        mimetype="application/json")
    else:
        return Response(response=[],
                        status=200,
                        mimetype="application/json")

@campus_routes.route('/api/campuses/getCampusesByUserID/', defaults={'token': None, 'id': None})
@campus_routes.route('/api/campuses/getCampusesByUserID/<string:token>/<string:id>', methods=['GET'])
@auto.doc()
def getCampusesByUserID(token, id):
    """
    <span class="card-title">This Call will return an array of all Campuses of a certain User By ID</span>
    <br>
    <b>Route Parameters</b><br>
        - token: 'seToken' of requesting user
        - The ID of <b>Wanted</b> User Campuses
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
        return forbidden("Invalid Token")


    try:
        user = get_user_by_id(int(id))
    except Exception as e:
        return bad_request("Bad id format")

    if user is None:
        return no_content("No User")

    arr = []
    for i in user.campuses_id_list:
        campus = Campus.get_by_id(int(i))
        arr.append(dict(json.loads(campus.to_JSON())))

    if len(arr) != 0:
        return Response(response=json.dumps(arr),
                        status=200,
                        mimetype="application/json")
    else:
        return Response(response=[],
                        status=200,
                        mimetype="application/json")

#----------------------------------------------------------
#                     DELETE
#----------------------------------------------------------


@campus_routes.route('/api/campuses/deleteCampus/<string:token>/<string:campusId>', methods=['DELETE'])
@auto.doc()
def deleteCampus(token,campusId):
    """
    <span class="card-title">This Call will delete a specific campus</span>
    <br>
    <b>Route Parameters</b><br>
        - seToken: 'seToken'
        - campusId: 1234567890
    <br>
    <br>
    <b>Payload</b><br>
     - NONE <br>
    <br>
    <br>
    <b>Response</b>
    <br>
    202 - Deleted campus
    <br>
    ....<br>
    {<br>
    ...<br>
    }req<br>

    ]<br>
    400 - no such campus
    <br>
    403 - Invalid token or not a lecturer or lecturer is not owner of campus!<br>
    """

    if not is_lecturer(token):  #todo: change to lecturer id
        return forbidden("Invalid token or not a lecturer!")

    user = get_user_by_token(token)

    try:
        camp = Campus.get_by_id(int(campusId))
    except Exception as e:
        return bad_request("Bad id format")

    if camp is None:
        return bad_request("no such campus")


    if camp.master_user_id == user.key().id():
        db.delete(camp)
        db.save
        return accepted("campus deleted")

    return forbidden("lecturer is not owner of campus")



#----------------------------------------------------------
#                     DOCUMENTATION
#----------------------------------------------------------

@campus_routes.route('/api/campuses/help')
def documentation():
    return auto.html()
