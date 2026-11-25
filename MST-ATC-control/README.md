# Dual Actuator Controller for Raspberry Pi 5

Serial defaults match COMTool screenshot: 9600 baud, 8 data bits, no parity, 1 stop bit, no flow control, RTS/DTR off, ASCII/UTF-8 text, no appended newline.

Each actuator uses a separate USB serial port and worker. On Stop, completed count, elapsed duration, or OK timeout, the worker sends the single byte `s` without a newline. Count mode waits for the last OK; duration mode interrupts waiting at the deadline. The UI expects OK (with or without newline).

Install:
```sh
sudo apt install python3-venv
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Visit http://10.0.1.36:5000 from a phone on the same network. If serial permissions fail, add the user to dialout and log out/in: `sudo usermod -aG dialout $USER`.

This is a LAN-only controller without authentication; do not expose it to the internet. Network and software stopping is not a safety-rated emergency stop.
