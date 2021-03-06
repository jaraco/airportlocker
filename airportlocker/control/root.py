import importlib

import os
import pkg_resources
import cherrypy

import airportlocker
from . import urls


base = os.getcwd()

app_conf = {
    'global': {
        'script_name': '/',
    },
    '/': {
        'request.dispatch': urls.api,
    },
    '/_test': {
        'tools.staticdir.on': True,
        'tools.staticdir.root': base,
        'tools.staticdir.dir': 'test/static',
    },
}

def CORS():
    cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
    cherrypy.response.headers['Access-Control-Allow-Headers'] = (
        'x-requested-with, content-type')

def setupapp():
    if airportlocker.config.production:
        cherrypy.config.update({'environment': 'production'})
    else:
        app_conf['/_dev'] = {
            'request.dispatch': urls.dev,
        }

    upload_limit = airportlocker.config.get('upload_limit', 100)
    MB = 2**20
    max_request_body_size = upload_limit * MB

    cherrypy.tools.CORS = cherrypy.Tool('before_handler', CORS)
    cherrypy.config.update({
        'server.socket_port': airportlocker.config.airportlocker_port,
        'server.socket_host': '::0',
        'server.thread_pool': airportlocker.config.threads,
        'server.max_request_body_size': max_request_body_size,
        'log.screen': True,
        'autoreload_on': True,
        'tools.CORS.on': True,
    })

def run():
    start()
    cherrypy.engine.block()

def start():
    setupapp()
    cherrypy.config.update(app_conf)
    cherrypy.tree.mount(None, "", config=app_conf)
    engine = cherrypy.engine
    if hasattr(engine, "signal_handler"):
        engine.signal_handler.subscribe()
    if hasattr(engine, "console_control_handler"):
        engine.console_control_handler.subscribe()
    engine.start()
