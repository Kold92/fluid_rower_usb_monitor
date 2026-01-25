# Usage Guide

## Recording a Session

### Starting a Session

1. Ensure your Fluid Rower is connected via USB
2. Run the monitor:
   ```bash
   uv run python -m fluid_rower_monitor.serial_conn
   ```
3. Wait for the connection confirmation
4. Begin rowing

### During a Session

**Live Statistics Display:**

The monitor shows real-time metrics as you row:

```
Distance: 250m | Duration: 60s | Avg 500m: 140.0s | Avg Power: 130W | SPM: 22
```

- **Distance:** Total meters rowed in the session
- **Duration:** Total active rowing time (excludes pauses)
- **Avg 500m:** Average pace per 500 meters in seconds
- **Avg Power:** Average power output in watts
- **SPM:** Current strokes per minute

**Automatic Flushing:**

The session is automatically saved periodically:
- Every 60 seconds (configurable via `flush_interval_secs`)
- Every 10 strokes (configurable via `flush_after_strokes`)

This protects your data if the connection is lost or the program crashes.

### Ending a Session

Press `Ctrl+C` to stop recording. The final session summary displays:

```
=== Session Summary ===
Total strokes: 120
Total distance: 1000.0m
Total duration: 300s
Mean 500m pace: 150.0s
Mean power: 125W
Total calories: 8880/hr
Session saved to: rowing_sessions/2026-01-25_10-30-45.parquet
```

## Connection Resilience

### Disconnections

If the connection is lost during a session:

1. **Automatic Pause:** The session pauses immediately
2. **Data Protection:** Partial data is flushed to disk
3. **Reconnection Attempts:** The monitor tries to reconnect (up to `max_attempts`)
4. **Resume or End:** 
   - If reconnection succeeds: Session resumes with a notification
   - If reconnection fails: Session ends with data saved

**Example Output:**

```
Serial read error: device reports readiness to read but returned no data
Partial session flushed (45 strokes)
Reconnect attempt 1 failed: [Errno 2] could not open port /dev/ttyUSB0
Reconnect attempt 2 failed: [Errno 2] could not open port /dev/ttyUSB0
✓ Successfully connected to the device v5!
Session resumed after reconnection.
```

### Pause Statistics

If your session had disconnections, the summary shows pause information:

```
=== Session Summary ===
...
Total pause time: 15.3s (2 interruptions)
Session saved to: rowing_sessions/2026-01-25_10-30-45.parquet
```

**Note:** Pause time is excluded from total session duration.

## Session Data

### Storage Location

Sessions are saved as Parquet files in the `rowing_sessions/` directory (configurable via `data.dir`).

**Filename Format:** `YYYY-MM-DD_HH-MM-SS.parquet`

Example: `2026-01-25_10-30-45.parquet`

### Data Structure

Each session file contains per-stroke data:

| Column | Description |
|--------|-------------|
| `stroke_distance_m` | Distance covered in this stroke (meters) |
| `stroke_duration_secs` | Time taken for this stroke (seconds) |
| `time_500m_secs` | Current 500m pace (seconds) |
| `strokes_per_min` | Current stroke rate |
| `power_watts` | Power output for this stroke (watts) |
| `calories_per_hour` | Current calorie burn rate |
| `resistance_level` | Resistance level setting |

### Reading Session Data

Using Python:

```python
import pandas as pd

# Load a session
df = pd.read_parquet("rowing_sessions/2026-01-25_10-30-45.parquet")

# View first 5 strokes
print(df.head())

# Calculate total distance
total_distance = df["stroke_distance_m"].sum()
print(f"Total distance: {total_distance}m")

# Plot power over time
import matplotlib.pyplot as plt
df["power_watts"].plot()
plt.show()
```

## Analyzing Sessions

### Using the Built-in Analyzer

```python
from fluid_rower_monitor.rowing_analyzer import RowingAnalyzer
from pathlib import Path

# Analyze a session file
session_file = Path("rowing_sessions/2026-01-25_10-30-45.parquet")
stats = RowingAnalyzer.get_historical_stats(session_file)

print(f"Strokes: {stats.num_strokes}")
print(f"Distance: {stats.total_distance_m}m")
print(f"Mean power: {stats.mean_power_watts}W")
```

### Comparing Sessions

```python
from fluid_rower_monitor.rowing_analyzer import RowingAnalyzer

session1 = Path("rowing_sessions/2026-01-25_10-30-45.parquet")
session2 = Path("rowing_sessions/2026-01-26_10-15-30.parquet")

comparison = RowingAnalyzer.compare_sessions(session1, session2)

print(f"Distance improvement: {comparison.distance_diff_m}m")
print(f"Power improvement: {comparison.power_diff_watts}W")
```

### Analyzing All Sessions

```python
from fluid_rower_monitor.rowing_data import RowingSession

# Get aggregate statistics across all sessions
all_stats = RowingSession.analyze_all_sessions()

print(f"Total sessions: {all_stats.total_sessions}")
print(f"Total strokes: {all_stats.total_strokes}")
print(f"Total distance: {all_stats.total_distance_m}m")
print(f"All-time max power: {all_stats.max_watts_all_time}W")
```

## Environment Variable Overrides

Any setting can be overridden via environment variables using the `FRM_` prefix:

```bash
# Override serial port
export FRM_SERIAL__PORT=/dev/ttyUSB1

# Override flush interval
export FRM_RECONNECT__FLUSH_INTERVAL_SECS=30.0

# Run with overrides
uv run python -m fluid_rower_monitor.serial_conn
```

**Nested settings use double underscores (`__`).**

## Tips for Best Results

1. **Ensure Stable Connection:** Use a quality USB cable and avoid moving it during sessions
2. **Regular Flushes:** Keep default flush settings for data safety
3. **Monitor Disk Space:** Session files accumulate over time; consider periodic cleanup
4. **Backup Sessions:** Copy important session files to backup storage
5. **Review Pause Stats:** High pause counts may indicate connection issues
