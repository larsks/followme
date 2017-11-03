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

LOG = logging.getLogger(__name__)

follow_alt = 30
target_distance = 10


class Follower(object):
    def __init__(self,
                 vehicle_connection=None,
                 follow_alt=20,
                 follow_distance=5,
                 min_delta=0.1,
                 port=None):

        if vehicle_connection is None:
            vehicle_connection = 'udp:localhost:14550'

        self.vehicle_connection = vehicle_connection
        self.follow_alt = follow_alt
        self.follow_distance = follow_distance
        self.min_delta = min_delta
        self.port = port

        self.connect_vehicle()
        self.connect_gpsd()
        self.start_app()

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
        if self.v.armed and self.p_vehicle.alt > 1:
            LOG.info('moving to follow altitude %dm', self.follow_alt)
            self.goto_alt(self.follow_alt)
        else:
            self.wait_for_arm()

            LOG.info('taking off to %fm', self.follow_alt)
            self.v.wait_simple_takeoff(self.follow_alt)

        LOG.info('reached target altitude (%fm)', self.follow_alt)

    @property
    def p_target(self):
        return self.g.pos

    @property
    def p_vehicle(self):
        loc = self.v.location.global_relative_frame
        return Point4D(loc.lat, loc.lon, loc.alt, self.v.heading)

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
                    *new_p_vehicle[:3]))
            else:
                self.v.simple_goto(self.v.location.global_relative_frame)

            self.set_yaw(b)
            p_target_last = p_target
            time.sleep(0.5)


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

    return p.parse_args()


def main():
    global follower

    args = parse_args()

    logging.basicConfig(level='INFO')
    follower = Follower(port=args.port,
                        follow_distance=args.follow_distance,
                        follow_alt=args.follow_alt,
                        vehicle_connection=args.vehicle_connection)
    follower.prepare()

    if not args.no_takeoff:
        follower.takeoff()

    follower.start_following()

if __name__ == '__main__':
    main()
