from __future__ import absolute_import
from __future__ import print_function

import functools
from itertools import ifilter
import threading
import time

import gps


# A placeholder value used before we receive any fix information
# from gpsd.
NoFix = type('', (), {'mode': -1})()


class Observable(object):
    def __init__(self):
        super(Observable, self).__init__()

        self._observers = set()
        self._obs_lock = threading.Lock()

    def clear_observers(self):
        with self._obs_lock:
            self._observers = set()

    def add_observer(self, func):
        with self._obs_lock:
            self._observers.add(func)

    def remove_observer(self, func):
        with self._obs_lock:
            try:
                self._observers.remove(func)
            except KeyError:
                pass

    def notify_observers(self, *args, **kwargs):
        with self._obs_lock:
            obs = list(self._observers)

        for func in obs:
            func(*args, **kwargs)


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
        self.gps.stream(gps.WATCH_ENABLE|gps.WATCH_NEWSTYLE)

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
        return (fix.lat, fix.lon, fix.alt)
