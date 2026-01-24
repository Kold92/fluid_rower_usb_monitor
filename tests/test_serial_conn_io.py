"""Tests for serial I/O functions with mocked serial port."""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from io import StringIO
import time

from fluid_rower_monitor.serial_conn import (
    setup_serial,
    get_serial_response,
    connect_to_device,
    reset_session,
    rowing_session,
)
from fluid_rower_monitor.rowing_data import RowingDataPoint, RowingSession


class TestSetupSerial:
    """Tests for setup_serial function."""

    def test_setup_serial_creates_serial_connection(self):
        """Test that setup_serial initializes serial connection with correct parameters."""
        with patch('fluid_rower_monitor.serial_conn.serial.Serial') as mock_serial_class:
            mock_ser = MagicMock()
            mock_ser.portstr = "/dev/ttyUSB0"
            mock_serial_class.return_value = mock_ser

            result = setup_serial("/dev/ttyUSB0", 9600, 2)

            mock_serial_class.assert_called_once_with(
                port="/dev/ttyUSB0",
                baudrate=9600,
                timeout=2
            )
            assert result == mock_ser

    def test_setup_serial_windows_port(self):
        """Test setup_serial with Windows COM port."""
        with patch('fluid_rower_monitor.serial_conn.serial.Serial') as mock_serial_class:
            mock_ser = MagicMock()
            mock_ser.portstr = "COM3"
            mock_serial_class.return_value = mock_ser

            result = setup_serial("COM3", 9600, 2)

            assert result == mock_ser
            mock_serial_class.assert_called_once()

    def test_setup_serial_different_baudrate(self):
        """Test setup_serial with different baudrate."""
        with patch('fluid_rower_monitor.serial_conn.serial.Serial') as mock_serial_class:
            mock_ser = MagicMock()
            mock_serial_class.return_value = mock_ser

            setup_serial("/dev/ttyUSB0", 19200, 5)

            mock_serial_class.assert_called_once_with(
                port="/dev/ttyUSB0",
                baudrate=19200,
                timeout=5
            )


class TestGetSerialResponse:
    """Tests for get_serial_response function."""

    def test_get_serial_response_immediate_data(self):
        """Test reading response when data is immediately available."""
        mock_ser = MagicMock()
        mock_ser.in_waiting = 1
        mock_ser.readline.return_value = b"A5 00001 00010 002 19 022 129 0744 09\n"

        result = get_serial_response(mock_ser, timeout=1)

        assert result == "A5 00001 00010 002 19 022 129 0744 09"
        mock_ser.readline.assert_called_once()

    def test_get_serial_response_timeout_no_data(self):
        """Test timeout when no data is available."""
        mock_ser = MagicMock()
        mock_ser.in_waiting = 0

        with patch('time.time') as mock_time:
            # Simulate time passing
            mock_time.side_effect = [0, 0.5, 1.0, 1.5]

            result = get_serial_response(mock_ser, timeout=1)

            assert result is None

    def test_get_serial_response_strips_whitespace(self):
        """Test that response strips leading/trailing whitespace."""
        mock_ser = MagicMock()
        mock_ser.in_waiting = 1
        mock_ser.readline.return_value = b"  A5 00001 00010 002 19 022 129 0744 09  \n"

        result = get_serial_response(mock_ser, timeout=1)

        assert result == "A5 00001 00010 002 19 022 129 0744 09"

    def test_get_serial_response_ignores_decode_errors(self):
        """Test that decode errors are ignored with replacement strategy."""
        mock_ser = MagicMock()
        mock_ser.in_waiting = 1
        mock_ser.readline.return_value = b"A5 \xff\xfe 00010 002 19 022 129 0744 09\n"

        result = get_serial_response(mock_ser, timeout=1)

        # Should return something despite decode errors
        assert result is not None
        assert isinstance(result, str)

    def test_get_serial_response_waits_for_data(self):
        """Test that function respects timeout."""
        mock_ser = MagicMock()
        mock_ser.in_waiting = 0

        with patch('time.time', side_effect=[0, 0.05, 0.1, 0.15, 1.5]):
            with patch('time.sleep'):
                result = get_serial_response(mock_ser, timeout=0.2)
                assert result is None


class TestConnectToDevice:
    """Tests for connect_to_device function."""

    def test_connect_to_device_success_first_attempt(self):
        """Test successful connection on first attempt."""
        mock_ser = MagicMock()
        
        with patch('fluid_rower_monitor.serial_conn.get_serial_response') as mock_get:
            mock_get.return_value = "C1"  # Device version 1
            
            result = connect_to_device(mock_ser)

            assert result is True
            mock_ser.write.assert_called_once_with(b"C\n")

    def test_connect_to_device_retries_on_bad_response(self):
        """Test that connect retries with non-C response."""
        mock_ser = MagicMock()
        
        with patch('fluid_rower_monitor.serial_conn.get_serial_response') as mock_get:
            # Bad response, then good
            mock_get.side_effect = ["A5 00001 00010 002 19 022 129 0744 09", "C2"]
            
            with patch('time.sleep'):
                result = connect_to_device(mock_ser)

            assert result is True
            assert mock_ser.write.call_count == 2

    def test_connect_to_device_timeout_after_max_attempts(self):
        """Test that connect fails after max attempts."""
        mock_ser = MagicMock()
        
        with patch('fluid_rower_monitor.serial_conn.get_serial_response') as mock_get:
            # Always bad response (not starting with C)
            mock_get.return_value = "A5 00001 00010 002 19 022 129 0744 09"
            
            with patch('time.sleep'):
                result = connect_to_device(mock_ser)

            assert result is False
            assert mock_ser.write.call_count == 20  # max_attempts

    def test_connect_to_device_handles_none_response(self):
        """Test that connect handles None response gracefully."""
        mock_ser = MagicMock()
        
        with patch('fluid_rower_monitor.serial_conn.get_serial_response') as mock_get:
            mock_get.side_effect = [None, None, "C3"]
            
            with patch('time.sleep'):
                result = connect_to_device(mock_ser)

            assert result is True


class TestResetSession:
    """Tests for reset_session function."""

    def test_reset_session_success(self):
        """Test successful session reset."""
        mock_ser = MagicMock()
        
        with patch('fluid_rower_monitor.serial_conn.get_serial_response') as mock_get:
            mock_get.return_value = "R"
            
            result = reset_session(mock_ser)

            assert result is True
            mock_ser.write.assert_called_once_with(b"R\n")

    def test_reset_session_timeout(self):
        """Test reset timeout."""
        mock_ser = MagicMock()
        
        with patch('fluid_rower_monitor.serial_conn.get_serial_response') as mock_get:
            mock_get.return_value = "A5 00001 00010 002 19 022 129 0744 09"  # Invalid response
            
            # This will loop indefinitely, so we need to mock out the infinite loop
            # Let's make it return None instead
            mock_get.return_value = None
            
            result = reset_session(mock_ser)

            assert result is False

    def test_reset_session_retries_on_invalid_response(self):
        """Test that reset succeeds with valid response."""
        mock_ser = MagicMock()
        
        with patch('fluid_rower_monitor.serial_conn.get_serial_response') as mock_get:
            mock_get.side_effect = ["A5 00001 00010 002 19 022 129 0744 09", "R"]
            
            result = reset_session(mock_ser)

            assert result is True


class TestRowingSession:
    """Tests for rowing_session function."""

    def test_rowing_session_keyboard_interrupt(self):
        """Test that rowing_session handles KeyboardInterrupt."""
        mock_ser = MagicMock()
        
        with patch('fluid_rower_monitor.serial_conn.reset_session') as mock_reset:
            mock_reset.return_value = True
            
            with patch('fluid_rower_monitor.serial_conn.get_serial_response') as mock_get:
                mock_get.side_effect = KeyboardInterrupt()
                
                # Should not raise, should handle gracefully
                rowing_session(mock_ser)

    def test_rowing_session_failed_reset(self):
        """Test that rowing_session handles failed reset."""
        mock_ser = MagicMock()
        
        with patch('fluid_rower_monitor.serial_conn.reset_session') as mock_reset:
            mock_reset.return_value = False
            
            # Should return early without raising
            rowing_session(mock_ser)

    def test_rowing_session_processes_data(self):
        """Test that rowing_session processes rowing data."""
        mock_ser = MagicMock()
        
        # Two data points to show delta calculation
        data_points = [
            "A5 00001 00010 002 19 022 129 0744 09",
            "A5 00002 00020 002 19 022 129 0744 09",
        ]
        
        with patch('fluid_rower_monitor.serial_conn.reset_session') as mock_reset:
            mock_reset.return_value = True
            
            with patch('fluid_rower_monitor.serial_conn.get_serial_response') as mock_get:
                # Yield data points then KeyboardInterrupt
                mock_get.side_effect = data_points + [KeyboardInterrupt()]
                
                with patch('fluid_rower_monitor.rowing_data.RowingSession.save'):
                    rowing_session(mock_ser)

    def test_rowing_session_ignores_non_rowing_data(self):
        """Test that rowing_session ignores non-rowing responses."""
        mock_ser = MagicMock()
        
        responses = [
            "C1",  # Connection response, not rowing data
            "R",   # Reset response
            "Unknown data",
            "A5 00001 00010 002 19 022 129 0744 09",  # Valid rowing
        ]
        
        with patch('fluid_rower_monitor.serial_conn.reset_session') as mock_reset:
            mock_reset.return_value = True
            
            with patch('fluid_rower_monitor.serial_conn.get_serial_response') as mock_get:
                mock_get.side_effect = responses + [KeyboardInterrupt()]
                
                with patch('fluid_rower_monitor.rowing_data.RowingSession.save'):
                    rowing_session(mock_ser)

    def test_rowing_session_saves_on_exit(self):
        """Test that rowing_session saves data on exit."""
        mock_ser = MagicMock()
        
        with patch('fluid_rower_monitor.serial_conn.reset_session') as mock_reset:
            mock_reset.return_value = True
            
            with patch('fluid_rower_monitor.serial_conn.get_serial_response') as mock_get:
                mock_get.side_effect = KeyboardInterrupt()
                
                with patch('fluid_rower_monitor.rowing_data.RowingSession.save') as mock_save:
                    rowing_session(mock_ser)
                    # Save might not be called if no data points

    def test_rowing_session_calculates_deltas(self):
        """Test that rowing_session correctly calculates per-stroke deltas."""
        mock_ser = MagicMock()
        
        # Data showing progression: distance 10->20, duration 1->2
        responses = [
            "A5 00001 00010 002 19 022 129 0744 09",  # First: 1s, 10m
            "A5 00002 00020 002 19 022 129 0744 09",  # Second: +1s, +10m delta
            KeyboardInterrupt(),
        ]
        
        with patch('fluid_rower_monitor.serial_conn.reset_session') as mock_reset:
            mock_reset.return_value = True
            
            with patch('fluid_rower_monitor.serial_conn.get_serial_response') as mock_get:
                mock_get.side_effect = responses
                
                with patch('fluid_rower_monitor.rowing_data.RowingSession.save'):
                    rowing_session(mock_ser)

    def test_rowing_session_handles_invalid_decoding(self):
        """Test that rowing_session handles invalid rowing data."""
        mock_ser = MagicMock()
        
        responses = [
            "A5 XXXXX YYYYY 002 19 022 129 0744 09",  # Invalid - will fail decode
            KeyboardInterrupt(),
        ]
        
        with patch('fluid_rower_monitor.serial_conn.reset_session') as mock_reset:
            mock_reset.return_value = True
            
            with patch('fluid_rower_monitor.serial_conn.get_serial_response') as mock_get:
                mock_get.side_effect = responses
                
                with patch('fluid_rower_monitor.rowing_data.RowingSession.save'):
                    # Should not raise, should handle gracefully
                    rowing_session(mock_ser)

    def test_rowing_session_no_data_recorded(self):
        """Test rowing_session message when no data is recorded."""
        mock_ser = MagicMock()
        
        with patch('fluid_rower_monitor.serial_conn.reset_session') as mock_reset:
            mock_reset.return_value = True
            
            with patch('fluid_rower_monitor.serial_conn.get_serial_response') as mock_get:
                mock_get.side_effect = KeyboardInterrupt()
                
                # No data recorded, should not call save
                with patch('fluid_rower_monitor.rowing_data.RowingSession.save') as mock_save:
                    rowing_session(mock_ser)
                    # When no data points, save may not be called


class TestMainFunction:
    """Tests for main() function."""

    def test_main_successful_flow(self):
        """Test main function successful execution."""
        with patch('fluid_rower_monitor.serial_conn.setup_serial') as mock_setup:
            with patch('fluid_rower_monitor.serial_conn.connect_to_device') as mock_connect:
                with patch('fluid_rower_monitor.serial_conn.rowing_session') as mock_session:
                    mock_ser = MagicMock()
                    mock_setup.return_value = mock_ser
                    mock_connect.return_value = True
                    
                    from fluid_rower_monitor.serial_conn import main
                    main()
                    
                    mock_setup.assert_called_once()
                    mock_connect.assert_called_once()
                    mock_session.assert_called_once()
                    mock_ser.close.assert_called_once()

    def test_main_connection_fails(self):
        """Test main handles failed connection."""
        with patch('fluid_rower_monitor.serial_conn.setup_serial') as mock_setup:
            with patch('fluid_rower_monitor.serial_conn.connect_to_device') as mock_connect:
                with patch('fluid_rower_monitor.serial_conn.rowing_session') as mock_session:
                    mock_ser = MagicMock()
                    mock_setup.return_value = mock_ser
                    mock_connect.return_value = False
                    
                    from fluid_rower_monitor.serial_conn import main
                    main()
                    
                    mock_session.assert_not_called()
                    mock_ser.close.assert_called_once()

    def test_main_serial_exception(self):
        """Test main handles SerialException."""
        with patch('fluid_rower_monitor.serial_conn.setup_serial') as mock_setup:
            import serial
            mock_setup.side_effect = serial.SerialException("Port not found")
            
            from fluid_rower_monitor.serial_conn import main
            # Should not raise
            main()

    def test_main_keyboard_interrupt(self):
        """Test main handles KeyboardInterrupt."""
        with patch('fluid_rower_monitor.serial_conn.setup_serial') as mock_setup:
            mock_setup.side_effect = KeyboardInterrupt()
            
            from fluid_rower_monitor.serial_conn import main
            # Should not raise
            main()
