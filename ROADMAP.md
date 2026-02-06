# Fluid Rower USB Monitor - Feature Roadmap

## Current Features
- ✅ Serial communication with Fluid Rower device
- ✅ Real-time session recording
- ✅ Per-stroke data storage (parquet format)
- ✅ Live statistics display
- ✅ FastAPI backend (REST + WebSocket)
- ✅ Web dashboard with live charts
- ✅ Session analysis and comparison
- ✅ Multi-session aggregation
- ✅ Basic README and project structure

---

## Phase 1: Testing Infrastructure & Foundation ✅ COMPLETE
### Testing Setup ✅
- ✅ pytest framework setup
- ✅ tox automation for test environments
- ✅ flake8 linting configuration
- ✅ pytest-cov for coverage reporting
- ⏸️ GitHub Actions CI/CD pipeline (deferred)
- ✅ Initial unit tests for decoder
- ✅ Unit tests for data models
- ✅ Unit tests for analyzer functions
- ✅ Target: >80% code coverage (93 tests, coverage achieved)

### Configuration & Setup ✅
- ✅ Configuration file (YAML with pydantic validation)
- ✅ Configuration schema validation
- ✅ Environment variable overrides (FRM_ prefix)
- ⏸️ Auto-discover serial port (deferred)
- ⏸️ Multi-user support (user profiles) (deferred)
- ⏸️ Default config generation on first run (deferred)

### Versioning & Data Durability
- ⏸️ Application version numbering (semantic versioning) (deferred)
- ✅ Schema version tracking in saved data
- ✅ Data migration framework for breaking changes
- ✅ Migration script examples and documentation

---

## Phase 1.5: Connection Resilience Analysis & Critical Risk Mitigation ✅ COMPLETE
### Risk Analysis ✅
- ✅ Analyze connection failure scenarios
- ✅ Identify critical vs. important vs. nice-to-have fixes
- ✅ Document failure modes and recovery strategies

### Critical Implementations ✅
- ✅ Graceful reconnection during active session (with exponential backoff)
- ✅ Session buffer storage to disk periodically (configurable time/stroke intervals)
- ✅ Connection loss detection
- ✅ Graceful pause on disconnection (pause tracking in session data)
- ✅ Resume session capability after reconnection

### Testing ✅
- ✅ Unit tests for reconnection logic (11 new tests)
- ✅ Simulate connection loss scenarios
- ✅ Verify data integrity after reconnection (partial save with append mode)

---

## Phase 1.6: Documentation ✅ COMPLETE
### User Documentation ✅
- ✅ Setup guide (installation, first connection) - docs/SETUP.md
- ✅ How to record your first session - docs/USAGE.md
- ✅ Troubleshooting guide - docs/TROUBLESHOOTING.md
- ✅ Configuration options explained - docs/CONFIGURATION.md

### Developer Documentation ✅
- ✅ Architecture overview - docs/DEVELOPER.md
- ✅ Data model documentation - docs/DEVELOPER.md
- ✅ Schema versioning guide - docs/DEVELOPER.md (strategy documented)
- ✅ Contributing guidelines - docs/DEVELOPER.md
- ✅ Updated README with quick start and documentation links

---

## Phase 2: Minimal Viable UI (Priority: High)
### Core UI Features
- [ ] Setup/Configuration screen (UI preferences only today)
- [x] Start/Stop rowing session buttons
- [x] Live data display during rowing:
  - Current stroke data (distance, duration, watts, pace, SPM)
  - Total time elapsed
  - Total distance rowed
- [ ] Session summary on finish
- [x] Clean separation between UI and business logic

### Offline Mode
- [ ] Application can start without device connection
- [ ] UI gracefully handles "device not connected" state
- [ ] (Historical session loading deferred to Phase 7)

---

## Phase 3: Graphs & Visualization (Priority: High)
### Data Visualization
- [x] Real-time power graph during session
- [x] Real-time 500m pace visualization
- [x] Real-time stroke-rate visualization
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
- **Graphing**: Chart.js (frontend)
- **UI**: SvelteKit + Tailwind + Chart.js
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
