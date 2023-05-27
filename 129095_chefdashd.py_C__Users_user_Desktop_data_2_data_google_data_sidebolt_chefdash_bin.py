#!/usr/bin/env python

import chefdash

if __name__ == '__main__':
	import geventwebsocket.handler
	import gevent.pywsgi
	import logging
	import sys

	if len(sys.argv) > 1:
		chefdash.app.config.from_pyfile(sys.argv[1])

	host = '0.0.0.0'
	port = 5000

	server_name = chefdash.app.config.get('SERVER_NAME')
	if server_name is not None and ':' in server_name:
		server_name = server_name.split(':')
		host = server_name[0]
		port = int(server_name[1])
	
	log = 'default'

	if not chefdash.app.debug:
		log = None
		filename = chefdash.app.config['LOG_FILE']
		if filename:
			handler = logging.FileHandler(filename)
			handler.setLevel(chefdash.app.config['LOG_LEVEL'])

			formatter = logging.Formatter(chefdash.app.config['LOG_FORMAT'])
			handler.setFormatter(formatter)

			chefdash.app.logger.setLevel(chefdash.app.config['LOG_LEVEL'])
			chefdash.app.logger.addHandler(handler)
	
	chefdash.app.logger.info('Listening on %s:%d' % (host, port))

	server = gevent.pywsgi.WSGIServer((host, port), chefdash.handler, handler_class = geventwebsocket.handler.WebSocketHandler, log = log)
	server.serve_forever()
