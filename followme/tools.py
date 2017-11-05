from followme.geom import Point3D


class AveragePosition (object):
    def __init__(self, npoints):
        self.npoints = npoints
        self.values = []

    @property
    def value(self):
        if len(self.values) == 0:
            return (0, 0, 0)

        return Point3D(*(float(sum(x))/len(x) for x in zip(*self.values)))

    def append(self, lat, lng, alt):
        self.values.append((lat, lng, alt))
        self.values = self.values[-self.npoints:]
