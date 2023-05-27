import copy

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
from models.Project import Project
from models.Message import Message

#Validation Utils Libs
from SE_API.Validation_Utils import *
from SE_API.Respones_Utils import *



message_routes = Blueprint("message_routes", __name__)
auto = Autodoc()



#----------------------------------------------------------
#                     POST
#----------------------------------------------------------


@message_routes.route('/api/messages/create/<string:token>', methods=['POST'])
@auto.doc()
def createMessage(token):
    """
    <span class="card-title">This call will create a new Message in the DB</span>
    <br>
    <b>Route Parameters</b><br>
        - seToken: 'seToken'
    <br>
    <br>
    <b>Payload</b><br>
     - JSON Object, Example: <br>
    {<br>
        'groupId' : 123456789,<br>
        'message' : 'Class is canceled',<br>
        'isProject' : true<br>
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
    # if not is_lecturer(token):  #todo: change to lecturer id
    #     return forbidden("Invalid token or not a lecturer!")

    user = get_user_by_token(token)

    #try to parse payload
    try:
        payload = json.loads(request.data)
    except Exception as e:
        return bad_request("here")

    try:
        msg = Message(groupId=payload['groupId'], message=payload['message'], msgDate=datetime.datetime.now(), master_id=user.key().id())
    except Exception as e:
        print e
        return bad_request("there")

    try:
        msg.isProject = payload['isProject']
    except Exception as e:
        pass

    db.put(msg)
    db.save
    return Response(response=msg.to_JSON(),
                            status=200,
                            mimetype="application/json")



#----------------------------------------------------------
#                     PUT
#----------------------------------------------------------


#----------------------------------------------------------
#                     GET
#----------------------------------------------------------

@message_routes.route('/api/messages/getMessagesByGroup/<string:token>/<string:groupId>', methods=["GET"])
@auto.doc()
def getMessagesByGroup(token, groupId):
    """
    <span class="card-title">>This Call will return an array of all messages (sorted by date),<br>
                                for a given group (course or project)</span>
    <br>
    <b>Route Parameters</b><br>
        - SeToken: token <br>
        - groupId: 1234567890
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
            'groupId' : 1234567890,<br>
            'message' : 'hello all',<br>
            'date' : {<br>
                'year': 2015,<br>
                'month': 5,<br>
                'day': 5,<br>
                'hour': 5,<br>
                'minute': 5<br>
            },<br>
            'id' : 1234567890,<br>
            'master_id' : 1234567890,<br>
            'isProject' : false,<br>
            'user': {<br>
        'username': 'DarkLord',<br>
        'name': 'Darth Vader',<br>
        'email': 'darkLord@death.planet,<br>
        'isLecturer': 'True',<br>
        'seToken': 'xxxxxx-xxxxx-xxxxx-xxxxxx',<br>
        'avatar_url': 'http://location.git.com/somthing'<br>
        'isFirstLogin': False,<br>
        'campuses_id_list': [43243532532,5325325325,532532342],<br>
        'courses_id_list': [53523,43432423,432432432432]<br>
        'id': 1234567890 <br>
        },<br>
        'group': {The Group Object Project OR Campus (according to isProject)}<br><br>

        }<br>
    </code>
    <br>
    """
    if get_user_by_token(token) is None:
        return bad_request("No such User")

    arr = []
    query = Message.all()

    try:
        query.filter("groupId =", int(groupId))
    except Exception as e:
        return bad_request("Bad id format")

    for m in query.run():
        msgDic = dict(json.loads(m.to_JSON()))
        #add a key 'forSortDate' for sorting dates
        msgTime = datetime.datetime(msgDic['date']['year'], msgDic['date']['month'], msgDic['date']['day'], msgDic['date']['hour'], msgDic['date']['minute'])
        msgDic['forSortDate'] = msgTime
        arr.append(msgDic)
    print arr
    arr = sorted(arr, key=itemgetter('forSortDate'), reverse=True)
    for i in arr:
        del i['forSortDate']
    print arr

    if len(arr) != 0:
        return Response(response=json.dumps(arr),
                        status=200,
                        mimetype="application/json")
    else:
        return Response(response=[],
                        status=200,
                        mimetype="application/json")

@message_routes.route('/api/messages/getAllUserMessages/<string:token>', methods=["GET"])
@auto.doc()
def getAllUserMessages(token):
    """
    <span class="card-title">>This Call will return an array of all messages (sorted by date),<br>
                                </span>
    <br>
    <b>Route Parameters</b><br>
        - SeToken: token <br>
        - groupId: 1234567890
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
            'groupId' : 1234567890,<br>
            'message' : 'hello all',<br>
            'date' : {<br>
                'year': 2015,<br>
                'month': 5,<br>
                'day': 5,<br>
                'hour': 5,<br>
                'minute': 5<br>
            },<br>
            'id' : 1234567890,<br>
            'master_id' : 1234567890,<br>
            'isProject' : false,<br>
            'user': {<br>
        'username': 'DarkLord',<br>
        'name': 'Darth Vader',<br>
        'email': 'darkLord@death.planet,<br>
        'isLecturer': 'True',<br>
        'seToken': 'xxxxxx-xxxxx-xxxxx-xxxxxx',<br>
        'avatar_url': 'http://location.git.com/somthing'<br>
        'isFirstLogin': False,<br>
        'campuses_id_list': [43243532532,5325325325,532532342],<br>
        'courses_id_list': [53523,43432423,432432432432]<br>
        'id': 1234567890 <br>
        },<br>
        'group': {The Group Object Project OR Campus (according to isProject)}<br><br>

        }<br>
        ]<br>
    </code>
    <br>
    """
    user = get_user_by_token(token)
    if user is None:
        return bad_request("No such User")

    arr = []

    allMsgs = Message.all()
    projectMsgs = copy.deepcopy(allMsgs)

    projectMsgs.filter('isProject =', False)
    for m in projectMsgs.run():
        if str(m.groupId) in user.courses_id_list:
            msgDic = dict(json.loads(m.to_JSON()))
            #add a key 'forSortDate' for sorting dates
            msgTime = datetime.datetime(msgDic['date']['year'], msgDic['date']['month'], msgDic['date']['day'], msgDic['date']['hour'], msgDic['date']['minute'])
            msgDic['forSortDate'] = msgTime
            arr.append(msgDic)


    allMsgs.filter('isProject =', True)
    for m in allMsgs.run():
        if str(m.groupId) in user.projects_id_list:
            msgDic = dict(json.loads(m.to_JSON()))
            #add a key 'forSortDate' for sorting dates
            msgTime = datetime.datetime(msgDic['date']['year'], msgDic['date']['month'], msgDic['date']['day'], msgDic['date']['hour'], msgDic['date']['minute'])
            msgDic['forSortDate'] = msgTime
            arr.append(msgDic)

    arr = sorted(arr, key=itemgetter('forSortDate'), reverse=True)
    for i in arr:
        del i['forSortDate']
    print arr

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

@message_routes.route('/api/messages/deleteMessage/<string:token>/<string:msgId>', methods=["DELETE"])
@auto.doc()
def deleteMessage(token, msgId):
    """
    <span class="card-title">>This Call will delete a message by owner token</span>
    <br>
    <b>Route Parameters</b><br>
        - SeToken: token
        - msgId: 1234567890
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
            'groupId' : 1234567890,<br>
            'message' : 'hello all',<br>
            'date' : {<br>
                'year': 2015,<br>
                'month': 5,<br>
                'day': 5,<br>
                'hour': 5,<br>
                'minute': 5<br>
            },<br>
            'id' : 1234567890,<br>
            'master_id' : 1234567890,<br>
            'isProject' : false<br>
        }<br>
    </code>
    <br>
    """

    user = get_user_by_token(token)
    if user is None:
        return bad_request("No such User")

    try:
        msg = Message.get_by_id(int(msgId))
    except Exception as e:
        return bad_request("Bad id format")


    if msg is None:
        return bad_request("No such Message")

    if msg.master_id != user.key().id():
        return forbidden("User is not the Creator of the message")

    db.delete(msg)
    db.save
    return no_content()





#----------------------------------------------------------
#                     DOCUMENTATION
#----------------------------------------------------------

@message_routes.route('/api/messages/help')
def documentation():
    return auto.html()