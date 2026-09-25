"""
Base Worker Class
Abstract base for all background workers
"""

import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseWorker(ABC):
    """
    Abstract base class for background workers.

    All workers run continuously in the background and can be
    started, stopped, and monitored.
    """

    def __init__(self, name: str, interval_seconds: int):
        """
        Initialize worker.

        Args:
            name: Worker name
            interval_seconds: How often to run worker loop
        """
        self.name = name
        self.interval_seconds = interval_seconds
        self.running = False
        self.logger = logging.getLogger(f"auto-trading-engine.{name}")

        # Stats
        self.iterations = 0
        self.last_run = None
        self.errors = 0

    async def start(self):
        """Start the worker."""
        self.running = True
        self.logger.info(f"🚀 {self.name} starting (interval: {self.interval_seconds}s)")

        while self.running:
            try:
                await self.run()
                self.iterations += 1
                self.last_run = asyncio.get_event_loop().time()

            except Exception as e:
                self.errors += 1
                self.logger.error(f"❌ Error in {self.name}: {e}", exc_info=True)
                # Continue running even if error occurs
                await asyncio.sleep(self.interval_seconds)
            else:
                # Sleep between iterations
                await asyncio.sleep(self.interval_seconds)

        self.logger.info(f"🛑 {self.name} stopped")

    async def stop(self):
        """Stop the worker."""
        self.logger.info(f"⏸️  Stopping {self.name}...")
        self.running = False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get worker statistics.

        Returns:
            Dictionary of worker stats
        """
        return {
            "name": self.name,
            "running": self.running,
            "iterations": self.iterations,
            "last_run": self.last_run,
            "errors": self.errors,
            "interval_seconds": self.interval_seconds
        }

    @abstractmethod
    async def run(self):
        """
        Run one iteration of the worker.

        This method must be implemented by subclasses.
        """
        pass
