import gevent
import gevent.monkey
import gevent.socket
gevent.monkey.patch_all()

import subprocess
import fcntl
import os
import errno
import sys
import urllib
import distutils.spawn

import gevent.queue
import gevent.event
import ujson

import flask
import flask.ext.login

import chef

import logging

app = flask.Flask('chefdash')

app.config.update(
	DEBUG = True,
	SECRET_KEY = 'dev',
	LOG_FILE = None,
	LOG_FORMAT = '%(asctime)s %(name)s\t%(levelname)s\t%(message)s',
	LOG_LEVEL = logging.INFO,
	ENABLE_BOOTSTRAP = True,
)

BOOTSTRAP_ENV = '__chefdash_bootstrap__'

if distutils.spawn.find_executable('knife'):
	bootstrap_enabled = True
else:
	bootstrap_enabled = False

login_manager = flask.ext.login.LoginManager(app)

api = chef.autoconfigure()

def handler(environ, start_response):
	handled = False
	path = environ['PATH_INFO']
	if path.startswith('/feed/'):
		ws = environ.get('wsgi.websocket')
		if ws:
			handle_websocket(ws, path[6:])
			handled = True
	
	if not handled:
		return app(environ, start_response)

websockets = {}

def handle_websocket(ws, env):
	if not env:
		env = BOOTSTRAP_ENV

	s = websockets.get(env)
	if s is None:
		s = websockets[env] = []
	s.append(ws)

	while True:
		buf = ws.receive()
		if buf is None:
			break

	if ws in s:
		s.remove(ws)

@app.route('/feed/<env>')
@flask.ext.login.login_required
def feed(env = None):
	flask.abort(400)

greenlets = {}

def processes(env = None, node = None, only_executing = True):
	env_greenlets = greenlets.get(env)
	if env_greenlets is None:
		return []
	elif node is None:
		result = []
		for greenlet in env_greenlets.itervalues():
			if not only_executing or not greenlet.ready():
				result.append(greenlet)
		return result
	else:
		greenlet = env_greenlets.get(node)
		if greenlet is None or (only_executing and greenlet.ready()):
			return []
		else:
			return [greenlet,]

def broadcast(env, packet):
	sockets = websockets.get(env)
	if sockets is not None:
		packet = ujson.encode(packet)
		for ws in list(sockets):
			if ws.socket is not None:
				try:
					ws.send(packet)
				except gevent.socket.error:
					if ws in sockets:
						sockets.remove(ws)

@app.route('/converge/<env>', methods = ['POST'])
@app.route('/converge/<env>/<node>', methods = ['POST'])
@flask.ext.login.login_required
def converge(env, node = None):

	if env == BOOTSTRAP_ENV:
		flask.abort(400)

	if len(processes(env, node, only_executing = True)) > 0:
		return ujson.encode({ 'status': 'converging' })

	if node is not None:
		nodes = { node: chef.Node(node, api = api), }
	else:
		nodes = { row.object.name: row.object for row in chef.Search('node', 'chef_environment:' + env, api = api) }
	
	get_command = lambda n: ['ssh', '-o', 'StrictHostKeyChecking=no', n['ipaddress'], 'sudo', 'chef-client']

	return _run(
		nodes,
		get_command,
		env = env,
		progress_status = 'converging',
	)

@app.route('/bootstrap')
@flask.ext.login.login_required
def bootstrap_list():
	if not bootstrap_enabled or not app.config.get('ENABLE_BOOTSTRAP'):
		flask.abort(400)

	nodes = greenlets.get(BOOTSTRAP_ENV, {}).keys()
	status, output, executing = get_env_status(BOOTSTRAP_ENV, nodes, progress_status = 'bootstrapping')
	return flask.render_template(
		'bootstrap.html',
		status = status,
		output = output,
		nodes = nodes,
	)

@app.route('/bootstrap/<ip>', methods = ['POST'])
@flask.ext.login.login_required
def bootstrap(ip):
	if not bootstrap_enabled or not app.config.get('ENABLE_BOOTSTRAP'):
		flask.abort(400)

	if len(processes(BOOTSTRAP_ENV, ip, only_executing = True)) > 0:
		return ujson.encode({ 'status': 'bootstrapping' })

	if len(chef.Search('node', 'ipaddress:%s OR fqdn:%s OR hostname:%s' % (ip, ip, ip), api = api)) > 0:
		broadcast(BOOTSTRAP_ENV, { 'host': ip, 'status': 'ready', 'data': 'A node already exists at this address.\n' })
		return ujson.encode({ 'status': 'ready' })

	get_command = lambda ip: ['knife', 'bootstrap', '--sudo', ip]

	return _run(
		{ ip: ip, },
		get_command,
		env = BOOTSTRAP_ENV,
		progress_status = 'bootstrapping',
	)

def _run(nodes, get_command, env, progress_status):
	# nodes: dictionary of node names mapped to node objects
	# Node objects can be anything. They're just passed to the get_command function

	# get_command: function that takes a node object and returns a command to execute via Popen
	
	# env: name of the environment

	# progress_status: the status to broadcast to the websockets when the command is executing

	env_greenlets = greenlets.get(env)
	if env_greenlets is None:
		greenlets[env] = env_greenlets = { }

	for node in nodes:
		try:
			del env_greenlets[node]
		except KeyError:
			pass

	for hostname in nodes:
		node_object = nodes[hostname]
		p = subprocess.Popen(get_command(node_object), shell = False, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		p.chunks = [] # Chunks of stdout data
		fcntl.fcntl(p.stdout, fcntl.F_SETFL, os.O_NONBLOCK) # make the file nonblocking

		def read(host, process):
			broadcast(env, { 'host': host, 'status': progress_status })

			while True:
				chunk = None
				try:
					chunk = process.stdout.read(4096)
					if not chunk:
						break

				except IOError, e:
					chunk = None
					if e[0] != errno.EAGAIN:
						raise
					sys.exc_clear()

				if chunk:
					process.chunks.append(chunk)
					broadcast(env, { 'host': host, 'data': chunk, })

				gevent.socket.wait_read(process.stdout.fileno())

			process.stdout.close()

			process.wait()

			errors = process.stderr.read()
			process.chunks.append(errors)

			broadcast(env, { 'host': host, 'status': 'ready' if process.returncode == 0 else 'error', 'data': errors })

			if len(processes(env, only_executing = True)) <= 1:
				broadcast(env, { 'status': 'ready' })

			return process.returncode

		greenlet = gevent.spawn(read, host = hostname, process = p)
		greenlet.process = p
		env_greenlets[hostname] = greenlet

	broadcast(env, { 'status': progress_status })

	return ujson.encode({ 'status': progress_status if len(nodes) > 0 else 'ready' })

@app.route('/')
@flask.ext.login.login_required
def index():
	envs = chef.Environment.list(api = api)
	return flask.render_template(
		'index.html',
		envs = envs.itervalues(),
		bootstrap_enabled = bootstrap_enabled and app.config.get('ENABLE_BOOTSTRAP'),
	)

def get_env_status(env, nodes, progress_status):
	status = {}
	output = {}
	executing = False

	env_greenlets = greenlets.get(env)
	if env_greenlets is None:
		env_greenlets = greenlets[env] = { }

	for node in nodes:
		greenlet = env_greenlets.get(node)
		if greenlet is None:
			status[node] = 'ready'
			output[node] = ''
		else:
			s = progress_status
			if greenlet.ready():
				s = 'ready' if greenlet.value == 0 else 'error'
			else:
				executing = True
			status[node] = s
			output[node] = ''.join(greenlet.process.chunks)
	return status, output, executing

@app.route('/env/<env>')
@flask.ext.login.login_required
def env(env):
	if env == BOOTSTRAP_ENV:
		flask.abort(400)
	
	if len(chef.Search('environment', 'name:' + env, api = api)) == 0:
		flask.abort(404)

	nodes = list(chef.Search('node', 'chef_environment:%s' % env, api = api))
	nodes.sort(key = lambda n: n.object.name)

	status, output, converging = get_env_status(env, (n.object.name for n in nodes), progress_status = 'converging')

	return flask.render_template(
		'env.html',
		env = env,
		converging = converging,
		status = status,
		output = output,
		nodes = nodes,
	)

@login_manager.user_loader
class User(object):
	def __init__(self, id):
		self.id = id
	
	def is_authenticated(self):
		return True

	def is_active(self):
		return True

	def is_anonymous(self):
		return False

	def get_id(self):
		return self.id

	#def get_auth_token(self):
		#return flask.ext.login.make_secure_token(self.id)

login_manager.login_view = 'login'

@app.template_filter('urlquote')
def urlquote(url):
	return urllib.quote(url, '')

@app.route('/login', methods = ['GET', 'POST'])
def login():
	request = flask.request
	if flask.ext.login.current_user.is_authenticated():
		return flask.redirect(request.args.get('next') or flask.url_for('index'))

	username = request.form.get('username')
	remember = request.form.get('remember') == 'on'

	if username is not None:

		password = request.form.get('password')

		auth_result = ujson.decode(api.request('POST', '/authenticate_user', data = ujson.encode({ 'name': username, 'password': password })))

		if auth_result.get('name') == username and auth_result.get('verified'):

			flask.ext.login.login_user(User(username), remember = remember)

			return flask.redirect(request.args.get('next') or flask.url_for('index'))

		else:
			return flask.render_template('login.html',
				username = username,
				error = True,
				remember = remember,
				next = request.args.get('next'),
			)

	return flask.render_template('login.html',
		username = None,
		error = False,
		remember = remember,
		next = request.args.get('next'),
	)

@app.route('/logout')
def logout():
	flask.ext.login.logout_user()
	return flask.redirect(flask.url_for('login'))

@app.route('/favicon.ico')
def favicon():
	return flask.send_from_directory(
		os.path.join(app.root_path, 'static'),
		'favicon.ico',
		mimetype = 'image/vnd.microsoft.icon',
	)
