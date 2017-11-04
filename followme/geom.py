# -*- coding: utf8 -*-

import collections
import logging
import math

LOG = logging.getLogger(__name__)

_Point = collections.namedtuple('Point', ['lat', 'lng'])
_Point3D = collections.namedtuple('Point3D', ['lat', 'lng', 'alt'])
_Point4D = collections.namedtuple('Point4D', ['lat', 'lng', 'alt', 'bearing'])

# radius of the earth
R = 6371e3


class PointBase(object):

    def to_radians(self):
        '''Convert the latitude and longitude to radians.'''
        return _Point(math.radians(self.lat), math.radians(self.lng))

    def distance_to(self, them):
        '''Calculate the distance to another Point.

        Calculate the distance in meters from self to them
        using the haversine formula.

        (http://www.movable-type.co.uk/scripts/latlong.html)
        '''

        LOG.info('them = %s', type(them))

        self_r = self.to_radians()
        them_r = them.to_radians()
        dlat = them_r.lat - self_r.lat
        dlng = them_r.lng - self_r.lng

        a = (
            (math.sin(dlat/2) * math.sin(dlat/2)) +
            (math.cos(self_r.lat) * math.cos(them_r.lat) *
             math.sin(dlng/2) * math.sin(dlng/2))
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

        dlng = them_r.lng - self_r.lng
        x = math.sin(dlng) * math.cos(them_r.lat)
        y = (
                (math.cos(self_r.lat) * math.sin(them_r.lat)) -
                (math.sin(self_r.lat) * math.cos(them_r.lat) * math.cos(dlng))
                )

        theta = math.atan2(x, y)
        return math.degrees(theta) % 360

    def move_bearing(self, b, d):
        self_r = self.to_radians()
        b = math.radians(b)

        lat1 = self_r.lat
        lng1 = self_r.lng

        lat2 = math.asin(
            (math.sin(lat1) * math.cos(d/R)) +
            (math.cos(lat1) * math.sin(d/R) * math.cos(b))
        )

        lng2 = lng1 + math.atan2(
            (math.sin(b) * math.sin(d/R) * math.cos(lat1)),
            (math.cos(d/R) - math.sin(lat1) * math.sin(lat2))
        )

        return self.__class__(
            math.degrees(lat2),
            math.degrees(lng2),
            *self[2:]
        )


class Point(_Point, PointBase):
    '''A geographic point represented as a (lat, lng) tuple.'''


class Point3D(_Point3D, PointBase):
    pass


class Point4D(_Point4D, PointBase):
    pass
