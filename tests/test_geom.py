import unittest

from followme.geom import Point, Point3D, Point4D  # NOQA

# whitehouse
p1 = Point(38.897741, -77.036450)
p1z = Point3D(38.897741, -77.036450, 10)
p1zb = Point4D(38.897741, -77.036450, 10, 180)

# pool (180 meters due south of the whitehouse)
p2 = Point(38.89612222110935, -77.03645)
p2z = Point3D(38.89612222110935, -77.03645, 10)
p2zb = Point4D(38.89612222110935, -77.03645, 10, 180)


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

    def test_2d_3d_compat(self):
        d = p1z.distance_to(p2)
        assert abs(180 - d) < 1

        d = p1.distance_to(p2z)
        assert abs(180 - d) < 1

    def test_2d_4d_compat(self):
        d = p1zb.distance_to(p2)
        assert abs(180 - d) < 1

        d = p1.distance_to(p2zb)
        assert abs(180 - d) < 1
