from __future__ import print_function

import dronekit
import flask
import json
import logging
from pymavlink import mavutil
import threading
import time

from followme.geom import Point
from followme.gps import GPS

LOG = logging.getLogger(__name__)

follow_alt = 30
target_distance = 10


def webapp(vehicle_pos, target_pos, debug=False):
    app = flask.Flask(__name__)

    reqlog = logging.getLogger('werkzeug')
    reqlog.setLevel(logging.ERROR)

    with open('map.html') as fd:
        map_html = fd.read()

    @app.route('/position')
    def position():
        pos = {
            'target': target_pos.pos,
            'vehicle': vehicle_pos.pos,
        }

        return flask.jsonify(pos)

    @app.route('/')
    def map():
        return map_html

    return app


class VehiclePos(object):
    def __init__(self, vehicle):
        self.v = vehicle

    @property
    def pos(self):
        loc = self.v.location.global_relative_frame

        return dict(lat=loc.lat, lon=loc.lon, alt=loc.alt,
                    bearing=self.v.heading)


class Follower(object):
    def __init__(self,
                 vehicle_connection=None,
                 follow_alt=20,
                 follow_distance=5,
                 min_delta=0.1):

        if vehicle_connection is None:
            vehicle_connection = 'localhost:14550'

        self.follow_alt = follow_alt
        self.follow_distance = follow_distance
        self.min_delta = min_delta

        self.connect_vehicle(vehicle_connection)
        self.connect_gpsd()
        self.start_app()

    def start_app(self):
        app = webapp(VehiclePos(self.v), self.g)
        t = threading.Thread(target=app.run)
        t.setDaemon(True)
        t.start()

    def connect_vehicle(self, vehicle_connection):
        self.v = dronekit.connect(vehicle_connection)

    def connect_gpsd(self):
        self.g = GPS()
        self.g.start()

    def set_yaw(self, heading, relative=False):
        if relative:
            is_relative = 1
        else:
            is_relative = 0

        msg = self.v.message_factory.command_long_encode(
            0, 0,
            mavutil.mavlink.MAV_CMD_CONDITION_YAW,
            0,
            heading,
            0,
            1,
            is_relative,
            0, 0, 0)

        self.v.send_mavlink(msg)

    def wait_for_gps(self):
        LOG.info('waiting for local gps fix')
        while not self.g.has_fix:
            time.sleep(1)
        LOG.info('local gps fix acquired')

    def wait_for_vehicle(self):
        LOG.info('waiting for vehicle to initialize')
        while not self.v.is_armable:
            time.sleep(1)
        LOG.info('vehicle initialization complete')

    def prepare(self):
        self.wait_for_gps()
        self.wait_for_vehicle()
        self._prepared = True

    def wait_for_arm(self):
        self.prepare()

        LOG.info('arming vehicle')
        self.v.arm()
        while not self.v.armed:
            time.sleep(1)
        LOG.info('vehicle is armed')

    def takeoff(self):
        self.wait_for_arm()

        LOG.info('taking off')
        self.v.mode = 'GUIDED'
        self.v.simple_takeoff(self.follow_alt)

        LOG.info('waiting for altitude')
        while True:
            cur_alt = self.v.location.global_relative_frame.alt
            if cur_alt >= (0.95 * self.follow_alt):
                break
            time.sleep(1)
        LOG.info('reached altitude %f', cur_alt)

    @property
    def p_target(self):
        return self.g.pos

    @property
    def p_vehicle(self):
        loc = self.v.location.global_relative_frame
        return Point(loc.lat, loc.lon, loc.alt)

    def start_following(self):
        p_target_last = self.p_target
        while True:
            p_target = self.p_target
            p_vehicle = self.p_vehicle

            d_target = p_vehicle.distance_to(p_target)
            d_moved = p_target_last.distance_to(p_target)
            b = p_vehicle.bearing_to(p_target)
            offset = (d_target - self.follow_distance)

            LOG.info('distance to target: %f', d_target)
            LOG.info('bearing to target: %f', b)
            LOG.info('target moved: %f, offset: %f',
                     d_moved, offset)

            if abs(offset) > (0.05 * self.follow_distance):
                LOG.info('move %f meters', offset)
                new_p_vehicle = p_vehicle.move_bearing(b, offset)
                self.v.simple_goto(dronekit.LocationGlobalRelative(
                    *new_p_vehicle))
            else:
                self.v.simple_goto(self.v.location.global_relative_frame)

            self.set_yaw(b)
            p_target_last = p_target
            time.sleep(0.5)


def main():
    global follower

    logging.basicConfig(level='INFO')
    follower = Follower()
    follower.prepare()


if __name__ == '__main__':
    main()
