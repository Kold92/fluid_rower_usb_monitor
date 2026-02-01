import argparse
import serial
import time
from . import __version__
from .rowing_data import RowingSession, RowingDataPoint, RawRowingData
from .rowing_analyzer import RowingAnalyzer
from .settings import AppSettings, ensure_config_exists

PORT = "/dev/ttyUSB0"  # Linux/macOS example
# PORT = "COM3"        # Windows example
BAUDRATE = 9600
TIMEOUT = 2  # seconds - used for blocking read


def setup_serial(port, baudrate, timeout):
    ser = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)

    print(f"Connected to {ser.portstr}")
    return ser


def get_serial_response(ser: serial.Serial, timeout: float) -> str | None:
    """Reads from serial or times out after 'timeout' seconds."""
    start_time = time.time()

    while True:
        if ser.in_waiting:
            return ser.readline().decode("utf-8", errors="ignore").strip()

        if (time.time() - start_time) > timeout:
            return None
        time.sleep(0.1)


def connect_to_device(ser: serial.Serial) -> bool:
    """
    Sends 'C' to connect to the device and waits for 'C' response.
    Returns True on successful connection, False on timeout.
    """
    max_attempts = 20
    for attempt in range(max_attempts):
        ser.write(b"C\n")
        print(f"[Attempt {attempt + 1}/{max_attempts}] Sent connection request 'C'")
        response = get_serial_response(ser, timeout=2)

        if response and response.startswith("C"):
            print(f"✓ Successfully connected to the device v{response[1:]}!")
            return True
        else:
            print(f"  Got: {repr(response)}, retrying...")
            time.sleep(0.1)

    print("✗ Failed to connect to device after max attempts")
    return False


def reset_device_session(ser: serial.Serial) -> bool:
    """Sends reset command to the device (rower-side session)."""
    ser.write(b"R\n")
    time.sleep(0.5)
    while True:
        response = get_serial_response(ser, timeout=2)
        if response and response.startswith("R"):
            return True
        if response is None:
            return False


def attempt_reconnect(settings: AppSettings, sleep_fn=None) -> serial.Serial | None:
    """Try to re-establish the serial connection with backoff.

    Returns the newly connected serial object or None if retries exhausted.
    """
    sleep = sleep_fn or time.sleep
    for attempt in range(settings.reconnect.max_attempts):
        try:
            ser = setup_serial(settings.serial.port, settings.serial.baudrate, settings.serial.timeout_secs)
            if connect_to_device(ser):
                return ser
        except serial.SerialException as exc:
            print(f"Reconnect attempt {attempt + 1} failed: {exc}")
        sleep(settings.reconnect.backoff_secs)
    return None


def decode_rowing_data(data: str) -> RawRowingData | None:
    """
    Decode rowing data in format: A5 00001 00010 002 19 022 129 0744 09

    Format (fixed-width, no spaces):
    - Position 0-1: A5 (device type, A prefix + digit)
    - Position 2-6: Row duration (secs)
    - Position 7-11: Row distance (meters)
    - Position 12-12: Unused
    - Position 13-14: 500m time (minutes)
    - Position 15-16: 500m time (seconds)
    - Position 17-19: Strokes per minute
    - Position 20-22: Power (watts)
    - Position 23-26: Calories per hour
    - Position 27-28: Resistance level

    Returns:
        RawRowingData object with cumulative values, or None on error
    """
    try:
        time_500m_minutes = int(data[13:15])
        time_500m_seconds = int(data[15:17])
        time_500m_total_secs = (time_500m_minutes * 60) + time_500m_seconds

        return RawRowingData(
            device_type=int(data[1]) if data[0] == "A" else None,
            cumulative_duration_secs=int(data[2:7]),
            cumulative_distance_m=int(data[7:12]),
            time_500m_secs=time_500m_total_secs,
            strokes_per_min=int(data[17:20]),
            power_watts=int(data[20:23]),
            calories_per_hour=int(data[23:27]),
            resistance_level=int(data[27:29]),
        )
    except (IndexError, ValueError) as e:
        print(f"Error decoding rowing data '{data}': {e}")
        return None


def rowing_session(ser: serial.Serial, settings: AppSettings | None = None):
    """
    Starts a new rowing session.
    Read rowing data, decode, store per-stroke data points, and save session.
    Supports periodic flushing, pause/resume tracking on disconnect/reconnect.
    """

    settings = settings or AppSettings()

    if not reset_device_session(ser):
        print("Failed to reset session.")
        return

    session = RowingSession(data_dir=settings.data.dir)
    print(f"New rowing session started. Saving to: {session.filename}")
    print()

    previous_data = None
    total_distance = 0
    total_duration = 0
    last_flush_time = time.time()
    last_flush_index = 0

    try:
        while True:
            try:
                response = get_serial_response(ser, timeout=5)
            except (serial.SerialException, OSError) as exc:
                print(f"Serial read error: {exc}")
                session.pause()
                # Flush partial data before disconnect
                if session.data_points:
                    session.partial_save(from_index=last_flush_index)
                    last_flush_index = len(session.data_points)
                    print(f"Partial session flushed ({len(session.data_points)} strokes)")
                if ser and ser.is_open:
                    ser.close()
                new_ser = attempt_reconnect(settings)
                if new_ser is None:
                    print("Failed to reconnect; ending session.")
                    break
                ser = new_ser
                session.resume()
                print("Session resumed after reconnection.")
                # Reset rolling state after reconnect to avoid bad deltas
                previous_data = None
                last_flush_time = time.time()
                continue

            if response and response.startswith("A"):
                decoded = decode_rowing_data(response)
                if decoded:
                    # Calculate per-stroke deltas
                    if previous_data:
                        stroke_distance = decoded.cumulative_distance_m - previous_data.cumulative_distance_m
                        stroke_duration = decoded.cumulative_duration_secs - previous_data.cumulative_duration_secs

                        total_distance += stroke_distance
                        total_duration += stroke_duration

                        # Create data point with per-stroke values
                        point = RowingDataPoint(
                            stroke_distance_m=stroke_distance,
                            stroke_duration_secs=stroke_duration,
                            time_500m_secs=decoded.time_500m_secs,
                            strokes_per_min=decoded.strokes_per_min,
                            power_watts=decoded.power_watts,
                            calories_per_hour=decoded.calories_per_hour,
                            resistance_level=decoded.resistance_level,
                        )
                        session.add_point(point)

                        # Display live stats
                        stats = RowingAnalyzer.get_live_stats(session.data_points)
                        print(
                            f"Distance: {total_distance}m | Duration: {total_duration}s | "
                            f"Avg 500m: {stats.mean_time_500m_secs:.1f}s | "
                            f"Avg Power: {stats.mean_power_watts:.0f}W | "
                            f"SPM: {decoded.strokes_per_min}"
                        )

                        # Check flush triggers
                        elapsed_since_flush = time.time() - last_flush_time
                        strokes_since_flush = len(session.data_points) - last_flush_index
                        if (
                            elapsed_since_flush >= settings.reconnect.flush_interval_secs
                            or strokes_since_flush >= settings.reconnect.flush_after_strokes
                        ):
                            session.partial_save(from_index=last_flush_index)
                            last_flush_index = len(session.data_points)
                            last_flush_time = time.time()
                            print(f"Session flushed ({strokes_since_flush} new strokes)")

                    previous_data = decoded

            elif response:
                print(f"Received: {response}")

    except KeyboardInterrupt:
        print("\n\nSession ended by user.")
    finally:
        # Ensure pause is finalized if still paused
        if session.paused_at is not None:
            session.resume()

        # Save session and show final stats
        if session.data_points:
            session.save()
            stats = RowingAnalyzer.get_live_stats(session.data_points)
            print("\n=== Session Summary ===")
            print(f"Total strokes: {stats.num_strokes}")
            print(f"Total distance: {stats.total_distance_m:.1f}m")
            print(f"Total duration: {stats.total_duration_secs:.0f}s")
            print(f"Mean 500m pace: {stats.mean_time_500m_secs:.1f}s")
            print(f"Mean power: {stats.mean_power_watts:.0f}W")
            print(f"Total calories: {stats.total_calories:.0f}/hr")
            if session.total_pause_secs > 0:
                print(f"Total pause time: {session.total_pause_secs:.1f}s ({len(session.pauses)} interruptions)")
            print(f"Session saved to: {session.filename}")
        else:
            print("No data recorded in session.")


def main(settings: AppSettings | None = None):
    # Ensure config.yaml exists before loading settings
    if settings is None:
        try:
            ensure_config_exists()
        except FileNotFoundError as e:
            print(f"Configuration error: {e}")
            return

    settings = settings or AppSettings()
    try:
        ser = setup_serial(settings.serial.port, settings.serial.baudrate, settings.serial.timeout_secs)

        if not connect_to_device(ser):
            print("Could not connect to device. Exiting.")
            return

        rowing_session(ser, settings=settings)

    except serial.SerialException as e:
        print(f"Serial error: {e}")
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        if "ser" in locals() and ser.is_open:
            ser.close()
            print("Serial port closed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fluid Rower USB Monitor - Track and analyze rowing sessions")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.parse_args()
    main()
