"""Tests for serial_conn module - serial communication and data decoding."""

from fluid_rower_monitor.serial_conn import decode_rowing_data
from fluid_rower_monitor.rowing_data import RawRowingData


class TestDecodeRowingData:
    """Test the decode_rowing_data function."""

    def test_decode_returns_dict_or_none(self):
        """Test that decode returns RawRowingData on success, None on failure."""
        # Valid string (29 chars)
        result = decode_rowing_data("A5000010001000219022129074409")
        assert isinstance(result, RawRowingData)

        # Invalid string (too short)
        result = decode_rowing_data("A50001")
        assert result is None

    def test_decode_invalid_short_string(self):
        """Test decoding with a string that's too short."""
        data = "A50001"  # Too short
        result = decode_rowing_data(data)
        assert result is None

    def test_decode_invalid_non_numeric(self):
        """Test decoding with non-numeric values."""
        data = "A5000X1000100219022129074409"  # X is not numeric
        result = decode_rowing_data(data)
        assert result is None

    def test_decode_empty_string(self):
        """Test decoding an empty string."""
        data = ""
        result = decode_rowing_data(data)
        assert result is None

    def test_decode_device_type_extraction(self):
        """Test that device type is correctly extracted from position 1."""
        # Device type 5
        data = "A5000010001002190221290744009"
        result = decode_rowing_data(data)
        assert result.device_type == 5

        # Device type 3
        data = "A3000010001002190221290744009"
        result = decode_rowing_data(data)
        assert result.device_type == 3

    def test_decode_all_fields_present(self):
        """Test that all expected fields are present in result."""
        data = "A5000010001002190221290744009"
        result = decode_rowing_data(data)

        assert result is not None
        assert hasattr(result, "device_type")
        assert hasattr(result, "cumulative_duration_secs")
        assert hasattr(result, "cumulative_distance_m")
        assert hasattr(result, "time_500m_secs")
        assert hasattr(result, "strokes_per_min")
        assert hasattr(result, "power_watts")
        assert hasattr(result, "calories_per_hour")
        assert hasattr(result, "resistance_level")

    def test_decode_returns_integers(self):
        """Test that all decoded fields are integers except device_type."""
        data = "A5000010001002190221290744009"
        result = decode_rowing_data(data)

        assert isinstance(result.device_type, int)
        assert isinstance(result.cumulative_duration_secs, int)
        assert isinstance(result.cumulative_distance_m, int)
        assert isinstance(result.time_500m_secs, int)
        assert isinstance(result.strokes_per_min, int)
        assert isinstance(result.power_watts, int)
        assert isinstance(result.calories_per_hour, int)
        assert isinstance(result.resistance_level, int)

    def test_decode_handles_various_device_types(self):
        """Test decoding with different device types."""
        for device_type in range(10):
            data = f"A{device_type}000010001002190221290744009"
            result = decode_rowing_data(data)
            assert result is not None
            assert result.device_type == device_type

    def test_decode_non_a_prefix_returns_none_device_type(self):
        """Test that non-A prefix results in None device type."""
        data = "B5000010001002190221290744009"
        result = decode_rowing_data(data)
        # The decoder checks if data[0] == 'A', if not device_type is None
        assert result.device_type is None

    def test_decode_real_device_data(self):
        """Test decoder with real Fluid Rower 16-level rower data."""
        # Real data samples from actual device
        real_data = [
            "A5000000000000245000078056809",
            "A5000010001000219022129074409",
            "A5000030001500231035101064809",
            "A5000050002300227028111068209",
            "A5000070002900233033097063409",
        ]

        for data_str in real_data:
            result = decode_rowing_data(data_str)
            assert result is not None
            assert result.device_type == 5

    def test_decode_real_data_example_detail(self):
        """Test specific real data with expected values."""
        # A5 00001 00010 0 02 19 022 129 0744 09
        # device=5, duration=1s, distance=10m, 500m_time=2:19 (139s), spm=22, watts=129, cal=744, resist=9
        data = "A5000010001000219022129074409"
        result = decode_rowing_data(data)

        assert result is not None
        assert result.device_type == 5
        assert result.cumulative_duration_secs == 1
        assert result.cumulative_distance_m == 10
        assert result.time_500m_secs == (2 * 60) + 19  # 139 seconds
        assert result.strokes_per_min == 22
        assert result.power_watts == 129
        assert result.calories_per_hour == 744
        assert result.resistance_level == 9

    def test_decode_real_data_high_effort(self):
        """Test real data from higher effort row."""
        # A5 00025 00086 0 02 35 034 094 0624 09
        data = "A5000250008600235034094062409"
        result = decode_rowing_data(data)

        assert result is not None
        assert result.cumulative_duration_secs == 25
        assert result.cumulative_distance_m == 86
        assert result.time_500m_secs == (2 * 60) + 35  # 155 seconds
        assert result.strokes_per_min == 34
        assert result.power_watts == 94
        assert result.calories_per_hour == 624
        assert result.resistance_level == 9

    def test_decode_real_data_idle(self):
        """Test real data from idle/setup state."""
        # A5 00000 00000 002 45 000 078 0568 09
        data = "A5000000000000245000078056809"
        result = decode_rowing_data(data)

        assert result is not None
        assert result.cumulative_duration_secs == 0
        assert result.cumulative_distance_m == 0
        assert result.time_500m_secs == (2 * 60) + 45  # 165 seconds
        assert result.strokes_per_min == 0
        assert result.power_watts == 78
        assert result.calories_per_hour == 568
        assert result.resistance_level == 9
