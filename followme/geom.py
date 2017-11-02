# -*- coding: utf8 -*-

import math
import collections

_Point = collections.namedtuple('_Point', ['lat', 'lon', 'alt'])

# radius of the earth
R = 6371e3

class Point(_Point):
    '''A geographic point represented as a (lat, lon, alt) tuple.
    
    The distance_to and bearing_to methods assume that geographic
    coordinates are expressed in degrees.
    '''

    def to_radians(self):
        '''Convert the latitude and longitude to radians.'''
        return Point(
                math.radians(self.lat),
                math.radians(self.lon),
                self.alt
                )

    def distance_to(self, them):
        '''Calculate the distance to another Point.

        This implements the Law of Cosines, where φ and λ are latitude
        and longitude, respectively, expressed in radians:

        d = acos(sin φ1 ⋅ sin φ2 + cos φ1 ⋅ cos φ2 ⋅ cos Δλ) ⋅ R

        (http://www.movable-type.co.uk/scripts/latlong.html)
        '''

        self_r = self.to_radians()
        them_r = them.to_radians()

        dlon = them_r.lon - self_r.lon

        d = math.acos(
                (math.sin(self_r.lat) * math.sin(them_r.lat)) +
                (math.cos(self_r.lat) * math.cos(them_r.lat) * math.cos(dlon))
                ) * R

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
                (math.cos(self_r.lat) * math.sin(them_r.lat))-
                (math.sin(self_r.lat) * math.cos(them_r.lat) * math.cos(dlon))
                )

        theta = math.atan2(x, y)
        return math.degrees(theta)

if __name__ == '__main__':
    p0 = Point(42.384472, -71.162725, 10)
    p_north = Point(42.384654, -71.162741, 10)
    p_east = Point(42.384479, -71.162445, 10)
    p_south = Point(42.384317, -71.162710, 10)

    print 'bearing to p_north:', p0.bearing_to(p_north)
    print 'bearing to p_east:', p0.bearing_to(p_east)
    print 'bearing to p_south:', p0.bearing_to(p_south)

    print 'distance to p_north:', p0.distance_to(p_north)
    print 'distance to p_east:', p0.distance_to(p_east)
    print 'distance to p_south:', p0.distance_to(p_south)
