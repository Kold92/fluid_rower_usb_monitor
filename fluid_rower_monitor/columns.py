"""Column names for rowing data - centralized constants to avoid magic strings."""

# RowingDataPoint DataFrame column names (per-stroke data)
STROKE_DISTANCE_M = "stroke_distance_m"
STROKE_DURATION_SECS = "stroke_duration_secs"
TIME_500M_SECS = "time_500m_secs"
STROKES_PER_MIN = "strokes_per_min"
POWER_WATTS = "power_watts"
CALORIES_PER_HOUR = "calories_per_hour"
RESISTANCE_LEVEL = "resistance_level"

# Tuple of all column names for easy reference
ALL_COLUMNS = (
    STROKE_DISTANCE_M,
    STROKE_DURATION_SECS,
    TIME_500M_SECS,
    STROKES_PER_MIN,
    POWER_WATTS,
    CALORIES_PER_HOUR,
    RESISTANCE_LEVEL,
)
