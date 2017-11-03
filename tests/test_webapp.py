import json
import unittest

from followme.geom import Point, Point4D  # NOQA
from followme.webapp import create_app


class FakeController(object):
    @property
    def p_target(self):
        return Point(10, 10)

    @property
    def p_vehicle(self):
        return Point4D(20, 20, 20, 180)


class TestPoint(unittest.TestCase):
    def setUp(self):
        app = create_app(FakeController())
        app.config['TESTING'] = True
        self.app = app.test_client()

    def test_map(self):
        rv = self.app.get('/')
        assert rv.status_code == 200
        assert rv.get_data().startswith('<!DOCTYPE html>')

    def test_position(self):
        rv = self.app.get('/position')
        assert rv.status_code == 200
        assert rv.mimetype == 'application/json'
        data = json.loads(rv.get_data())
        assert 'target' in data
        assert 'vehicle' in data
        assert data['target']['lat'] == 10
        assert data['vehicle']['lat'] == 20
