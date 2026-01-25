# Configuration Reference

Complete reference for all configuration options in `config.yaml`.

## Configuration File Location

**Default:** `config.yaml` in the current working directory

**Custom Location:**
```bash
export FRM_CONFIG_FILE=/path/to/custom-config.yaml
```

## Full Configuration Example

```yaml
version: 1

serial:
  port: /dev/ttyUSB0
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

## Configuration Sections

### `version`

**Type:** `integer`  
**Default:** `1`  
**Description:** Configuration schema version. Reserved for future use when breaking changes occur.

```yaml
version: 1
```

---

### `serial` - Serial Port Settings

Controls communication with the Fluid Rower device.

#### `serial.port`

**Type:** `string`  
**Default:** `/dev/ttyUSB0`  
**Description:** Serial port path for the Fluid Rower connection.

**Common Values:**
- Linux: `/dev/ttyUSB0`, `/dev/ttyACM0`
- macOS: `/dev/cu.usbserial-*`
- Windows: `COM3`, `COM4`, etc.

```yaml
serial:
  port: /dev/ttyUSB0
```

**Environment Variable:**
```bash
export FRM_SERIAL__PORT=/dev/ttyUSB1
```

#### `serial.baudrate`

**Type:** `integer`  
**Default:** `9600`  
**Description:** Baud rate for serial communication. Should match your Fluid Rower's settings.

```yaml
serial:
  baudrate: 9600
```

**Typical Values:** `9600`, `19200`, `38400`, `115200`

#### `serial.timeout_secs`

**Type:** `float`  
**Default:** `2.0`  
**Description:** Read timeout in seconds for serial operations.

```yaml
serial:
  timeout_secs: 2.0
```

**Recommendations:**
- Increase for slower/unstable connections: `5.0`
- Decrease for fast connections: `1.0`

---

### `data` - Data Storage Settings

Controls where and how session data is stored.

#### `data.dir`

**Type:** `string`  
**Default:** `rowing_sessions`  
**Description:** Directory path for storing session files (relative or absolute).

```yaml
data:
  dir: rowing_sessions
```

**Examples:**
```yaml
# Relative path
data:
  dir: ./my_sessions

# Absolute path
data:
  dir: /home/user/rowing_data

# Windows path
data:
  dir: C:\Users\username\Documents\rowing_sessions
```

**Environment Variable:**
```bash
export FRM_DATA__DIR=/path/to/sessions
```

---

### `logging` - Logging Settings

Controls application logging verbosity.

#### `logging.level`

**Type:** `string`  
**Default:** `INFO`  
**Description:** Log level for application output.

**Valid Values:** `DEBUG`, `INFO`, `WARN`, `ERROR`, `CRITICAL`

```yaml
logging:
  level: INFO
```

**Recommendations:**
- Production: `INFO`
- Troubleshooting: `DEBUG`
- Minimal output: `WARN`

**Environment Variable:**
```bash
export FRM_LOGGING__LEVEL=DEBUG
```

---

### `reconnect` - Connection Resilience Settings

Controls automatic reconnection and data protection behavior.

#### `reconnect.max_attempts`

**Type:** `integer`  
**Default:** `5`  
**Minimum:** `1`  
**Description:** Maximum number of reconnection attempts after connection loss.

```yaml
reconnect:
  max_attempts: 5
```

**Recommendations:**
- Stable connections: `3-5`
- Unstable connections: `10-15`
- Quick failure: `1-2`

**Environment Variable:**
```bash
export FRM_RECONNECT__MAX_ATTEMPTS=10
```

#### `reconnect.backoff_secs`

**Type:** `float`  
**Default:** `0.5`  
**Minimum:** `0.0`  
**Description:** Delay in seconds between reconnection attempts.

```yaml
reconnect:
  backoff_secs: 0.5
```

**Recommendations:**
- Quick retry: `0.1-0.5`
- Standard: `0.5-1.0`
- Conservative: `2.0-5.0`

**Environment Variable:**
```bash
export FRM_RECONNECT__BACKOFF_SECS=1.0
```

#### `reconnect.flush_interval_secs`

**Type:** `float`  
**Default:** `60.0`  
**Minimum:** `1.0`  
**Description:** Time interval in seconds for automatic session data flushing to disk.

```yaml
reconnect:
  flush_interval_secs: 60.0
```

**Protects Against:**
- Connection loss
- Application crashes
- Power failures

**Recommendations:**
- Maximum safety: `30.0`
- Balanced: `60.0`
- Performance: `120.0` or higher

**Trade-offs:**
- Lower values = more disk writes, better protection
- Higher values = fewer disk writes, less protection

**Environment Variable:**
```bash
export FRM_RECONNECT__FLUSH_INTERVAL_SECS=30.0
```

#### `reconnect.flush_after_strokes`

**Type:** `integer`  
**Default:** `10`  
**Minimum:** `1`  
**Description:** Number of strokes after which to flush session data to disk.

```yaml
reconnect:
  flush_after_strokes: 10
```

**Recommendations:**
- Maximum safety: `5`
- Balanced: `10-20`
- Performance: `50` or higher

**Note:** Whichever trigger (`flush_interval_secs` or `flush_after_strokes`) happens first will trigger a flush.

**Environment Variable:**
```bash
export FRM_RECONNECT__FLUSH_AFTER_STROKES=5
```

---

## Environment Variable Override System

All configuration settings can be overridden via environment variables.

### Naming Convention

**Prefix:** `FRM_`  
**Nesting:** Use double underscores (`__`) for nested settings  
**Case:** Uppercase

### Examples

```bash
# Serial settings
export FRM_SERIAL__PORT=/dev/ttyUSB1
export FRM_SERIAL__BAUDRATE=115200
export FRM_SERIAL__TIMEOUT_SECS=3.0

# Data settings
export FRM_DATA__DIR=/custom/path

# Logging settings
export FRM_LOGGING__LEVEL=DEBUG

# Reconnect settings
export FRM_RECONNECT__MAX_ATTEMPTS=10
export FRM_RECONNECT__BACKOFF_SECS=1.0
export FRM_RECONNECT__FLUSH_INTERVAL_SECS=30.0
export FRM_RECONNECT__FLUSH_AFTER_STROKES=5
```

### Priority Order

Settings are loaded in this priority (highest to lowest):

1. **Environment Variables** (`FRM_*`)
2. **Config File** (`config.yaml` or `FRM_CONFIG_FILE`)
3. **Default Values**

## Validation

All configuration values are validated on load:

- **Type checking:** Values must match expected types
- **Range validation:** Numeric values respect minimum/maximum constraints
- **Required fields:** Missing required fields cause errors

**Example Validation Error:**

```
pydantic_core._pydantic_core.ValidationError: 1 validation error for AppSettings
reconnect.max_attempts
  Input should be greater than or equal to 1 [type=greater_than_equal]
```

## Configuration Best Practices

1. **Start with Defaults:**
   - Copy `config.example.yaml`
   - Only change what you need

2. **Test Changes Incrementally:**
   - Change one setting at a time
   - Verify behavior before additional changes

3. **Document Custom Settings:**
   - Add comments to your `config.yaml`
   - Note why you changed from defaults

4. **Use Environment Variables for:**
   - Temporary overrides
   - Testing different values
   - CI/CD deployments

5. **Keep Sensitive Data Separate:**
   - Use environment variables for paths
   - Don't commit `config.yaml` with personal paths

## Troubleshooting Configuration

### View Active Configuration

```python
from fluid_rower_monitor.settings import load_settings

settings = load_settings()
print(settings.model_dump_json(indent=2))
```

### Verify Config File Syntax

```bash
python -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

### Check Environment Variables

```bash
env | grep FRM_
```

### Reset to Defaults

```bash
# Unset all overrides
unset $(env | grep ^FRM_ | cut -d= -f1)

# Remove custom config
rm config.yaml

# Use defaults
uv run python -m fluid_rower_monitor.serial_conn
```
