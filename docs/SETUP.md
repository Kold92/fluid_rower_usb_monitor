# Setup Guide

## Prerequisites

- Python 3.8 or later
- A Fluid Rower with USB serial connection
- Linux, macOS, or Windows operating system

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/kold/fluid_rower_usb_monitor.git
cd fluid_rower_usb_monitor
```

### 2. Install Dependencies

Using `uv` (recommended):

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies
uv sync --extra dev
```

Or using pip:

```bash
pip install -e .
```

### 3. Identify Your Serial Port

Connect your Fluid Rower to your computer via USB.

**Linux/macOS:**
```bash
ls /dev/tty*
# Look for /dev/ttyUSB0, /dev/ttyACM0, or similar
```

**Windows:**
```powershell
# Check Device Manager → Ports (COM & LPT)
# Look for COM3, COM4, etc.
```

### 4. Create Configuration File

Copy the example configuration:

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml` with your serial port:

```yaml
version: 1
serial:
  port: /dev/ttyUSB0  # Change this to your port
  baudrate: 9600
  timeout_secs: 2.0
data:
  dir: rowing_sessions
logging:
  level: INFO
reconnect:
  max_attempts: 5
  backoff_secs: 0.5
  flush_interval_secs: 60.0
  flush_after_strokes: 10
```

## First Connection Test

### 1. Run the Monitor

```bash
uv run python -m fluid_rower_monitor.serial_conn
# Or if installed: fluid-rower-monitor
```

### 2. Expected Output

You should see:

```
Connected to /dev/ttyUSB0
[Attempt 1/20] Sent connection request 'C'
✓ Successfully connected to the device v5!
New rowing session started. Saving to: rowing_sessions/2026-01-25_10-30-45.parquet
```

### 3. Start Rowing

Begin rowing on your Fluid Rower. You should see live stats:

```
Distance: 10m | Duration: 1s | Avg 500m: 139.0s | Avg Power: 129W | SPM: 22
Distance: 20m | Duration: 3s | Avg 500m: 138.5s | Avg Power: 131W | SPM: 23
...
```

### 4. End Session

Press `Ctrl+C` to stop recording. You'll see a session summary:

```
Session ended by user.

=== Session Summary ===
Total strokes: 50
Total distance: 500.0m
Total duration: 120s
Mean 500m pace: 140.2s
Mean power: 135W
Total calories: 7440/hr
Session saved to: rowing_sessions/2026-01-25_10-30-45.parquet
```

## Troubleshooting

If you encounter issues:

1. **Permission denied on Linux:**
   ```bash
   sudo usermod -a -G dialout $USER
   # Log out and back in
   ```

2. **Connection timeout:**
   - Verify the correct serial port in `config.yaml`
   - Check that the Fluid Rower is powered on
   - Try unplugging and reconnecting the USB cable

3. **See the full [Troubleshooting Guide](TROUBLESHOOTING.md)**

## Next Steps

- Read the [Usage Guide](USAGE.md) to learn about all features
- Check the [Configuration Reference](CONFIGURATION.md) for advanced settings
- Review [Troubleshooting](TROUBLESHOOTING.md) for common issues
