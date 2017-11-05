import flask
import logging
import os
import pkg_resources


class config(object):
    DEBUG = False
    STATIC_FOLDER = pkg_resources.resource_filename(__name__, 'static')
    STATIC_URL_PATH = '/static'


def create_app(controller):
    map_html = pkg_resources.resource_string(__name__, 'static/map.html')

    app = flask.Flask('followme')
    app.config.from_object('followme.webapp.config')

    if 'FOLLOWME_SETTINGS' in os.environ:
        app.config.from_envvar('FOLLOWME_SETTINGS')

    reqlog = logging.getLogger('werkzeug')
    reqlog.setLevel(logging.ERROR)

    @app.route('/position')
    def position():
        pos = [
            {
                'title': 'target',
                'position': controller.p_target,
                'label': 'T',
                'center': True,
                'symbol': 'CIRCLE',
                'color': 'green',
            },
            {
                'title': 'vehicle',
                'position': controller.p_vehicle,
                'label': 'V',
                'symbol': 'FORWARD_CLOSED_ARROW',
                'heading': controller.v.heading,
            },
        ]

        return flask.jsonify(pos)

    @app.route('/')
    def map():
        return map_html

    return app
