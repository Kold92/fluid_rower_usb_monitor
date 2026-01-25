# Developer Documentation

## Architecture Overview

The Fluid Rower Monitor is designed with clear separation between business logic and interface layers, enabling future UI/CLI flexibility.

### Key Design Principles

1. **UI-Agnostic Core:** Business logic has no dependencies on presentation layer
2. **Testability:** All components are independently testable with high coverage
3. **Resilience:** Robust error handling with automatic reconnection and data protection
4. **Type Safety:** Pydantic models for configuration; dataclasses for data structures
5. **Data Durability:** Parquet format with periodic flushing for crash protection

### Component Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Interface Layer                     │
│  (serial_conn.py - CLI, future: web/desktop UI)     │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│                 Business Logic                       │
│  ┌─────────────────────────────────────────┐        │
│  │  rowing_data.py                         │        │
│  │  - Session management                   │        │
│  │  - Data point models                    │        │
│  │  - Persistence (Parquet)                │        │
│  │  - Pause/resume tracking                │        │
│  └─────────────────────────────────────────┘        │
│  ┌─────────────────────────────────────────┐        │
│  │  rowing_analyzer.py                     │        │
│  │  - Statistics calculation               │        │
│  │  - Session comparison                   │        │
│  │  - Aggregation                          │        │
│  └─────────────────────────────────────────┘        │
│  ┌─────────────────────────────────────────┐        │
│  │  settings.py                            │        │
│  │  - YAML + environment configuration     │        │
│  │  - Validation (Pydantic)                │        │
│  └─────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│              Hardware Interface                      │
│  (pyserial - Serial communication)                  │
└─────────────────────────────────────────────────────┘
```

## Module Reference

### `rowing_data.py`

**Core data models and session management.**

#### Data Models

- **`RowingDataPoint`:** Per-stroke data (distance, duration, power, etc.)
- **`RawRowingData`:** Cumulative device data before delta calculation
- **`SessionStats`:** Calculated statistics for a session
- **`AllSessionsStats`:** Aggregate statistics across all sessions

#### Classes

##### `RowingSession`

Manages a single rowing session with persistence and pause/resume tracking.

**Key Methods:**

- `add_point(point)`: Add a stroke to the session
- `save()`: Save complete session to Parquet
- `partial_save(from_index)`: Append partial data for crash protection
- `pause()`: Mark session as paused (disconnection)
- `resume()`: Resume after reconnection, tracking pause duration
- `get_stats()`: Get session statistics dictionary

**State Tracking:**

- `data_points`: List of all strokes
- `pauses`: List of (paused_at, resumed_at) tuples
- `total_pause_secs`: Cumulative pause duration
- `paused_at`: Current pause timestamp or None

**Static Methods:**

- `list_sessions(data_dir)`: Get all session files
- `load_session(filepath)`: Load session DataFrame
- `delete_session(filepath)`: Delete a session file
- `analyze_all_sessions(data_dir)`: Aggregate stats

---

### `rowing_analyzer.py`

**Statistical analysis and session comparison.**

#### Classes

##### `RowingAnalyzer`

Pure static class for data analysis.

**Methods:**

- `calculate_stats(df)`: Calculate SessionStats from DataFrame
- `get_live_stats(data_points)`: Real-time stats from list of RowingDataPoint
- `get_live_dataframe(data_points)`: Convert points to DataFrame
- `get_historical_stats(filepath)`: Load and analyze saved session
- `compare_sessions(file1, file2)`: Compare two sessions

**SessionComparison Output:**

```python
@dataclass
class SessionComparison:
    session1_stats: SessionStats
    session2_stats: SessionStats
    distance_diff_m: float       # Positive = session2 longer
    duration_diff_secs: float
    power_diff_watts: float      # Positive = session2 more powerful
    pace_diff_secs: float        # Positive = session2 slower
```

---

### `serial_conn.py`

**Serial communication and session orchestration.**

#### Functions

##### Connection Management

- `setup_serial(port, baudrate, timeout)`: Initialize serial connection
- `connect_to_device(ser)`: Handshake with device (send 'C', expect 'C' response)
- `reset_session(ser)`: Reset device counters (send 'R')
- `attempt_reconnect(settings)`: Retry connection with backoff

##### Data Processing

- `get_serial_response(ser, timeout)`: Read and decode serial data
- `decode_rowing_data(data)`: Parse device protocol to RawRowingData

##### Session Management

- `rowing_session(ser, settings)`: Main session loop with:
  - Stroke-by-stroke delta calculation
  - Live statistics display
  - Automatic periodic flushing
  - Reconnection on error
  - Pause/resume tracking
  - Graceful shutdown

##### Entry Point

- `main(settings)`: Application entry point

---

### `settings.py`

**Configuration management with validation.**

#### Models

- **`SerialSettings`:** Port, baudrate, timeout
- **`DataSettings`:** Storage directory
- **`LoggingSettings`:** Log level
- **`ReconnectSettings`:** Resilience parameters (attempts, backoff, flush triggers)
- **`AppSettings`:** Root settings container

#### Configuration Loading

**Priority:** Environment Variables > YAML File > Defaults

**YAML Source:**

```python
@staticmethod
def _yaml_config_settings_source() -> Dict[str, Any]:
    # Loads from FRM_CONFIG_FILE or config.yaml
```

**Environment Overrides:**

- Prefix: `FRM_`
- Nesting: `__` (e.g., `FRM_SERIAL__PORT`)

#### Helper Functions

```python
def load_settings(config_path: str | Path | None = None) -> AppSettings:
    """Load settings with optional explicit path."""
```

---

### `columns.py`

**Column name constants for data consistency.**

```python
STROKE_DISTANCE_M = "stroke_distance_m"
STROKE_DURATION_SECS = "stroke_duration_secs"
TIME_500M_SECS = "time_500m_secs"
STROKES_PER_MIN = "strokes_per_min"
POWER_WATTS = "power_watts"
CALORIES_PER_HOUR = "calories_per_hour"
RESISTANCE_LEVEL = "resistance_level"
```

**Purpose:** Avoid magic strings; enable IDE autocomplete.

---

## Data Model & Schema

### Stroke Data Pipeline

```
Device (Cumulative) → RawRowingData → Delta Calculation → RowingDataPoint → Parquet
```

1. **Device Protocol:** Fixed-width string format (29 chars)
   ```
   A5 00001 00010 002 19 022 129 0744 09
   ```

2. **RawRowingData:** Parsed cumulative values
   ```python
   RawRowingData(
       cumulative_duration_secs=1,
       cumulative_distance_m=10,
       ...
   )
   ```

3. **Delta Calculation:** Per-stroke values
   ```python
   stroke_distance = current.cumulative_distance_m - previous.cumulative_distance_m
   ```

4. **RowingDataPoint:** Stored per-stroke data
   ```python
   RowingDataPoint(
       stroke_distance_m=10.0,
       stroke_duration_secs=2.3,
       ...
   )
   ```

5. **Parquet Storage:** Column-oriented, efficient compression

### Schema Versioning Strategy

**Current Version:** 1 (implicit in schema)

**Future Versioning Plan:**

When breaking changes are needed:

1. **Add Schema Version to Parquet Metadata:**
   ```python
   df.to_parquet(filename, index=False, 
                 metadata={"schema_version": "2"})
   ```

2. **Migration Scripts:**
   ```python
   def migrate_v1_to_v2(filepath: Path) -> None:
       df = pd.read_parquet(filepath)
       # Transform data
       df["new_column"] = ...
       df.to_parquet(filepath, metadata={"schema_version": "2"})
   ```

3. **Versioned Loaders:**
   ```python
   def load_session_v1(filepath):
       # Old schema
   
   def load_session_v2(filepath):
       # New schema
   
   def load_session_auto(filepath):
       meta = pd.read_parquet(filepath, metadata_only=True).metadata
       version = meta.get("schema_version", "1")
       if version == "1":
           return load_session_v1(filepath)
       elif version == "2":
           return load_session_v2(filepath)
   ```

**Breaking Changes That Require Versioning:**

- Column renames
- Column type changes
- Removing columns
- Changing data representation (e.g., pace format)

**Non-Breaking Changes:**

- Adding new columns (old loaders ignore them)
- Metadata changes

---

## Testing Strategy

### Test Organization

```
tests/
├── test_rowing_data.py       # Data models, session persistence
├── test_rowing_analyzer.py   # Statistics, comparison, aggregation
├── test_serial_conn.py       # Protocol decoding (pure functions)
├── test_serial_conn_io.py    # I/O operations with mocks
├── test_settings.py          # Configuration loading, validation
└── test_resilience.py        # Pause/resume, partial saves, flush
```

### Testing Approach

**Unit Tests:**
- Mock external dependencies (serial port, filesystem)
- Test pure functions directly
- Verify edge cases and error handling

**Integration Tests:**
- Use temp directories for file operations
- Test end-to-end workflows
- Validate data persistence

**Mocking Strategy:**

```python
# Mock serial port
mock_ser = MagicMock()
mock_ser.in_waiting = 1
mock_ser.readline.return_value = b"A5 00001 00010..."

# Mock file system
with tempfile.TemporaryDirectory() as tmpdir:
    session = RowingSession(data_dir=tmpdir)
```

### Coverage Requirements

**Target:** >80% code coverage

**Run Coverage:**
```bash
uv run pytest --cov=fluid_rower_monitor --cov-report=html
```

**Critical Coverage:**
- Data models: 100%
- Configuration: 100%
- Protocol decoding: 100%
- Reconnection logic: 100%

---

## Resilience Mechanisms

### Connection Loss Handling

**Detection:**
- `serial.SerialException` during read
- `OSError` during read
- Timeout patterns (future)

**Response Flow:**

```
1. Detect error
2. Call session.pause()
3. Flush partial data (session.partial_save)
4. Close serial connection
5. Attempt reconnection (max_attempts, with backoff)
6. If success:
   - Reinitialize serial
   - Call session.resume()
   - Reset cumulative state (previous_data = None)
   - Continue session
7. If failure:
   - End session
   - Save final data
```

### Data Protection Layers

**Layer 1: Periodic Flush**
- Time-based: Every `flush_interval_secs`
- Count-based: Every `flush_after_strokes`
- Automatic append to existing file

**Layer 2: Disconnect Flush**
- Immediate flush on connection error
- Before reconnection attempts

**Layer 3: Final Save**
- On KeyboardInterrupt (Ctrl+C)
- On session end
- In `finally` block (guaranteed)

### State Management

**Cumulative State Reset:**

After reconnection, `previous_data = None` to avoid incorrect deltas:

```python
# Before disconnect: cumulative_distance = 100m
# After reconnect: cumulative_distance resets to 10m
# Without reset: delta = 10 - 100 = -90m (wrong!)
# With reset: skip first stroke, delta = 20 - 10 = 10m (correct)
```

**Pause Time Exclusion:**

Pause duration is tracked but excluded from session duration:

```python
active_duration = total_duration - total_pause_secs
```

---

## Contributing Guidelines

### Code Style

- **Line Length:** 120 characters
- **Formatter:** Black
- **Linter:** Flake8 (ignore E203, W503)
- **Type Hints:** Use throughout; support Python 3.8+

### Development Workflow

1. **Create Branch:**
   ```bash
   git checkout -b feature/your-feature
   ```

2. **Make Changes:**
   - Write code
   - Add tests
   - Update documentation

3. **Run Tests:**
   ```bash
   uv run pytest
   uv run flake8 fluid_rower_monitor tests --max-line-length=120 --ignore=E203,W503
   uv run tox  # Test multiple Python versions
   ```

4. **Commit:**
   ```bash
   git add .
   git commit -m "Add feature: description"
   ```

5. **Push & PR:**
   ```bash
   git push origin feature/your-feature
   # Create PR on GitHub
   ```

### Adding Features

**For New Data Fields:**

1. Add to `RowingDataPoint` dataclass
2. Update `decode_rowing_data()` parser
3. Add column constant to `columns.py`
4. Update tests
5. Document schema change (consider versioning)

**For New Configuration Options:**

1. Add to appropriate settings model
2. Update `config.example.yaml`
3. Add validation rules (Field with constraints)
4. Update `docs/CONFIGURATION.md`
5. Add tests

**For UI Layers:**

1. Keep business logic in core modules
2. Create new interface module (e.g., `web_ui.py`)
3. Import and use existing business logic
4. Don't couple UI to core

---

## Performance Considerations

### Parquet Format

**Advantages:**
- Columnar storage (efficient for analytics)
- Compression (smaller files)
- Fast reads for aggregate queries
- Wide ecosystem support

**Trade-offs:**
- Row-by-row appends are inefficient (need read-modify-write)
- Best for batch operations

**Optimization for Partial Saves:**

```python
# Read existing, append new, write all
df_existing = pd.read_parquet(filename)
df_new = pd.DataFrame(new_data)
df_combined = pd.concat([df_existing, df_new])
df_combined.to_parquet(filename)
```

**Future Optimization:**

- Consider append-optimized format (e.g., Delta Lake, Iceberg)
- Or keep partial data in memory/CSV buffer, finalize to Parquet on session end

### Memory Usage

**Current Approach:** In-memory accumulation

```python
self.data_points: list[RowingDataPoint] = []
```

**Memory Profile:**
- ~100 bytes per stroke
- 1000 strokes = ~100 KB
- 10,000 strokes = ~1 MB (reasonable)

**Scaling:** For extremely long sessions (hours), consider streaming to disk.

---

## Future Roadmap

See [ROADMAP.md](../ROADMAP.md) for full feature roadmap.

**Upcoming Phases:**

- **Phase 2:** Minimal UI (web/desktop)
- **Phase 3:** Visualization (graphs, charts)
- **Phase 4-6:** Workout modes (distance, time, intervals)
- **Phase 7:** Session browser and history
- **Phase 8:** Ghost race mode

**Technical Debt:**

- Refactor flush mechanism for better performance
- Add explicit schema versioning to Parquet files
- Implement logging framework (replace print statements)
- Add type stubs for pyserial
