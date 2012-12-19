import sys
import cgitb

import cherrypy
import fab
from yg.process.erroremail import email_error

import airportlocker


def handle_500(include_ex_message=False):
    tb_info = sys.exc_info()
    cherrypy.log.error(cgitb.text(tb_info))
    cherrypy.response.status = 500
    if airportlocker.config.email_error:
        exc = tb_info[1]
        if hasattr(fab.request, 'error_info') and fab.request.error_info:
            extra_info = fab.request.error_info
        else:
            extra_info = {}
        if 'user' not in extra_info and getattr(fab.session, 'username', None):
            extra_info['user'] = fab.session.username
        if getattr(exc, 'do_not_email', False):
            pass
        else:
            email_error(
                airportlocker.config.email_server,
                airportlocker.config.email_list, 'Airportlocker', tb_info,
                extra_info)
        cherrypy.response.body = ["Error Occurred"]
        if include_ex_message and exc.message:
            cherrypy.response.body.append(': %s' % (exc.message))
    else:
        from fab import cgitb_ext
        cherrypy.response.body = [cgitb_ext.format_tb_for_display(
            appname='Airportlocker')]
