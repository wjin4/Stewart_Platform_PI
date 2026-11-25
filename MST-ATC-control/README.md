# Dual Actuator Controller — Raspberry Pi 5

## Install (64-bit Raspberry Pi OS)
Install Miniforge for Linux aarch64 from https://github.com/conda-forge/miniforge, initialize the shell, then:

```sh
mamba create -n actuator -c conda-forge python=3.11 flask pyserial -y
mamba activate actuator
cd ~/Stewart_Platform_PI/MST-ATC-control
python app.py
```

Visit **http://10.0.1.36:5000** on a phone on the same LAN. If serial access is denied, run `sudo usermod -aG dialout $USER`, then log out and back in.

## Use
In **Manual Control**, select and connect a different USB serial port for each actuator. Default serial settings are 9600 baud, 8N1, no flow control, RTS/DTR off, and no appended newline. Manual mode supports independent send, loops, and stop (`s`).

In **Automatic Position Test**, first **manually move Actuator A fully to `>` and wait for it to stop**. Set position step (default 1000), maximum (20000), full-stroke wait (default 40 s), and OK timeout. The sequence is `A:P01000`, `B:<`, `B:>`, ... through `A:P20000`, then `A:<`, `B:<`, `B:>`. Position commands wait 3 seconds without OK; `<` and `>` wait for OK and then the configurable stroke duration. Raw received bytes are logged during command acknowledgment and movement waits. A `BUSY` response stops the test and attempts to send `s` to both actuators. **Stop Both** also sends `s`.

`OK` acknowledges command receipt, **not completed motion**. Fixed waits do not verify position; adjust them conservatively. Do not run another process using these USB ports. This is an unauthenticated LAN-only controller: do not expose it to the internet. Software stopping is not a hardware emergency stop.
