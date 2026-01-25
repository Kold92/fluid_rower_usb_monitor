# Troubleshooting Guide

## Connection Issues

### Cannot Connect to Device

**Symptoms:**
```
✗ Failed to connect to device after max attempts
```

**Solutions:**

1. **Verify Serial Port:**
   - Linux/macOS: `ls /dev/tty*` and look for your device
   - Windows: Check Device Manager → Ports
   - Update `serial.port` in `config.yaml`

2. **Check Permissions (Linux):**
   ```bash
   # Add your user to the dialout group
   sudo usermod -a -G dialout $USER
   # Log out and back in for changes to take effect
   ```

3. **Verify Rower is Powered On:**
   - Ensure the Fluid Rower display is active
   - Try pressing buttons on the rower to wake it up

4. **Try Different USB Port:**
   - Some USB ports may have power issues
   - Try a different port on your computer

5. **Check USB Cable:**
   - Use a data-capable cable (not charge-only)
   - Try a different cable if available

### Connection Drops Frequently

**Symptoms:**
```
Serial read error: device reports readiness to read but returned no data
```

**Solutions:**

1. **Check USB Cable Quality:**
   - Replace with a shorter, higher-quality cable
   - Avoid USB hubs; connect directly to computer

2. **Reduce Power Management (Linux):**
   ```bash
   # Disable USB autosuspend for your device
   echo -1 | sudo tee /sys/bus/usb/devices/*/power/autosuspend
   ```

3. **Increase Flush Frequency:**
   ```yaml
   reconnect:
     flush_interval_secs: 30.0  # Flush more often
     flush_after_strokes: 5     # Flush more frequently
   ```

4. **Check System Resources:**
   - Close other applications using the serial port
   - Monitor CPU usage during sessions

### Reconnection Fails

**Symptoms:**
```
Failed to reconnect; ending session.
```

**Solutions:**

1. **Increase Reconnect Attempts:**
   ```yaml
   reconnect:
     max_attempts: 10  # Try more times
     backoff_secs: 1.0  # Wait longer between attempts
   ```

2. **Manually Reset Connection:**
   - Unplug USB cable
   - Wait 5 seconds
   - Plug back in
   - Restart the monitor

3. **Check for Hardware Issues:**
   - Test with a different USB cable
   - Try on a different computer if possible

## Data Issues

### No Data Recorded

**Symptoms:**
```
No data recorded in session.
```

**Solutions:**

1. **Ensure You're Rowing:**
   - The monitor only records data when you're actively rowing
   - First stroke establishes baseline; data starts from second stroke

2. **Check Reset Success:**
   ```
   Failed to reset session.
   ```
   - If reset fails, disconnect and reconnect the rower
   - Restart the monitor application

### Missing Strokes in Data

**Symptoms:**
- Stroke count seems lower than expected

**Solutions:**

1. **Review Pause Statistics:**
   - Check session summary for interruptions
   - High pause counts indicate connection issues

2. **Check Flush Messages:**
   - Look for "Partial session flushed" messages
   - Indicates data was saved before disconnection

3. **Verify Data File:**
   ```python
   import pandas as pd
   df = pd.read_parquet("rowing_sessions/2026-01-25_10-30-45.parquet")
   print(f"Rows in file: {len(df)}")
   ```

### Incorrect Pace/Power Values

**Symptoms:**
- Unrealistic power readings (too high or too low)
- Negative deltas or strange pace values

**Possible Causes:**

1. **Connection Reset During Stroke:**
   - When connection drops, cumulative state resets
   - First stroke after reconnect may show large delta
   - This is expected behavior for data integrity

2. **Device Reporting Issue:**
   - Some devices may send incorrect data occasionally
   - Check raw data file for anomalies

## Configuration Issues

### Config File Not Found

**Symptoms:**
```
# Uses defaults even though config.yaml exists
```

**Solutions:**

1. **Check File Location:**
   - Config file must be named `config.yaml`
   - Must be in the current working directory
   - Or specify path: `export FRM_CONFIG_FILE=/path/to/config.yaml`

2. **Verify YAML Syntax:**
   ```bash
   # Check for syntax errors
   python -c "import yaml; yaml.safe_load(open('config.yaml'))"
   ```

### Settings Not Applied

**Symptoms:**
- Changed settings in config.yaml but behavior unchanged

**Solutions:**

1. **Restart the Application:**
   - Configuration is loaded at startup
   - Changes require restart to take effect

2. **Check Environment Variables:**
   - Environment variables override config file
   - Unset any `FRM_*` variables if not needed:
     ```bash
     unset FRM_SERIAL__PORT
     ```

3. **Validate Configuration:**
   ```python
   from fluid_rower_monitor.settings import load_settings
   settings = load_settings()
   print(settings.model_dump_json(indent=2))
   ```

## Performance Issues

### High CPU Usage

**Solutions:**

1. **Reduce Polling Frequency:**
   - This is typically not adjustable
   - Consider closing other applications

2. **Check for Infinite Loops:**
   - Look for repeated "Reconnect attempt" messages
   - May indicate configuration issue

### Slow Session Saves

**Solutions:**

1. **Reduce Flush Frequency:**
   ```yaml
   reconnect:
     flush_interval_secs: 120.0  # Flush less often
     flush_after_strokes: 20     # Flush after more strokes
   ```

2. **Check Disk Space:**
   ```bash
   df -h  # Check available space
   ```

3. **Use SSD if Available:**
   - Move `data.dir` to SSD for faster writes

## Error Messages

### `ModuleNotFoundError`

**Error:**
```
ModuleNotFoundError: No module named 'fluid_rower_monitor'
```

**Solution:**
```bash
# Reinstall the package
uv sync --extra dev
# Or
pip install -e .
```

### `serial.SerialException: [Errno 13] Permission denied`

**Solution (Linux):**
```bash
sudo usermod -a -G dialout $USER
# Log out and log back in
```

### `ValidationError` on Config

**Error:**
```
pydantic_core._pydantic_core.ValidationError: ...
```

**Solution:**
- Check config.yaml for invalid values
- Ensure numeric fields are numbers, not strings
- Verify required fields are present

## Getting Help

If you've tried the above solutions and still have issues:

1. **Check Existing Issues:**
   - Visit: https://github.com/kold/fluid_rower_usb_monitor/issues
   - Search for similar problems

2. **Create a New Issue:**
   - Include your configuration (remove sensitive data)
   - Provide full error output
   - Specify your OS and Python version
   - Describe steps to reproduce

3. **Debug Mode:**
   ```yaml
   logging:
     level: DEBUG
   ```
   - Provides more detailed output
   - Include debug logs when reporting issues
