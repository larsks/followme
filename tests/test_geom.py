import unittest

from followme.geom import Point

# whitehouse
p1 = Point(38.897741, -77.036450)

# pool (180 meters due south of the whitehouse)
p2 = Point(38.89612222110935, -77.03645)


class TestPoint(unittest.TestCase):

    def test_distance(self):
        d = p1.distance_to(p2)
        assert abs(180 - d) < 1

    def test_bearing(self):
        b = p1.bearing_to(p2)
        assert abs(180 - b) < 1

    def test_move(self):
        p3 = p1.move_bearing(180, 180)
        d1 = p1.distance_to(p3)
        assert abs(180 - d1) < 1
        d2 = p2.distance_to(p3)
        assert d2 < 1
