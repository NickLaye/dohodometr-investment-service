"""
Простой планировщик задач для админ-модуля (in-process, минимальный).
"""

import threading
import time
from collections.abc import Callable


class RepeatedTimer:
    def __init__(self, interval_seconds: float, function: Callable, *args, **kwargs):
        self.interval = interval_seconds
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        while not self._stop_event.is_set():
            try:
                self.function(*self.args, **self.kwargs)
            finally:
                time.sleep(self.interval)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._thread.join(timeout=1)


