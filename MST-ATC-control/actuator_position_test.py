#!/usr/bin/env python3
"""Sequential two-actuator position sweep (9600 8N1, raw ASCII, no newline)."""
import argparse
import sys
import time
import serial
from serial.tools import list_ports

class TestStopped(Exception):
    pass

def available_ports():
    return [p.device for p in list_ports.comports()]

def command(port, name, cmd, timeout):
    # Do not clear the input buffer: preserve fast acknowledgments, but ignore
    # stale bytes accumulated before the command by clearing first.
    port.reset_input_buffer()
    port.write(cmd.encode('ascii'))
    port.flush()
    print(f'{time.strftime("%H:%M:%S")} {name} TX {cmd!r}', flush=True)
    deadline = time.monotonic() + timeout
    buf = bytearray()
    while time.monotonic() < deadline:
        chunk = port.read(128)
        if chunk:
            buf.extend(chunk)
            # Match standalone OK in a stream, with or without line endings.
            # For this device protocol, any OK token is an acknowledgment.
            if b'OK' in buf:
                print(f'{time.strftime("%H:%M:%S")} {name} RX OK', flush=True)
                return
            if len(buf) > 8192:
                buf = buf[-128:]
    raise TimeoutError(f'{name}: no OK within {timeout:g}s after {cmd!r}; received {bytes(buf)!r}')

def stop_both(ports):
    for name, port in ports:
        try:
            port.write(b's')
            port.flush()
            print(f'{name} TX STOP (s)', flush=True)
        except Exception as exc:
            print(f'{name}: unable to send stop: {exc}', file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port1', help='USB serial port for Actuator 1')
    parser.add_argument('--port2', help='USB serial port for Actuator 2')
    parser.add_argument('--baud', type=int, default=9600)
    parser.add_argument('--timeout', type=float, default=30.0, help='Seconds to wait for each OK')
    parser.add_argument('--step', type=int, default=1000)
    parser.add_argument('--max-position', type=int, default=20000)
    parser.add_argument('--dry-run', action='store_true', help='Show sequence without moving actuators')
    args = parser.parse_args()
    if args.step <= 0 or args.max_position <= 0 or args.max_position % args.step or args.timeout <= 0:
        parser.error('step and timeout must be positive, and max-position must be divisible by step')
    sequence = [('A1', '<')]
    for pos in range(args.step, args.max_position + 1, args.step):
        sequence.extend([('A1', f'P{pos}'), ('A2', '<'), ('A2', '>')])
    sequence.extend([('A1', '>'), ('A2', '<'), ('A2', '>')])
    if args.dry_run:
        for i, (name, cmd) in enumerate(sequence, 1):
            print(f'{i:03d} {name}: {cmd} -> wait OK')
        return 0
    ports_found = available_ports()
    print('Available serial ports:', ', '.join(ports_found) or '(none)')
    if not args.port1 or not args.port2:
        parser.error('specify both --port1 and --port2 (see available ports above)')
    if args.port1 == args.port2:
        parser.error('Actuators must use different serial ports')
    opened = []
    completed = False
    try:
        for name, device in [('A1', args.port1), ('A2', args.port2)]:
            s = serial.Serial(device, baudrate=args.baud, bytesize=8,
                              parity=serial.PARITY_NONE, stopbits=1,
                              timeout=0.05, write_timeout=2,
                              rtscts=False, dsrdtr=False)
            opened.append((name, s))
        by_name = dict(opened)
        print('Check clear travel, correct port assignments, and hardware E-stop.')
        if input('Type RUN to start motion: ').strip() != 'RUN':
            print('Cancelled without motion.')
            return 1
        for idx, (name, cmd) in enumerate(sequence, 1):
            print(f'[{idx}/{len(sequence)}]', end=' ')
            command(by_name[name], name, cmd, args.timeout)
        completed = True
        print('Test complete. Both actuators at commanded retracted endpoints.')
        return 0
    except (KeyboardInterrupt, TimeoutError, serial.SerialException, OSError) as exc:
        print(f'ABORTED: {exc}', file=sys.stderr)
        return 2
    finally:
        if not completed and opened:
            stop_both(opened)
        for _, s in opened:
            s.close()

if __name__ == '__main__':
    sys.exit(main())
