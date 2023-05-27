import os
import sys

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
web_dir  = os.path.join(root_dir, 'demo', 'web')
sys.path.insert(0, root_dir)

import cherrypy
from jinja2 import Environment, FileSystemLoader

from rackspace_monitoring.types import Provider
from rackspace_monitoring.providers import get_driver

env = Environment(loader=FileSystemLoader(os.path.join(web_dir, 'templates')))

def http_methods_allowed(methods=['GET', 'HEAD']):
    method = cherrypy.request.method.upper()
    if method not in methods:
        cherrypy.response.headers['Allow'] = ", ".join(methods)
        raise cherrypy.HTTPError(405)

cherrypy.tools.allow = cherrypy.Tool('on_start_resource', http_methods_allowed)

class Root:
    def _driver(self):
        cookie = cherrypy.request.cookie
        username = None
        apikey = None

        if cookie.has_key('monitoring_username'):
            username = cookie['monitoring_username'].value
        if cookie.has_key('monitoring_apikey'):
            apikey = cookie['monitoring_apikey'].value

        raxMon = get_driver(Provider.RACKSPACE)
        driver = raxMon(username, apikey, ex_force_base_url="https://ele-api.k1k.me/v1.0")
        return driver

    @cherrypy.expose
    def list_entities(self):
        driver = self._driver()
        entities = driver.list_entities()
        print entities
        tmpl = env.get_template('list_entities.html')
        return tmpl.render(entities=entities)

    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST'])
    def setapikey(self, username, apikey):
        cherrypy.response.cookie['monitoring_username'] = username
        cherrypy.response.cookie['monitoring_apikey'] = apikey
        raise cherrypy.HTTPRedirect('/list_entities')

    @cherrypy.expose
    def index(self):
        cookie = cherrypy.request.cookie
        if cookie.has_key('monitoring_username') and cookie.has_key('monitoring_apikey'):
            return self.list_entities()
        else:
            tmpl = env.get_template('index.html')
        return tmpl.render()


cherrypy.tree.mount(Root(), script_name='/')
cherrypy.config.update({'engine.autoreload_on': False})