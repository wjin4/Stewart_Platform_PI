"""Background position sweep using the web server's already-open serial channels."""
import threading
import time
from collections import deque


def sequence(step, maximum):
    yield 'a', '<'
    for position in range(step, maximum + 1, step):
        yield 'a', f'P{position}'
        yield 'b', '<'
        yield 'b', '>'
    yield 'a', '>'
    yield 'b', '<'
    yield 'b', '>'


class PositionTest:
    def __init__(self, channels):
        self.channels = channels
        self.lock = threading.RLock()
        self.cancel = threading.Event()
        self.running = False
        self.state = 'idle'
        self.error = None
        self.completed = 0
        self.total = 0
        self.current = ''
        self.logs = deque(maxlen=300)

    def log(self, message):
        with self.lock:
            self.logs.append(f'{time.strftime("%H:%M:%S")} {message}')

    def status(self):
        with self.lock:
            return dict(running=self.running, state=self.state, error=self.error,
                        completed=self.completed, total=self.total, current=self.current,
                        logs=list(self.logs))

    def start(self, step, maximum, timeout):
        if not (1 <= step <= 20000 and 1 <= maximum <= 20000 and maximum % step == 0):
            raise ValueError('Step must divide maximum position (1 to 20000)')
        if not 0.1 <= timeout <= 3600:
            raise ValueError('Timeout must be between 0.1 and 3600 seconds')
        with self.lock:
            if self.running:
                raise ValueError('Test already running')
            for ch in self.channels.values():
                if not ch.ser or not ch.ser.is_open or ch.running:
                    raise ValueError('Connect both actuators and stop manual loops first')
            self.cancel.clear()
            for ch in self.channels.values():
                ch.stop_event.clear()
            self.running = True
            self.state = 'running'
            self.error = None
            self.completed = 0
            self.total = 3 * (maximum // step) + 4
            self.current = ''
            self.logs.clear()
            threading.Thread(target=self._run, args=(step, maximum, timeout), daemon=True).start()

    def stop(self):
        self.cancel.set()
        for ch in self.channels.values():
            ch.stop_event.set()
        self.log('Stop requested')
        # Send stop now, rather than waiting for a worker timeout.
        for ch in self.channels.values():
            ch.send_stop()

    def _run(self, step, maximum, timeout):
        try:
            for cid, command in sequence(step, maximum):
                if self.cancel.is_set():
                    raise InterruptedError('Cancelled')
                with self.lock:
                    self.current = f'Actuator {cid.upper()}: {command}'
                self.log(f'TX {self.current}')
                self.channels[cid].exchange(command, 'none', timeout)
                if self.cancel.is_set():
                    raise InterruptedError('Cancelled')
                with self.lock:
                    self.completed += 1
                self.log(f'RX OK: {self.current}')
            with self.lock:
                self.state = 'complete'
                self.current = 'Finished'
            self.log('Sweep completed successfully')
        except InterruptedError:
            with self.lock:
                self.state = 'stopped'
            self.log('Sweep cancelled')
        except Exception as exc:
            with self.lock:
                self.state = 'error'
                self.error = str(exc)
            self.log(f'ERROR {exc}')
        finally:
            # Stop both at the end, including successful completion.
            for ch in self.channels.values():
                ch.send_stop()
            with self.lock:
                self.running = False
