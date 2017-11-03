import flask
import logging
import os
import pkg_resources


class config(object):
    DEBUG = False


def create_app(controller):
    map_html = pkg_resources.resource_string(__name__, 'static/map.html')
    static_path = pkg_resources.resource_filename(__name__, 'static')

    app = flask.Flask('followme', static_path=static_path)
    app.config.from_object('followme.webapp.config')

    if 'FOLLOWME_SETTINGS' in os.environ:
        app.config.from_envvar('FOLLOWME_SETTINGS')

    reqlog = logging.getLogger('werkzeug')
    reqlog.setLevel(logging.ERROR)

    @app.route('/position')
    def position():
        pos = {
            'target': controller.p_target,
            'vehicle': controller.p_vehicle,
        }

        return flask.jsonify(pos)

    @app.route('/')
    def map():
        return map_html

    return app
