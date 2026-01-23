# Fluid Rower USB Monitor - Feature Roadmap

## Current Features
- ✅ Serial communication with Fluid Rower device
- ✅ Real-time session recording
- ✅ Per-stroke data storage (parquet format)
- ✅ Live statistics display
- ✅ Session analysis and comparison
- ✅ Multi-session aggregation

---

## Phase 1: Core Analytics (Priority: High)
### Data Visualization
- [ ] Plot watts over time during session
- [ ] Plot 500m pace over time
- [ ] Plot stroke rate progression
- [ ] Histogram of power distribution
- [ ] Distance vs time graph (rowing curve)

### Session Insights
- [ ] Best split time (fastest 500m)
- [ ] Power curve analysis (watts vs time)
- [ ] Consistency metrics (std dev of watts, pace)
- [ ] Personal records tracking (fastest 500m, max watts, etc.)
- [ ] Estimated 2km time based on current pace

### Progress Tracking
- [ ] Weekly/monthly statistics
- [ ] Performance trends (improving/declining metrics)
- [ ] Goal setting and progress toward goals
- [ ] Workout history by date

---

## Phase 2: User Interface (Priority: High)
### CLI Improvements
- [ ] Interactive menu system
- [ ] Session browser/selector
- [ ] Real-time dashboard during rowing
- [ ] Session details viewer

### Web Dashboard (Stretch Goal)
- [ ] Flask/FastAPI web server
- [ ] Interactive graphs (Plotly/Matplotlib)
- [ ] Session browsing interface
- [ ] Performance comparisons
- [ ] Export reports (PDF, CSV)

### Desktop GUI (Future)
- [ ] PyQt/Tkinter application
- [ ] Live monitoring interface
- [ ] Session management UI
- [ ] Settings configuration

---

## Phase 3: Advanced Features (Priority: Medium)
### Data Export
- [ ] CSV export with all session data
- [ ] PDF reports with graphs and statistics
- [ ] Strava integration (upload workouts)
- [ ] Apple Health integration

### Workout Plans
- [ ] Interval workout support
- [ ] Target pace/wattage workouts
- [ ] Workout templates
- [ ] Real-time feedback on target achievement

### Competitive Features
- [ ] Leaderboards (personal PRs)
- [ ] Workout sharing
- [ ] Compare with other users (anonymized)
- [ ] Challenges/competitions

---

## Phase 4: Device Integration (Priority: Medium)
### Heart Rate Support
- [ ] Parse and store heart rate data
- [ ] Heart rate zones analysis
- [ ] VO2 max estimation
- [ ] Heart rate variability tracking

### Resistance Level Optimization
- [ ] Analyze power output at different resistance levels
- [ ] Recommendations for optimal resistance
- [ ] Power curve by resistance

### Multi-Device Support
- [ ] Support for different Fluid Rower models (4, 7, 16, 20 level)
- [ ] Rowing machine compatibility (other brands)
- [ ] Erging machine support

---

## Phase 5: Machine Learning & Insights (Priority: Low)
### Predictive Analytics
- [ ] Predict future performance based on training
- [ ] Injury risk assessment (unusual patterns)
- [ ] Optimal training recommendations
- [ ] Fatigue detection

### Smart Features
- [ ] Auto-detect session type (steady, intervals, sprint)
- [ ] Anomaly detection (unusual power drops, pace changes)
- [ ] Performance plateaus and breakthrough moments

---

## Phase 6: Testing & Documentation (Priority: High)
### Testing
- [ ] Unit tests for data decoder
- [ ] Integration tests with mock serial data
- [ ] Data validation tests
- [ ] Performance tests (large datasets)

### Documentation
- [ ] API documentation (docstrings)
- [ ] Developer guide
- [ ] Architecture documentation
- [ ] Protocol documentation (Fluid Rower serial format)

---

## Phase 7: Performance & Optimization (Priority: Low)
### Efficiency
- [ ] Optimize parquet read/write for large datasets
- [ ] Lazy loading for historical data
- [ ] Caching mechanisms
- [ ] Database option for real-time streaming

### Robustness
- [ ] Better error handling and recovery
- [ ] Reconnection logic for serial drops
- [ ] Data corruption recovery
- [ ] Backup mechanisms

---

## Known Limitations / To Address
- [ ] No validation of received serial data ranges
- [ ] No handling of corrupted/dropped packets
- [ ] Serial connection recovery is basic
- [ ] No real-time plotting (currently just text output)
- [ ] Single device support only
- [ ] No user authentication/profiles (multi-user)

---

## Tech Stack Ideas
- **Web Dashboard**: Flask + Plotly/D3.js
- **Desktop GUI**: PyQt6 or Tkinter
- **Database**: SQLite (if needed for performance)
- **Graphing**: Matplotlib, Seaborn, Plotly
- **Testing**: pytest, pytest-cov
- **Documentation**: Sphinx, MkDocs
- **CI/CD**: GitHub Actions

---

## Success Metrics
- Real-time visualization of rowing session
- Ability to analyze 100+ sessions quickly (<1s)
- Accurate per-stroke data capture
- User can track personal improvements over time
- Extensible architecture for future device support
