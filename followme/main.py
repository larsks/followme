from __future__ import absolute_import
from __future__ import print_function

import argparse
import dronekit
import logging
from pymavlink import mavutil
import threading
import time

from followme.geom import Point, Point3D, Point4D  # NOQA
from followme.gpsclient import GPS
from followme.webapp import create_app
from followme.tools import AveragePosition

LOG = logging.getLogger(__name__)

follow_alt = 30
target_distance = 10


class Follower(object):
    def __init__(self,
                 vehicle_connection=None,
                 follow_alt=20,
                 follow_distance=5,
                 min_delta=0.3,
                 average_points=5,
                 loop_interval=0.1,
                 port=None):

        if vehicle_connection is None:
            vehicle_connection = 'udp:localhost:14550'

        self.vehicle_connection = vehicle_connection
        self.follow_alt = follow_alt
        self.follow_distance = follow_distance
        self.min_delta = min_delta
        self.port = port
        self.loop_interval = loop_interval
        self._vpos = AveragePosition(average_points)

        self.connect_vehicle()
        self.connect_gpsd()

    @property
    def p_vehicle(self):
        return Point3D(*self._vpos.value)

    @property
    def p_target(self):
        return self.g.pos

    def update_vpos(self, obj, attr, val):
        self._vpos.append(val.lat, val.lon, val.alt)

    def start_app(self):
        app = create_app(self)
        t = threading.Thread(target=app.run,
                             kwargs=dict(port=self.port))
        t.setDaemon(True)
        t.start()

    def connect_vehicle(self):
        c = self.vehicle_connection
        LOG.info('connecting to %s', c)

        kwargs = {}

        if c.startswith('serial:'):
            try:
                _, dev, baud = c.split(':')
            except ValueError:
                _, dev = c.split(':')
                baud = None

            c = dev
            if baud is not None:
                kwargs['baud'] = baud

        self.v = dronekit.connect(c, **kwargs)
        self.v.location.add_attribute_listener(
            'global_frame',
            self.update_vpos)

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
        self.v.wait_for_armable()
        LOG.info('vehicle initialization complete')

    def prepare(self):
        self.wait_for_gps()
        self.wait_for_vehicle()

    def wait_for_arm(self):
        self.prepare()

        LOG.info('switching to GUIDED mode')
        self.v.wait_for_mode('GUIDED')

        LOG.info('arming vehicle')
        self.v.arm(wait=True)
        LOG.info('vehicle is armed')

    def goto_alt(self, alt):
        loc = dronekit.LocationGlobalRelative(
            self.p_vehicle.lat,
            self.p_vehicle.lng,
            alt)

        self.v.simple_goto(loc)
        self.v.wait_for_alt(alt)

    def takeoff(self):
        if self.v.armed:
            LOG.info('moving to follow altitude %dm', self.follow_alt)
            self.goto_alt(self.follow_alt)
        else:
            self.wait_for_arm()

            LOG.info('taking off to %fm', self.follow_alt)
            self.v.wait_simple_takeoff(self.follow_alt)

        LOG.info('reached target altitude (%fm)', self.follow_alt)

    def start_following(self):
        p_target_last = self.g.pos
        while True:
            p_target = self.p_target
            p_vehicle = self.p_vehicle

            d_target = p_vehicle.distance_to(p_target)
            d_moved = p_target_last.distance_to(p_target)
            b = p_vehicle.bearing_to(p_target)
            offset = (d_target - self.follow_distance)
            p_target_last = p_target
            yaw_offset = b - self.v.heading

            LOG.debug('distance to target: %f', d_target)
            LOG.debug('bearing to target: %f', b)
            LOG.debug('target moved: %f, offset: %f',
                      d_moved, offset)

            if d_moved < self.min_delta:
                LOG.debug('target is stationary')
                threshold = 0.1
            else:
                LOG.debug('target is in motion')
                threshold = 0.05

            max_offset = threshold * self.follow_distance
            if abs(offset) > max_offset:
                LOG.debug('move %f meters', offset)
                new_p_vehicle = p_vehicle.move_bearing(b, offset)
                self.v.simple_goto(dronekit.LocationGlobalRelative(
                    new_p_vehicle.lat, new_p_vehicle.lng,
                    self.follow_alt))

            if abs(yaw_offset) > 5:
                self.set_yaw(b)

            time.sleep(self.loop_interval)


def parse_args():
    p = argparse.ArgumentParser()

    p.add_argument('--port', '-p',
                   default=5000,
                   type=int,
                   help='port on which webapp will listen')
    p.add_argument('--no-takeoff', '-n',
                   action='store_true',
                   help='do not arm or takeoff')
    p.add_argument('--follow-distance', '-d',
                   type=float,
                   default=5,
                   help='horizontal distance to maintain from target')
    p.add_argument('--follow-alt', '-a',
                   type=float,
                   default=10,
                   help='following altitude to maintain')
    p.add_argument('--vehicle-connection', '-c')
    p.add_argument('--loop-interval', '-i',
                   type=float,
                   default=0.1,
                   help='control main loop frequency')
    p.add_argument('--debug',
                   action='store_const',
                   const='DEBUG',
                   dest='loglevel')

    p.set_defaults(loglevel='INFO')

    return p.parse_args()


def main():
    global follower

    args = parse_args()
    logging.basicConfig(level=args.loglevel)

    follower = Follower(port=args.port,
                        follow_distance=args.follow_distance,
                        follow_alt=args.follow_alt,
                        loop_interval=args.loop_interval,
                        vehicle_connection=args.vehicle_connection)
    follower.prepare()
    follower.start_app()

    if not args.no_takeoff:
        follower.takeoff()

    follower.start_following()


if __name__ == '__main__':
    main()
