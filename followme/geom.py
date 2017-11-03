# -*- coding: utf8 -*-

import collections
import logging
import math

LOG = logging.getLogger(__name__)

_Point = collections.namedtuple('_Point', ['lat', 'lon', 'alt'])

# radius of the earth
R = 6371e3


class Point(_Point):
    '''A geographic point represented as a (lat, lon, alt) tuple.

    The distance_to and bearing_to methods assume that geographic
    coordinates are expressed in degrees.
    '''

    def __new__(cls, x, y, z, radians=False):
        self = super(Point, cls).__new__(cls, x, y, z)
        self.radians = radians
        return self

    def to_radians(self):
        '''Convert the latitude and longitude to radians.'''
        if self.radians:
            return self

        return Point(
            math.radians(self.lat),
            math.radians(self.lon),
            self.alt,
            radians=True
        )

    def to_degrees(self):
        if not self.radians:
            return self

        return Point(
            math.degrees(self.lat),
            math.degrees(self.lon),
            self.alt,
            radians=False
        )

    def distance_to(self, them):
        '''Calculate the distance to another Point.

        Calculate the distance in meters from self to them
        using the haversine formula.

        (http://www.movable-type.co.uk/scripts/latlong.html)
        '''

        self_r = self.to_radians()
        them_r = them.to_radians()
        dlat = them_r.lat - self_r.lat
        dlon = them_r.lon - self_r.lon

        a = (
            (math.sin(dlat/2) * math.sin(dlat/2)) +
            (math.cos(self_r.lat) * math.cos(them_r.lat) *
             math.sin(dlon/2) * math.sin(dlon/2))
        )

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        d = R * c

        return d

    def bearing_to(self, them):
        '''Caculate bearing to another Point.

        This implements the following formula, where φ and λ are latitude
        and longitude, respectively, expressed in radians:

        θ = atan2(sin Δλ ⋅ cos φ2 , cos φ1 ⋅ sin φ2 − sin φ1 ⋅ cos φ2 ⋅ cos Δλ)

        (http://www.movable-type.co.uk/scripts/latlong.html)
        '''

        self_r = self.to_radians()
        them_r = them.to_radians()

        dlon = them_r.lon - self_r.lon
        x = math.sin(dlon) * math.cos(them_r.lat)
        y = (
                (math.cos(self_r.lat) * math.sin(them_r.lat)) -
                (math.sin(self_r.lat) * math.cos(them_r.lat) * math.cos(dlon))
                )

        theta = math.atan2(x, y)
        return math.degrees(theta) % 360

    def move_bearing(self, b, d):
        self_r = self.to_radians()
        b = math.radians(b)

        lat1 = self_r.lat
        lon1 = self_r.lon

        lat2 = math.asin(
            (math.sin(lat1) * math.cos(d/R)) +
            (math.cos(lat1) * math.sin(d/R) * math.cos(b))
        )

        lon2 = lon1 + math.atan2(
            (math.sin(b) * math.sin(d/R) * math.cos(lat1)),
            (math.cos(d/R) - math.sin(lat1) * math.sin(lat2))
        )

        return Point(
            math.degrees(lat2),
            math.degrees(lon2),
            self.alt
        )
