# Raspberry Pi 5 Dual Actuator Controller

Mobile web UI with **Manual Control** and **Automatic Position Test**. USB serial defaults: **9600 baud, 8N1, no flow control, no appended newline**. Commands are ASCII; `OK` (with or without newline) is treated as completion. `s` stops an actuator immediately (no newline).

## Install with Mamba

On 64-bit Raspberry Pi OS (`uname -m` should show `aarch64`), install [Miniforge](https://github.com/conda-forge/miniforge) if needed:

```sh
cd ~
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-aarch64.sh
bash Miniforge3-Linux-aarch64.sh
source ~/.bashrc
mamba create -n actuator -c conda-forge python=3.11 flask pyserial -y
sudo usermod -aG dialout "$USER"   # log out and back in once
```

## Start the website

```sh
cd ~/Stewart_Platform_PI/MST-ATC-control
mamba activate actuator
python app.py
```

On your phone (same LAN), open **http://10.0.1.36:5000**. Choose **Manual Control**, refresh USB devices, select two *different* ports, and connect both. Send a command once or run independent count/duration loops; each loop waits for `OK`. Stop sends `s`.

## Automatic Position Test

Switch to **Automatic Position Test**. Set step (default `1000`), maximum position (`20000`), and OK timeout (`30` seconds). Confirm clear travel and press **Start Position Test**. The test sends A1 `<`, then A1 `P1000`, A2 `<`, A2 `>`, then A1 `P2000`, etc., through `P20000`; finally A1 `>` and one last A2 `<`, A2 `>` cycle. Every command waits for `OK`. **Stop Both** sends `s` to both channels; errors/timeouts also attempt to stop both. Manual commands are blocked during the test. Live progress and logs appear on the page.

The original CLI sweep is also available: `python actuator_position_test.py --dry-run` or run with `--port1 /dev/ttyUSB0 --port2 /dev/ttyUSB1 --timeout 30` **after stopping the web server**.

**Safety:** Test only with clear travel, correct USB port assignments, and a physical emergency stop. `OK` must indicate motion completion, not mere command receipt. This LAN-only site has no authentication; do not expose it to the internet. Software/USB/network stopping is not safety-rated.
