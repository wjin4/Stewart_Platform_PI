import threading
import time
from collections import deque
from flask import Flask, jsonify, render_template, request
import serial
from serial.tools import list_ports

app = Flask(__name__)

class Channel:
    def __init__(self, name):
        self.name = name
        self.lock = threading.RLock()
        self.io_lock = threading.Lock()
        self.ser = None
        self.port = None
        self.baud = None
        self.worker = None
        self.stop_event = threading.Event()
        self.running = False
        self.completed = 0
        self.error = None
        self.logs = deque(maxlen=250)

    def log(self, message):
        with self.lock:
            self.logs.append(f'{time.strftime("%H:%M:%S")} {message}')

    def connect(self, port, baud):
        with self.lock:
            if self.running:
                raise ValueError('Stop the loop before reconnecting')
            if self.ser:
                self.ser.close()
                self.ser = None
            self.ser = serial.Serial(port, baudrate=baud, bytesize=8, parity=serial.PARITY_NONE, stopbits=1, xonxoff=False, rtscts=False, dsrdtr=False, timeout=0.05, write_timeout=0.5)
            self.ser.rts = False
            self.ser.dtr = False
            self.port, self.baud = port, baud
            self.error = None
            self.log(f'Connected {port} at {baud}')

    def disconnect(self):
        with self.lock:
            if self.running:
                raise ValueError('Stop the loop before disconnecting')
            if self.ser:
                self.ser.close()
            self.ser = None
            self.port = None
            self.log('Disconnected')

    def exchange(self, command, ending, timeout, duration_deadline=None):
        # Only the channel worker or an idle manual request calls this method.
        payload = command.encode('utf-8') + {'lf': b'\n', 'crlf': b'\r\n', 'cr': b'\r', 'none': b''}[ending]
        with self.io_lock:
            self.ser.reset_input_buffer()
            self.ser.write(payload)
            self.ser.flush()
        self.log(f'TX {payload!r}')
        deadline = time.monotonic() + timeout
        buffer = bytearray()
        while time.monotonic() < deadline:
            if self.stop_event.is_set() or (duration_deadline is not None and time.monotonic() >= duration_deadline):
                raise InterruptedError('Stopped')
            with self.io_lock:
                chunk = self.ser.read(128)
            if chunk:
                buffer.extend(chunk)
                if len(buffer) > 8192:
                    raise ValueError('Response exceeds 8192 bytes')
                # Accept OK on a complete CR/LF-delimited line, or bare OK.
                lines = bytes(buffer).replace(b'\r', b'\n').split(b'\n')
                if any(line.strip() == b'OK' for line in lines):
                    self.log(f'RX {bytes(buffer)!r} (OK)')
                    return
                # For bare OK with no terminator, accept only when entire buffer is OK.
                if bytes(buffer).strip() == b'OK':
                    self.log('RX OK')
                    return
        self.log(f'RX timeout; received {bytes(buffer)!r}')
        raise TimeoutError(f'No OK within {timeout:g} seconds')

    def start(self, command, ending, timeout, mode, limit):
        with self.lock:
            if not self.ser or not self.ser.is_open:
                raise ValueError('Connect a serial port first')
            if self.running:
                raise ValueError('Channel already running')
            self.stop_event.clear()
            self.running = True
            self.completed = 0
            self.error = None
            self.worker = threading.Thread(target=self._run, args=(command, ending, timeout, mode, limit), daemon=True)
            self.worker.start()

    def _run(self, command, ending, timeout, mode, limit):
        start = time.monotonic()
        duration_deadline = start + limit if mode == 'duration' else None
        self.log(f'Started {mode} loop; limit={limit}')
        try:
            while not self.stop_event.is_set():
                if mode == 'count' and self.completed >= int(limit):
                    break
                if mode == 'duration' and time.monotonic() - start >= limit:
                    break
                self.exchange(command, ending, timeout, duration_deadline)
                with self.lock:
                    self.completed += 1
        except InterruptedError:
            pass
        except Exception as exc:
            with self.lock:
                self.error = str(exc)
            self.log(f'ERROR {exc}')
        finally:
            self.send_stop()
            with self.lock:
                self.running = False
            self.log('Loop finished; stop command sent')

    def send_stop(self):
        try:
            with self.io_lock:
                if self.ser and self.ser.is_open:
                    self.ser.write(b's')
                    self.ser.flush()
                    self.log("TX b's' (STOP)")
        except Exception as exc:
            with self.lock:
                self.error = f'Stop command failed: {exc}'
            self.log(f'STOP ERROR {exc}')

    def stop(self):
        self.stop_event.set()
        self.log('Stop requested')
        # The worker sends s on exit. If idle, send it here.
        with self.lock:
            running = self.running
        if not running:
            self.send_stop()

    def status(self):
        with self.lock:
            return dict(name=self.name, connected=bool(self.ser and self.ser.is_open), port=self.port,
                        baud=self.baud, running=self.running, completed=self.completed,
                        error=self.error, logs=list(self.logs))

channels = {'a': Channel('Actuator A'), 'b': Channel('Actuator B')}

def get_channel(cid):
    if cid not in channels:
        raise ValueError('Unknown channel')
    return channels[cid]

def settings(data):
    command = str(data.get('command', ''))
    ending = data.get('ending', 'none')
    timeout = float(data.get('timeout', 5))
    if not command or len(command) > 1024:
        raise ValueError('Command must contain 1 to 1024 characters')
    if ending not in ('lf', 'crlf', 'cr', 'none'):
        raise ValueError('Invalid line ending')
    if not 0.1 <= timeout <= 3600:
        raise ValueError('Timeout must be 0.1 to 3600 seconds')
    return command, ending, timeout

@app.errorhandler(Exception)
def handle_error(exc):
    return jsonify(error=str(exc)), 400

@app.get('/')
def index():
    return render_template('index.html')

@app.get('/api/ports')
def ports():
    return jsonify([{'device': p.device, 'description': p.description} for p in list_ports.comports()])

@app.get('/api/status')
def status():
    return jsonify({cid: ch.status() for cid, ch in channels.items()})

@app.post('/api/<cid>/connect')
def connect(cid):
    ch = get_channel(cid)
    data = request.get_json(force=True)
    port = str(data.get('port', ''))
    valid_ports = {p.device for p in list_ports.comports()}
    if port not in valid_ports:
        raise ValueError('Select an available serial port')
    for other in channels.values():
        if other is not ch and other.port == port and other.ser and other.ser.is_open:
            raise ValueError('This port is already connected to another channel')
    baud = int(data.get('baud', 9600))
    if not 300 <= baud <= 4000000:
        raise ValueError('Invalid baud rate')
    ch.connect(port, baud)
    return jsonify(ok=True)

@app.post('/api/<cid>/disconnect')
def disconnect(cid):
    get_channel(cid).disconnect()
    return jsonify(ok=True)

@app.post('/api/<cid>/start')
def start(cid):
    ch = get_channel(cid)
    data = request.get_json(force=True)
    command, ending, timeout = settings(data)
    mode = data.get('mode', 'count')
    limit = float(data.get('limit', 1))
    if mode not in ('count', 'duration') or not 1 <= limit <= 100000000:
        raise ValueError('Invalid loop mode or limit')
    if mode == 'count' and not limit.is_integer():
        raise ValueError('Count must be an integer')
    ch.start(command, ending, timeout, mode, limit)
    return jsonify(ok=True)

@app.post('/api/<cid>/stop')
def stop(cid):
    get_channel(cid).stop()
    return jsonify(ok=True)

@app.post('/api/<cid>/send')
def send(cid):
    ch = get_channel(cid)
    data = request.get_json(force=True)
    command, ending, timeout = settings(data)
    with ch.lock:
        if ch.running:
            raise ValueError('Stop the loop before manual send')
        if not ch.ser or not ch.ser.is_open:
            raise ValueError('Connect first')
        ch.stop_event.clear()
        ch.exchange(command, ending, timeout)
    return jsonify(ok=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=False)
