from __future__ import absolute_import
from __future__ import print_function

import threading

import gps

from followme.geom import Point
from followme.observable import Observable


# A placeholder value used before we receive any fix information
# from gpsd.
class _NoFix (object):
    mode = -1

NoFix = _NoFix()


class GPS(Observable, threading.Thread):
    def __init__(self):
        super(GPS, self).__init__()
        self.setDaemon(True)
        self.gps = gps.gps()
        self.lock = threading.Lock()

        self._fix = NoFix
        self._lastfix = NoFix
        self._quit = False

    def run(self):
        self.gps.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)

        for report in self.gps:
            if self._quit:
                break

            if report['class'] == 'TPV':
                with self.lock:
                    self._lastfix = self._fix
                    self._fix = report

                if self._lastfix.mode != self._fix.mode:
                    self.notify_observers(self._lastfix, self._fix)

    def cancel(self):
        self._quit = True

    @property
    def fix(self):
        with self.lock:
            return self._fix

    @property
    def has_fix(self):
        with self.lock:
            return self._fix and self._fix.mode == gps.MODE_3D

    @property
    def pos(self):
        if not self.has_fix:
            return

        fix = self.fix
        return Point(fix.lat, fix.lon, fix.alt)
