# Fluid Rower Monitor

A Python application to monitor and analyze rowing sessions from a Fluid Rower device via serial connection.

## Features

- **Serial Communication**: Connect to Fluid Rower via 9600 baud serial connection
- **Real-time Monitoring**: Live tracking of rowing metrics during sessions
- **Data Storage**: Parquet-based storage for efficient compression and fast analysis
- **Session Analysis**: Analyze individual sessions and compare across multiple sessions
- **Performance Tracking**: Track watts, pace, stroke rate, distance, and more

## Project Structure

- `serial_conn.py` - Serial communication and session recording
- `rowing_data.py` - Data models and storage (RowingSession, RowingDataPoint)
- `rowing_analyzer.py` - Analysis functions for live and historical data
- `rowing_sessions/` - Stored session data (parquet files)

## Requirements

- Python 3.8+
- `pyserial` - Serial communication
- `pandas` - Data manipulation
- `polars` - Fast data analysis
- `pyarrow` - Parquet file support

## Installation

```bash
pip install pyserial pandas polars pyarrow
```

## Usage

### Record a Rowing Session

```python
python serial_conn.py
```

The script will:
1. Connect to the rower via serial (default: `/dev/ttyUSB0`)
2. Record per-stroke data
3. Display live statistics
4. Save session to `rowing_sessions/YYYY-MM-DD_HH-MM-SS.parquet`

### Analyze Sessions

```python
from rowing_data import RowingSession
from rowing_analyzer import RowingAnalyzer

# Analyze a specific session
stats = RowingAnalyzer.get_historical_stats("rowing_sessions/2026-01-23_14-30-45.parquet")
print(f"Mean 500m pace: {stats['mean_time_500m_secs']:.1f}s")
print(f"Mean power: {stats['mean_power_watts']:.0f}W")
print(f"Total distance: {stats['total_distance_m']:.1f}m")

# Analyze all sessions
all_stats = RowingSession.analyze_all_sessions()
print(f"Total sessions: {all_stats['total_sessions']}")
print(f"Average watts (all time): {all_stats['avg_watts_all_time']:.0f}W")

# Compare two sessions
comparison = RowingAnalyzer.compare_sessions("sessions/session1.parquet", "sessions/session2.parquet")
```

## Device Protocol

The Fluid Rower sends data in fixed-width format:

```
A5 00001 00010 002 19 022 129 0744 09
```

- A5: Device type (16 level rower)
- 00001: Row duration (seconds)
- 00010: Row distance (meters)
- 002 19: 500m time (2:19)
- 022: Strokes per minute
- 129: Power (watts)
- 0744: Calories per hour
- 09: Resistance level
