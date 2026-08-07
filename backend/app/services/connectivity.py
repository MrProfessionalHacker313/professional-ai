"""
Professional AI - Internet Connectivity Detection
Detects online/offline status and connection quality for adaptive behavior.
"""

import asyncio
import time
import socket
import httpx
from typing import Optional, Dict, Any, Callable, Awaitable
from enum import Enum
from dataclasses import dataclass, field
from loguru import logger


class ConnectionQuality(Enum):
    ONLINE = "online"
    LOW_BANDWIDTH = "low_bandwidth"
    OFFLINE = "offline"


@dataclass
class ConnectionState:
    is_online: bool = True
    quality: ConnectionQuality = ConnectionQuality.ONLINE
    latency_ms: float = 0.0
    last_check: float = field(default_factory=time.time)
    consecutive_failures: int = 0


class ConnectivityService:
    """
    Detects internet connectivity and connection quality.
    Uses multiple check methods for reliability.
    """

    def __init__(self):
        self.state = ConnectionState()
        self._check_interval = 30  # seconds
        self._check_task: Optional[asyncio.Task] = None
        self._listeners: list = []
        self._check_urls = [
            "http://www.google.com/generate_204",
            "http://1.1.1.1/cdn-cgi/trace",
            "http://clients3.google.com/generate_204",
            "http://www.msftconnecttest.com/connecttest.txt",
        ]
        self._slow_threshold_ms = 2000  # >2s = slow connection
        self._failure_threshold = 3

    async def start(self):
        """Start background connectivity monitoring."""
        if self._check_task is None:
            self._check_task = asyncio.create_task(self._monitor_loop())
            logger.info("Connectivity monitor started")

    async def stop(self):
        """Stop connectivity monitoring."""
        if self._check_task:
            self._check_task.cancel()
            self._check_task = None
            logger.info("Connectivity monitor stopped")

    def add_listener(self, callback: Callable[[ConnectionState], Awaitable[None]]):
        """Add listener for connectivity changes."""
        self._listeners.append(callback)

    async def _notify_listeners(self):
        """Notify all listeners of state change."""
        for listener in self._listeners:
            try:
                await listener(self.state)
            except Exception as e:
                logger.debug(f"Listener notification failed: {e}")

    async def _monitor_loop(self):
        """Background connectivity check loop."""
        while True:
            try:
                await self.check_connectivity()
                await asyncio.sleep(self._check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Connectivity monitor error: {e}")
                await asyncio.sleep(self._check_interval)

    async def check_connectivity(self) -> ConnectionState:
        """
        Perform connectivity check and update state.
        Returns the current connection state.
        """
        start_time = time.time()
        is_online = False
        latency_ms = 0.0

        # Method 1: Try DNS resolution (fastest, no HTTP needed)
        try:
            await asyncio.get_event_loop().run_in_executor(
                None, socket.gethostbyname, "www.google.com"
            )
            is_online = True
            latency_ms = (time.time() - start_time) * 1000
        except Exception:
            is_online = False

        # Method 2: Try HTTP check if DNS worked
        if is_online:
            for url in self._check_urls:
                try:
                    check_start = time.time()
                    async with httpx.AsyncClient(
                        timeout=httpx.Timeout(5.0, connect=2.0),
                        follow_redirects=False,
                    ) as client:
                        response = await client.get(url)
                    latency_ms = (time.time() - check_start) * 1000

                    if response.status_code in (200, 204, 301, 302):
                        is_online = True
                        break
                except Exception:
                    continue

        # Determine connection quality
        old_state = self.state
        if not is_online:
            self.state.consecutive_failures += 1
            if self.state.consecutive_failures >= self._failure_threshold:
                self.state.is_online = False
                self.state.quality = ConnectionQuality.OFFLINE
        else:
            self.state.consecutive_failures = 0
            self.state.is_online = True
            self.state.latency_ms = latency_ms
            self.state.last_check = time.time()

            if latency_ms > self._slow_threshold_ms:
                self.state.quality = ConnectionQuality.LOW_BANDWIDTH
            else:
                self.state.quality = ConnectionQuality.ONLINE

        # Notify listeners on state change
        if old_state.is_online != self.state.is_online or old_state.quality != self.state.quality:
            logger.info(
                f"Connectivity changed: {old_state.quality.value} -> {self.state.quality.value}"
            )
            await self._notify_listeners()

        return self.state

    async def is_online(self) -> bool:
        """Quick check if internet is available."""
        return self.state.is_online

    async def get_quality(self) -> ConnectionQuality:
        """Get current connection quality."""
        return self.state.quality

    async def get_latency(self) -> float:
        """Get current latency in milliseconds."""
        return self.state.latency_ms

    def get_state(self) -> ConnectionState:
        """Get current connection state."""
        return self.state


connectivity_service = ConnectivityService()
