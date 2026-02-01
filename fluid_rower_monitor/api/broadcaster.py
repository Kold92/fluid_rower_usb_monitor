"""Data broadcaster for live rowing data.

Provides a publish-subscribe pattern for streaming rowing samples to multiple WebSocket clients.
Supports both dev mode (synthetic data) and production mode (real serial connection).
"""

from __future__ import annotations

import asyncio
import random
import serial
import time
from typing import AsyncIterator, Literal

from ..rowing_data import RowingDataPoint
from ..serial_conn import (
    attempt_reconnect,
    connect_to_device,
    decode_rowing_data,
    reset_device_session,
    setup_serial,
)
from ..settings import AppSettings
from .session_manager import record_point

BroadcastMode = Literal["dev", "production"]


class DataBroadcaster:
    """Singleton broadcaster for rowing data points."""

    def __init__(self, mode: BroadcastMode = "dev", settings: AppSettings | None = None):
        self.mode = mode
        self.settings = settings or AppSettings()
        self.subscribers: list[asyncio.Queue] = []
        self._task: asyncio.Task | None = None
        self.serial_conn: serial.Serial | None = None
        self.previous_raw_data: dict[str, float] | None = None

    async def start(self) -> None:
        """Start the data stream task."""
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._run_stream())

    async def stop(self) -> None:
        """Stop the data stream task."""
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def subscribe(self) -> AsyncIterator[RowingDataPoint]:
        """Subscribe to data stream. Yields RowingDataPoint instances."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self.subscribers.append(queue)
        try:
            while True:
                point = await queue.get()
                yield point
        finally:
            self.subscribers.remove(queue)

    async def _publish(self, point: RowingDataPoint) -> None:
        """Publish a data point to all subscribers."""
        record_point(point)
        dead_queues = []
        for q in self.subscribers:
            try:
                q.put_nowait(point)
            except asyncio.QueueFull:
                # Subscriber too slow; drop this point or mark for removal
                dead_queues.append(q)
        for q in dead_queues:
            if q in self.subscribers:
                self.subscribers.remove(q)

    async def _run_stream(self) -> None:
        """Main streaming loop (dev or production)."""
        if self.mode == "dev":
            await self._run_dev_stream()
        else:
            await self._run_production_stream()

    async def _run_dev_stream(self) -> None:
        """Synthetic data generator for development."""
        while True:
            point = RowingDataPoint(
                stroke_duration_secs=round(random.uniform(1.8, 2.5), 2),
                stroke_distance_m=round(random.uniform(8.5, 10.5), 2),
                time_500m_secs=random.randint(110, 160),
                strokes_per_min=random.randint(18, 30),
                power_watts=random.randint(100, 300),
                calories_per_hour=random.randint(500, 900),
                resistance_level=random.randint(6, 12),
            )
            await self._publish(point)
            await asyncio.sleep(2.0)  # Simulate stroke interval

    async def _run_production_stream(self) -> None:
        """Real serial connection streaming from rowing device."""
        try:
            self.serial_conn = setup_serial(
                self.settings.serial.port,
                self.settings.serial.baudrate,
                self.settings.serial.timeout_secs,
            )
            if not connect_to_device(self.serial_conn):
                print("Failed to connect to rower device")
                return

            if not reset_device_session(self.serial_conn):
                print("Failed to reset device session")
                return

            print("Production streaming started")
            self.previous_raw_data = None

            while True:
                try:
                    loop = asyncio.get_running_loop()
                    response = await loop.run_in_executor(None, self._read_serial_blocking)

                    if response and response.startswith("A"):
                        raw_data = decode_rowing_data(response)
                        if raw_data and self.previous_raw_data:
                            stroke_distance = (
                                raw_data.cumulative_distance_m
                                - self.previous_raw_data["cumulative_distance_m"]
                            )
                            stroke_duration = (
                                raw_data.cumulative_duration_secs
                                - self.previous_raw_data["cumulative_duration_secs"]
                            )

                            point = RowingDataPoint(
                                stroke_distance_m=stroke_distance,
                                stroke_duration_secs=stroke_duration,
                                time_500m_secs=raw_data.time_500m_secs,
                                strokes_per_min=raw_data.strokes_per_min,
                                power_watts=raw_data.power_watts,
                                calories_per_hour=raw_data.calories_per_hour,
                                resistance_level=raw_data.resistance_level,
                            )
                            await self._publish(point)

                        if raw_data:
                            self.previous_raw_data = {
                                "cumulative_distance_m": raw_data.cumulative_distance_m,
                                "cumulative_duration_secs": raw_data.cumulative_duration_secs,
                            }

                except (serial.SerialException, OSError) as exc:
                    print(f"Serial read error: {exc}")
                    if self.serial_conn:
                        self.serial_conn.close()
                    new_ser = attempt_reconnect(self.settings)
                    if new_ser:
                        self.serial_conn = new_ser
                        self.previous_raw_data = None
                    else:
                        print("Failed to reconnect; stopping production stream")
                        break

        except Exception as exc:
            print(f"Production stream error: {exc}")
        finally:
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.close()
                print("Serial connection closed")

    def _read_serial_blocking(self) -> str | None:
        """Blocking serial read (runs in executor to avoid blocking event loop)."""
        if not self.serial_conn:
            return None
        start_time = time.time()
        while True:
            if self.serial_conn.in_waiting:
                return self.serial_conn.readline().decode("utf-8", errors="ignore").strip()
            if (time.time() - start_time) > self.settings.serial.timeout_secs:
                return None
            time.sleep(0.01)


# Global singleton instance
_broadcaster: DataBroadcaster | None = None


def get_broadcaster(mode: BroadcastMode = "dev") -> DataBroadcaster:
    """Get or create the global broadcaster instance."""
    global _broadcaster
    if _broadcaster is None:
        _broadcaster = DataBroadcaster(mode=mode)
    return _broadcaster
