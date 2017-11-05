from __future__ import absolute_import
from __future__ import print_function

import logging
import socket
import threading
import time

import gps

from followme.geom import Point3D
from followme.observable import Observable
from followme.tools import AveragePosition

LOG = logging.getLogger(__name__)


# A placeholder value used before we receive any fix information
# from gpsd.
class _NoFix (object):
    mode = 0

NoFix = _NoFix()


class GPS(Observable, threading.Thread):
    def __init__(self, average_points=5):
        super(GPS, self).__init__()
        self.setDaemon(True)
        self.lock = threading.Lock()

        self._fix = NoFix
        self._lastfix = NoFix
        self._lastgood = None
        self._avg = AveragePosition(average_points)
        self._quit = False

    def _set_fix(self, fix):
        with self.lock:
            self._lastfix = self.fix
            self._fix = fix

            if fix.mode == gps.MODE_3D:
                self._lastgood = fix
                self._avg.append(fix.lat, fix.lon, fix.alt)

        if self._lastfix.mode != self._fix.mode:
            LOG.debug('notifying observers of fix change, %d -> %d',
                      self._lastfix.mode, self._fix.mode)
            self.notify_observers(self._lastfix, self._fix)

    def _run(self):
        self.gps = gps.gps()
        self.gps.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)

        for report in self.gps:
            if self._quit:
                break

            if report.get('class') == 'TPV':
                self._set_fix(report)

    def run(self):
        while True:
            try:
                self._run()
            except socket.error:
                LOG.error('failed to connect gpsd')
                time.sleep(1)
                continue
            finally:
                self._set_fix(NoFix)

    def cancel(self):
        self._quit = True

    @property
    def fix(self):
        return self._fix

    @property
    def has_fix(self):
        return self._fix.mode == gps.MODE_3D

    @property
    def pos(self):
        return self._avg.value

    @property
    def raw(self):
        fix = self._lastgood
        if not fix:
            return None

        return Point3D(fix.lat, fix.lon, fix.alt)
