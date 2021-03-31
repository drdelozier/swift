# SWIFT Taskbook
# Web Application for Task Management

# system libraries
import os

# web transaction objects
from bottle import request, response

# HTML request types
from bottle import route, get, put, post, delete

# web page template processor
from bottle import template

# database library & support
import dataset
from random import seed, randint
import time

import passwords

VERSION=0.1

# development server
PYTHONANYWHERE = ("PYTHONANYWHERE_SITE" in os.environ)

if PYTHONANYWHERE:
    from bottle import default_app
else:
    from bottle import run

# ---------------------------
# user management
# ---------------------------
user_db = dataset.connect('sqlite:///user.db')
seed()


# ---------------------------
# session management
# ---------------------------
session_db = dataset.connect('sqlite:///session.db')

# ---------------------------
# web application routes
# ---------------------------

@route('/')
@route('/tasks')
def tasks():
    session_id = request.cookies.get('session_id',None)
    print([session_id])
    print("session_id in request = ",session_id)
    if session_id == "None":
        session_id = None
    if session_id :
        session_id = int(session_id)
    else:
        session_id = randint(10000000, 20000000)
    # try to load session information
    session_table = session_db.create_table('session')
    sessions = list(session_table.find(session_id=session_id))
    if len(sessions) == 0:
        # we need to create a session
        session = {
                    "session_id":session_id,
                    "started_at":time.time(),
                    "username" : None
                  } 
        # put the session in the database
        session_table.insert(session)
    else:
        session = sessions[0]
    print(session)
    if "username" not in session: 
        return template("login_failure.tpl",user="not logged in", password="n/a")
    if session["username"] == None:
        return template("login_failure.tpl",user="not logged in", password="n/a")

    # persist the session
    session_table.update(row=session, keys=['session_id'])

    assert session_id
    assert int(session_id) 
    print("session_id sent in response = ",str(session_id))
    save_session(response, session)
    response.set_cookie('session_id',str(session_id))    # <host/url> <name> <value>
    return template("tasks.tpl")

@route('/session')
def session():
    session_id = request.cookies.get('session_id',None)
    print("session_id in request = ",session_id)
    if session_id and session_id != "None":
        session_id = int(session_id)
        session_table = session_db.create_table('session')
        sessions = list(session_table.find(session_id=session_id))
        if len(list(sessions)) > 0:
            session = sessions[0]
        else:
            session = {}
    else:
        session = {}
    return template("session.tpl",session_str=session)

def hash(x):
    sum = 0
    for c in x:
        sum = sum + ord(c)
    return sum

@route('/register/<user>/<password>')
def register(user, password):
    print("registering",user,password)
    session_id = request.cookies.get('session_id',None)
    print("session_id in request = ",session_id)
    assert session_id != "None", "Darn it, string None in cookie again!"
    session_table = session_db.create_table('session')
    if session_id:
        session_id = int(session_id)
        sessions = list(session_table.find(session_id=session_id))
        if len(list(sessions)) > 0:
            session = sessions[0]
        else:
            session = {}
    else:
        session_id = randint(10000000, 20000000)
        session = {                   
                    "session_id":session_id,
                    "started_at":time.time(),
                    "username" : None
                    }

    user_table = user_db.create_table('user')
    user_profile = {
                "username":user,
                "password":passwords.encode_password(password),
            } 
    user_table.insert(user_profile)

    session["username"] = user
    session_table.update(row=session, keys=['session_id'])

    response.set_cookie('session_id',str(session_id))  
    return template("register.tpl",user=user, password=password)

@route('/login/<user>/<password>')
def login(user, password):
    username = user
    print(username)
    user_table = user_db.create_table('user')
    users = list(user_table.find(username=user))
    if len(list(users)) > 0:
        user_profile = list(users)[0]
        print(user_profile)
        if (not passwords.verify_password(password,user_profile["password"])):            
            return template("login_failure.tpl",user=user, password="****")
    else:
        return template("login_failure.tpl",user=user, password="****")
    session_id = request.cookies.get('session_id',None)
    if session_id == "None":
        session_id = None
    print("session_id in request = ",[session_id])
    if session_id:
        print("getting session from cookie")
        session_id = int(session_id)
    else:
        print("getting new session from randint")
        session_id = randint(10000000, 20000000)
    print("Login", session_id)
    # try to load session information
    session_table = session_db.create_table('session')
    sessions = list(session_table.find(session_id=session_id))
    if len(sessions) == 0:
        # we need to create a session
        session = {
                    "session_id":session_id,
                    "started_at":time.time()
                  } 
        # put the session in the database
        session_table.insert(session)
    else:
        session = sessions[0]
    # update the session
    session['username'] = username
    print(session)
    # persist the session
    session_table.update(row=session, keys=['session_id'])
    print("persisting cookie as ",[session_id])
    response.set_cookie('session_id',str(session_id))    # <host/url> <name> <value>
    return template("login.tpl",user=user, password=password)

# @route('/register')
# def login():
#     return template("register.tpl")

# ---------------------------
# task REST api
# ---------------------------

import json
import dataset
import time

taskbook_db = dataset.connect('sqlite:///taskbook.db')

@get('/api/version')
def get_version():
    return { "version":VERSION }

@get('/api/tasks')
def get_tasks():
    'return a list of tasks sorted by submit/modify time'
    response.headers['Content-Type'] = 'application/json'
    response.headers['Cache-Control'] = 'no-cache'
    task_table = taskbook_db.get_table('task')
    tasks = [dict(x) for x in task_table.find(order_by='time')]
    return { "tasks": tasks }

@post('/api/tasks')
def create_task():
    'create a new task in the database'
    try:
        data = request.json
        for key in data.keys():
            assert key in ["description","list"], f"Illegal key '{key}'"
        assert type(data['description']) is str, "Description is not a string."
        assert len(data['description'].strip()) > 0, "Description is length zero."
        assert data['list'] in ["today","tomorrow"], "List must be 'today' or 'tomorrow'"
    except Exception as e:
        response.status="400 Bad Request:"+str(e)
        return
    try:
        task_table = taskbook_db.get_table('task')
        task_table.insert({
            "time": time.time(),
            "description":data['description'].strip(),
            "list":data['list'],
            "completed":False
        })
    except Exception as e:
        response.status="409 Bad Request:"+str(e)
    # return 200 Success
    response.headers['Content-Type'] = 'application/json'
    return json.dumps({'status':200, 'success': True})

@put('/api/tasks')
def update_task():
    'update properties of an existing task in the database'
    try:
        data = request.json
        for key in data.keys():
            assert key in ["id","description","completed","list"], f"Illegal key '{key}'"
        assert type(data['id']) is int, f"id '{id}' is not int"
        if "description" in request:
            assert type(data['description']) is str, "Description is not a string."
            assert len(data['description'].strip()) > 0, "Description is length zero."
        if "completed" in request:
            assert type(data['completed']) is bool, "Completed is not a bool."
        if "list" in request:
            assert data['list'] in ["today","tomorrow"], "List must be 'today' or 'tomorrow'"
    except Exception as e:
        response.status="400 Bad Request:"+str(e)
        return
    if 'list' in data:
        data['time'] = time.time()
    try:
        task_table = taskbook_db.get_table('task')
        task_table.update(row=data, keys=['id'])
    except Exception as e:
        response.status="409 Bad Request:"+str(e)
        return
    # return 200 Success
    response.headers['Content-Type'] = 'application/json'
    return json.dumps({'status':200, 'success': True})

@delete('/api/tasks')
def delete_task():
    'delete an existing task in the database'
    try:
        data = request.json
        assert type(data['id']) is int, f"id '{id}' is not int"
    except Exception as e:
        response.status="400 Bad Request:"+str(e)
        return
    try:
        task_table = taskbook_db.get_table('task')
        task_table.delete(id=data['id'])
    except Exception as e:
        response.status="409 Bad Request:"+str(e)
        return
    # return 200 Success
    response.headers['Content-Type'] = 'application/json'
    return json.dumps({'success': True})

if PYTHONANYWHERE:
    application = default_app()
else:
   if __name__ == "__main__":
       run(host='0.0.0.0', port=8080, debug=True)


