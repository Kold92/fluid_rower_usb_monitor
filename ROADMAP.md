# Fluid Rower USB Monitor - Feature Roadmap

## Current Features
- ✅ Serial communication with Fluid Rower device
- ✅ Real-time session recording
- ✅ Per-stroke data storage (parquet format)
- ✅ Live statistics display
- ✅ Session analysis and comparison
- ✅ Multi-session aggregation
- ✅ Basic README and project structure

---

## Phase 1: Testing Infrastructure & Foundation (Priority: CRITICAL)
### Testing Setup
- [ ] pytest framework setup
- [ ] tox automation for test environments
- [ ] flake8 linting configuration
- [ ] pytest-cov for coverage reporting
- [ ] GitHub Actions CI/CD pipeline
- [ ] Initial unit tests for decoder
- [ ] Unit tests for data models
- [ ] Unit tests for analyzer functions
- [ ] Target: >80% code coverage

### Configuration & Setup
- [ ] Configuration file (YAML/JSON)
- [ ] Auto-discover serial port
- [ ] Multi-user support (user profiles)
- [ ] Configuration schema validation
- [ ] Default config generation on first run

---

## Phase 2: Minimal Viable UI (Priority: High)
### Core UI Features
- [ ] Setup/Configuration screen
- [ ] Start/Stop rowing session buttons
- [ ] Live data display during rowing:
  - Current stroke data (distance, duration, watts, pace, SPM)
  - Total time elapsed
  - Total distance rowed
- [ ] Session summary on finish
- [ ] Clean separation between UI and business logic

---

## Phase 3: Graphs & Visualization (Priority: High)
### Data Visualization
- [ ] Real-time power graph during session
- [ ] Real-time 500m pace visualization
- [ ] Session summary: Power curve graph
- [ ] Session summary: Distance vs time graph
- [ ] Session summary: Pace distribution histogram

---

## Phase 4: Target Distance Mode (Priority: High)
### Workout Features
- [ ] Set distance goal (e.g., 5km)
- [ ] Progress bar/display
- [ ] Live distance remaining countdown
- [ ] Time-to-completion estimate
- [ ] Session summary after completion

---

## Phase 5: Target Row Time Mode (Priority: High)
### Workout Features
- [ ] Set time goal (e.g., 30 minutes)
- [ ] Live time remaining countdown
- [ ] Distance estimate at completion
- [ ] Progress visualization
- [ ] Session summary after completion

---

## Phase 6: Interval Workouts Mode (Priority: High)
### Workout Features
- [ ] Define interval structure (e.g., 5x500m, 10x1min)
- [ ] Rest period tracking and alerts
- [ ] Live interval progress display
- [ ] Performance metrics per interval
- [ ] Session summary with interval breakdown

---

## Phase 7: Session History & Browser (Priority: High)
### Session Management
- [ ] View list of all past sessions
- [ ] Browse session details (date, distance, time, avg pace, etc.)
- [ ] Filter/search sessions by date range
- [ ] Display session statistics
- [ ] Delete sessions

---

## Phase 8: Ghost Race Workout Mode (Priority: High)
### Workout Features
- [ ] Race against best previous session
  - Real-time offset display (ahead/behind by seconds/distance)
  - Visual indicators of progress
  - Live alerts (on pace, falling behind, pulling ahead)
- [ ] Race against fixed pace
  - User sets target pace (e.g., 2:15 per 500m)
  - Real-time comparison to target
  - Performance feedback

---

## Phase 9: Export Features (Priority: Medium)
### Data Export
- [ ] CSV export with all session data
- [ ] PDF session reports with graphs and statistics
- [ ] Data backup functionality

---

## Future Ideas / Out of Scope
- [ ] Power Target Mode (row at specific wattage with feedback)
- [ ] Heart rate support and zones
- [ ] Multi-device support (different rower models)
- [ ] Predictive analytics and ML insights
- [ ] Social features (leaderboards, workout sharing)
- [ ] Mobile app (native iOS/Android)
- [ ] Strava integration
- [ ] Apple Health integration

---

## Tech Stack
- **Testing**: pytest, pytest-cov, tox, flake8
- **Data Storage**: pandas, parquet (pyarrow)
- **Graphing**: Matplotlib or Plotly
- **UI**: TBD (Web/CLI/Desktop) - decided in Phase 2
- **CI/CD**: GitHub Actions

---

## Architecture Principles
- Clear separation between UI layer and business logic
- Business logic (decoder, analyzer, data models) UI-agnostic
- Enables easy switching between UI technologies in future
- Each phase should be independently testable

---

## Success Metrics
- Phase 2: Users can record a complete rowing session
- Phase 3: Users can visualize their performance
- Phase 4-6: Users have motivating workout modes
- Phase 7: Users can track long-term progress
- Phase 8: Users are engaged with competitive features
- By Phase 9: Comprehensive, usable application
- Clean, maintainable code (flake8 compliant)
