
__author__ = 'sagi'
import json
from GithubAPI.GithubAPI import GitHubAPI_Keys

from google.appengine.ext import db
import requests
import uuid
import datetime

from flask import Flask, request, render_template, redirect, abort, Response

from flask.ext.github import GitHub
from flask.ext.cors import CORS, cross_origin
from flask.ext.autodoc import Autodoc

# DB Models
from models.User import User
from models.Course import Course
from models.Project import Project
from models.Campus import Campus

# All API
from SE_API.Validation_Utils import *
from SE_API.Respones_Utils import *
from SE_API.Email_Utils import *

from SE_API.UserRoutes import user_routes
from SE_API.CampusRoutes import campus_routes
from SE_API.CourseRoutes import course_routes
from SE_API.ProjectRoutes import project_routes
from SE_API.TaskRoutes import task_routes
from SE_API.MessageRoutes import message_routes




app = Flask(__name__, static_folder='../templates')



githubKeys = GitHubAPI_Keys()

app.config['GITHUB_CLIENT_ID'] = githubKeys.getId()
app.config['GITHUB_CLIENT_SECRET'] = githubKeys.getSecret()

github = GitHub(app)
cross = CORS(app)

app.register_blueprint(user_routes)
app.register_blueprint(campus_routes)
app.register_blueprint(course_routes)
app.register_blueprint(project_routes)
app.register_blueprint(task_routes)
app.register_blueprint(message_routes)

auto = Autodoc(app)

@app.route('/')
def wellcomePage():
    return app.send_static_file('index.html')

@app.route('/api/validation/confirm/<string:validation_token>', methods=["GET"])
@auto.doc()
def confirm_user_to_campus(validation_token):
    """
    <span class="card-title">This Function is will Activate a user and add tha campus to it</span>
    <br>
    <b>Route Parameters</b><br>
        - validation_token: 'seToken|email_suffix'
    <br>
    <br>
    <b>Payload</b><br>
     - NONE
    <br>
    <br>
    <b>Response</b>
    <br>
    200 - redirect to home + new cookie
    <br>
    403 - Invalid Token
    """
    #TODO
    token = str(validation_token).split('|')[0]
    email_sufix = '@'+str(validation_token).split('|')[1]

    user = get_user_by_token(token)

    if user is None:
        return forbidden('Forbidden: invalid Token')
    else:
        campus = get_campus_by_suffix(email_sufix)
        if campus is None:
            return bad_request('Bad Request: Email Suffix ' + email_sufix + ' Not Found')
    user.isFirstLogin = False
    user.seToken = str(uuid.uuid4())
    if str(campus.key().id()) not in user.campuses_id_list:
        user.campuses_id_list.append(str(campus.key().id()))
    db.put(user)
    return cookieMonster(user.seToken)



@app.route('/api/validation/sendmail/<string:token>', methods=['POST'])
@auto.doc()
def send_activation(token):
    """
    <span class="card-title">This Method Will Send An Email To The User - To Confirm his Account</span>
    <br>
    <b>Route Parameters</b><br>
        - token: 'seToken'<br>
    <br>
    <b>Payload</b><br>
     - JSON object <i>Example</i>
     <br>
     <code>{email: 'academic@email.ac.com'}</code>
    <br>
    <br>
    <b>Response</b>
    <br>
    200 - Email Sent - No Response<br>
    400 - Bad Request<br>
    403 - Invalid Token<br>
    """
    if not request.data:
        return bad_request()
    payload = json.loads(request.data)
    if not is_user_token_valid(token):
        return forbidden("Not A Valid Token!")

    query = User.all()
    query.filter('seToken =', token)
    for u in query.run(limit=1):
        try:
            send_validation_email(token=token, name=u.username, email=payload["email"])
        except Exception:
            return bad_request()

        return Response(status=200)

@app.route('/api/help')
def documentation_index():
    return app.send_static_file('API_Doc/api_doc_index.html')

@app.route('/api/help/misc')
def documentation_misc():
    return auto.html()

@app.route('/home')
def returnHome():
    try:
        return app.send_static_file('views/index.html')
    except Exception:
        abort(404)





@app.route('/githubOAuth')
@cross_origin('*')
@github.authorized_handler
def oauth(oauth_token):
    if oauth_token is None:
        return render_template("index.html", messages={'error': 'OAuth Fail'})
    try:
        response = requests.get("https://api.github.com/user?access_token=" + oauth_token)
        user_data = json.loads(response.content)
        response = requests.get("https://api.github.com/user/emails?access_token=" + oauth_token)
        userEmails = json.loads(response.content)
    except Exception:
        return "<h1>Max Retries connection To Github</h1><p>github has aborted connection due to to many retries. you need to wait</p>"

    resault = User.all()
    resault.filter("username =", str(user_data["login"]))

    print user_data["login"]

    for u in resault.run():
        print "Exists!!!"
        u.seToken = str(uuid.uuid4())
        u.accessToken = oauth_token
        u.put()
        return cookieMonster(u.seToken)

    tempName = ";"

    if 'email' in user_data:
        if user_data["email"] == "":
            for email in userEmails:
                if email["primary"] and email["verified"]:
                    tempEmail = email["email"]
    else:
        tempEmail = user_data["email"]

    user = User(username=user_data["login"], name=tempName, avatar_url=user_data["avatar_url"], email=tempEmail, isLecturer=False, accessToken=oauth_token, seToken=str(uuid.uuid4()))
    db.put(user)
    db.save
    return cookieMonster(user.seToken)




@app.route('/login')
@cross_origin('*')
def login():
    return github.authorize()

debug = True # Change In Production
if debug:
    import random
    counter = random.randrange(300,400)

    @auto.doc()
    @app.route('/debug/login')
    def set_local_token_view():
        """
        <span class="card-title">Go To This URL To Set The SE-Token Cookie</span>
        <br>
        <b>Route Parameters</b><br>
            - token: None<br>
        <br>
        <b>Payload</b><br>
         - None
        <b>Response</b>
        <br>
        None.
    """
        return app.send_static_file('DEBUG_Views/set_cookie.html')

    @auto.doc()
    @app.route('/debug/createUser/<string:gitHubUserName>')
    def createUser(gitHubUserName):
        """
        <span class="card-title">Go To This URL To Set The SE-Token Cookie</span>
        <br>
        <p>This User Will Automatically be added to JCE Campus as a Lecturer</p>
        <b>Route Parameters</b><br>
            - gitHubUserName: A Username<br>
        <br>
        <b>Payload</b><br>
         - None
        <b>Response</b>
        <br>
        None.
        """
        try:
            query = Campus.all().filter('title =', 'JCE')
            for c in query.run(limit=1):
                campus = c
            user = User(name=";", username=gitHubUserName, isFirstLogin=False,
                        avatar_url='http://placekitten.com/g/200/'+str(counter), accessToken="RandomGitHubToken",
                        email='username@mailservice.com', campuses_id_list=[str(campus.key().id())],
                        seToken=str(uuid.uuid4()), isLecturer=True)
            db.put(user)
            return created(gitHubUserName + 'Was Created. Token: ' + user.seToken)
        except Exception as e:
            return bad_request(str(e))

@app.route('/api/qa/init')
def init_QA():
    is_student_exist = False
    is_lecturer_exist = False
    qa_student = User(username='qa_student', name='Student QA', avatar_url='http://ava.com', email='just@mail.com',
                   isLecturer=False, accessToken='student_token_', seToken='_QA_TOKEN_TEST_STUDENT')
    qa_lecturer = User(username='qa_lecturer', name='Student QA', avatar_url='http://ava.com', email='just@mail.com',
                   isLecturer=True, accessToken='student_token_', seToken='_QA_TOKEN_TEST_LECTURER')
    query = User.all().filter('username =', qa_student.username)
    for u in query.run():
        is_student_exist = True
        u.isLecturer = qa_student.isLecturer
        u.seToken = qa_student.seToken
        u.campuses_id_list = []
        u.classes_id_list = []
        db.put(u)

    query = User.all().filter('username =', qa_lecturer.username)
    for u in query.run():
        is_lecturer_exist = True
        u.isLecturer = qa_lecturer.isLecturer
        u.seToken = qa_lecturer.seToken
        u.campuses_id_list = []
        u.classes_id_list = []
        db.put(u)

    if not is_lecturer_exist:
        db.put(qa_lecturer)
    if not is_student_exist:
        db.put(qa_student)

    return Response(status=200)


def cookieMonster(uid):
    redirect_to_home = redirect('/home')
    response = app.make_response(redirect_to_home )
    response.set_cookie('com.sehub.www',value=uid)
    return response


