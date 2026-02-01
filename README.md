# Fluid Rower Monitor

A Python application to monitor and analyze rowing sessions from a Fluid Rower device via serial connection.

## Features

- **Web Dashboard**: Real-time UI with live charts (power, stroke rate, split time)
- **API + WebSocket**: FastAPI backend for sessions, config, and live streaming
- **Real-time Monitoring**: Live tracking of rowing metrics (distance, power, pace, SPM)
- **Connection Resilience**: Automatic reconnection with data protection during disconnects
- **Data Protection**: Periodic auto-save every 60 seconds or 10 strokes
- **Pause/Resume Tracking**: Records connection interruptions with duration tracking
- **Session Analysis**: Analyze individual sessions and compare across multiple sessions
- **Flexible Configuration**: YAML config with environment variable overrides
- **Data Storage**: Parquet-based storage for efficient compression and fast analysis

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/kold/fluid_rower_usb_monitor.git
cd fluid_rower_usb_monitor

# Install with uv (recommended)
uv sync --extra dev

# Or with pip
pip install -e .
```

### First Session

```bash
# Copy example config
cp config.example.yaml config.yaml

# Edit config.yaml with your serial port
# Then start monitoring
uv run python -m fluid_rower_monitor.serial_conn
```

### Web Dashboard (API + UI)

```bash
# Start the API (production mode by default)
uv run fluid-rower-monitor-api

# Or use synthetic data
uv run fluid-rower-monitor-api --dev

# Start the frontend (in another terminal)
cd frontend
npm install
npm run dev
```

Open the UI at the printed dev server URL (usually http://localhost:5173).

## Documentation

- **[Setup Guide](docs/SETUP.md)** - Installation and first connection
- **[Usage Guide](docs/USAGE.md)** - Recording sessions, analyzing data
- **[Configuration Reference](docs/CONFIGURATION.md)** - All settings explained
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Developer Docs](docs/DEVELOPER.md)** - Architecture and contributing

## Project Structure

```
fluid_rower_monitor/
├── __init__.py           # Package exports
├── api/                  # FastAPI backend (REST + WebSocket)
├── columns.py            # Column name constants
├── rowing_data.py        # Data models and storage
├── rowing_analyzer.py    # Session analysis and comparison
├── serial_conn.py        # Serial communication and session loop
└── settings.py           # Configuration management
frontend/                 # SvelteKit UI
tests/                    # Comprehensive test suite
docs/                     # User and developer documentation
```

## Requirements

- Python 3.12+
- Serial connection to Fluid Rower device
- Node.js 18+ (for running the frontend)

## Key Dependencies

- `pyserial` - Serial communication
- `pandas` - Data manipulation
- `polars` - Fast data analysis
- `pyarrow` - Parquet file support
- `pydantic` - Configuration validation

## Session Example

```bash
$ uv run python -m fluid_rower_monitor.serial_conn

Connected to /dev/ttyUSB0
✓ Successfully connected to the device v5!
New rowing session started. Saving to: rowing_sessions/2026-01-25_10-30-45.parquet

Distance: 100m | Duration: 25s | Avg 500m: 125.0s | Avg Power: 135W | SPM: 22
Distance: 200m | Duration: 50s | Avg 500m: 125.0s | Avg Power: 136W | SPM: 23
...

^C
Session ended by user.

=== Session Summary ===
Total strokes: 120
Total distance: 1000.0m
Total duration: 300s
Mean 500m pace: 150.0s
Mean power: 125W
Total calories: 8880/hr
Session saved to: rowing_sessions/2026-01-25_10-30-45.parquet
```

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=fluid_rower_monitor --cov-report=html

# Run tox (multiple Python versions)
uv run tox
```

## Configuration Example

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
ui:
  x_axis_type: samples
  max_points: 30
```

## Analyzing Session Data

```python
from fluid_rower_monitor.rowing_data import RowingSession
from fluid_rower_monitor.rowing_analyzer import RowingAnalyzer
from pathlib import Path

# Analyze a specific session
session_file = Path("rowing_sessions/2026-01-25_10-30-45.parquet")
stats = RowingAnalyzer.get_historical_stats(session_file)
print(f"Mean 500m pace: {stats.mean_time_500m_secs:.1f}s")
print(f"Mean power: {stats.mean_power_watts:.0f}W")
print(f"Total distance: {stats.total_distance_m:.1f}m")

# Analyze all sessions
all_stats = RowingSession.analyze_all_sessions()
print(f"Total sessions: {all_stats.total_sessions}")
print(f"Average watts (all time): {all_stats.avg_watts_all_time:.0f}W")

# Compare two sessions
session1 = Path("rowing_sessions/2026-01-25_10-30-45.parquet")
session2 = Path("rowing_sessions/2026-01-26_11-15-30.parquet")
comparison = RowingAnalyzer.compare_sessions(session1, session2)
print(f"Power improvement: {comparison.power_diff_watts:.1f}W")
```

## Device Protocol

The Fluid Rower sends data in fixed-width format (29 characters):

```
A5000010001000219022129074409
```

Decoded as:

- **A5**: Device type (16-level rower)
- **00001**: Row duration (seconds, cumulative)
- **00010**: Row distance (meters, cumulative)
- **0**: Unused
- **02 19**: 500m time (2:19 = 139 seconds)
- **022**: Strokes per minute
- **129**: Power (watts)
- **0744**: Calories per hour
- **09**: Resistance level

## Contributing

See [DEVELOPER.md](docs/DEVELOPER.md) for architecture details and contribution guidelines.

## License

MIT License

## Roadmap

See [ROADMAP.md](ROADMAP.md) for planned features and development phases.
