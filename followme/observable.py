import threading


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
