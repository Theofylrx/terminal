"""
Session Manager Worker
Manages auto-trading sessions and daily resets
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from datetime import datetime, timedelta
from .base_worker import BaseWorker
from ..core.config import settings
from ..services import TradingClient, NotificationClient
from ..repositories import AutoTradingConfigRepository, AutoTradingSessionRepository
from shared.database.connection import get_session_maker
from shared.database.models.auto_trading_session import SessionStatus


class SessionManagerWorker(BaseWorker):
    """
    Session Manager Worker.

    Manages auto-trading sessions and performs housekeeping tasks.

    Responsibilities:
    - Update session statistics
    - Reset daily loss counters at start of new trading day
    - Check for emergency shutdown conditions
    - Clean up stopped sessions
    - Monitor system health
    """

    def __init__(self):
        """Initialize Session Manager Worker."""
        super().__init__(
            name="SessionManager",
            interval_seconds=settings.SESSION_MANAGER_INTERVAL_SECONDS
        )

        # Initialize service clients
        self.trading_client = TradingClient()
        self.notification_client = NotificationClient()

        # Track last daily reset
        self.last_reset_day = None

        # Stats
        self.sessions_managed = 0
        self.daily_resets = 0
        self.emergency_shutdowns = 0
        self.configs_paused = 0

    async def run(self):
        """Run one iteration of session management."""
        self.logger.debug("⚙️  Managing sessions...")

        try:
            session_maker = get_session_maker()
            async with session_maker() as session:
                config_repo = AutoTradingConfigRepository(session)
                session_repo = AutoTradingSessionRepository(session)

                # 1. Check if new trading day (reset daily counters)
                await self._check_daily_reset(session_repo)

                # 2. Get all active sessions
                active_sessions = await session_repo.get_active_sessions()

                if not active_sessions:
                    self.logger.debug("ℹ️  No active sessions to manage")
                    return

                self.logger.info(f"⚙️  Managing {len(active_sessions)} active sessions")

                # 3. Check each session for emergency conditions
                for session_obj in active_sessions:
                    try:
                        await self._manage_session(
                            session_obj,
                            config_repo,
                            session_repo
                        )
                        self.sessions_managed += 1

                    except Exception as e:
                        self.logger.error(
                            f"❌ Error managing session {session_obj.id}: {e}",
                            exc_info=True
                        )

        except Exception as e:
            self.logger.error(f"❌ Error in session management: {e}", exc_info=True)

    async def _check_daily_reset(self, session_repo):
        """
        Check if we need to reset daily loss counters.

        Args:
            session_repo: AutoTradingSessionRepository
        """
        current_day = datetime.utcnow().date()

        # Reset at start of new day
        if self.last_reset_day is None or self.last_reset_day < current_day:
            self.logger.info("🔄 New trading day - resetting daily loss counters")

            active_sessions = await session_repo.get_active_sessions()

            for session_obj in active_sessions:
                try:
                    await session_repo.reset_daily_loss(session_obj.id)
                    self.daily_resets += 1

                except Exception as e:
                    self.logger.error(
                        f"❌ Error resetting daily loss for session {session_obj.id}: {e}"
                    )

            self.last_reset_day = current_day
            self.logger.info(f"✅ Reset {self.daily_resets} session daily loss counters")

    async def _manage_session(self, session_obj, config_repo, session_repo):
        """
        Manage a single session.

        Args:
            session_obj: AutoTradingSession
            config_repo: AutoTradingConfigRepository
            session_repo: AutoTradingSessionRepository
        """
        # Get configuration
        config = await config_repo.get_by_id(session_obj.config_id)
        if not config:
            self.logger.warning(f"⚠️  Config not found for session {session_obj.id}")
            return

        # Check emergency shutdown conditions
        await self._check_emergency_shutdown(session_obj, config, config_repo, session_repo)

        # Check daily loss limit
        await self._check_daily_loss_limit(session_obj, config, config_repo, session_repo)

        # Update activity timestamp
        await session_repo.update_activity(session_obj.id)

    async def _check_emergency_shutdown(
        self,
        session_obj,
        config,
        config_repo,
        session_repo
    ):
        """
        Check if emergency shutdown is needed.

        Triggers emergency shutdown if:
        - Account drawdown exceeds threshold
        - Too many consecutive losses
        - Critical errors detected

        Args:
            session_obj: AutoTradingSession
            config: AutoTradingConfig
            config_repo: AutoTradingConfigRepository
            session_repo: AutoTradingSessionRepository
        """
        if not settings.EMERGENCY_SHUTDOWN_ENABLED:
            return

        # Get user capital
        capital = await self.trading_client.get_user_capital(config.user_id)
        if not capital:
            return

        # Calculate account drawdown
        total_pnl = session_obj.total_pnl
        drawdown_percent = (total_pnl / capital) * 100 if capital > 0 else 0.0

        # Check if drawdown exceeds threshold
        if drawdown_percent < -settings.CIRCUIT_BREAKER_THRESHOLD:
            self.logger.error(
                f"🚨 EMERGENCY SHUTDOWN: Account drawdown {drawdown_percent:.2f}% "
                f"exceeds threshold ({settings.CIRCUIT_BREAKER_THRESHOLD}%)"
            )

            await self._execute_emergency_shutdown(
                user_id=config.user_id,
                reason=f"Account drawdown {drawdown_percent:.2f}%",
                total_loss=abs(total_pnl),
                config_repo=config_repo,
                session_repo=session_repo
            )

            self.emergency_shutdowns += 1

    async def _check_daily_loss_limit(
        self,
        session_obj,
        config,
        config_repo,
        session_repo
    ):
        """
        Check if daily loss limit has been reached.

        Args:
            session_obj: AutoTradingSession
            config: AutoTradingConfig
            config_repo: AutoTradingConfigRepository
            session_repo: AutoTradingSessionRepository
        """
        if not settings.AUTO_PAUSE_ON_DAILY_LOSS:
            return

        # Get user capital
        capital = await self.trading_client.get_user_capital(config.user_id)
        if not capital:
            return

        # Calculate daily loss limit
        max_daily_loss = capital * (config.max_daily_loss_percent / 100)

        # Check if daily loss exceeds limit
        if session_obj.daily_loss >= max_daily_loss:
            self.logger.warning(
                f"⚠️  Daily loss limit reached for {config.symbol}: "
                f"${session_obj.daily_loss:.2f} / ${max_daily_loss:.2f}"
            )

            # Pause the configuration
            await config_repo.disable(config.id)
            await session_repo.pause(session_obj.id)

            self.configs_paused += 1

            # Send notification
            await self.notification_client.send_trade_exit_notification(
                user_id=config.user_id,
                symbol=config.symbol,
                pnl=-session_obj.daily_loss,
                pnl_percent=-(session_obj.daily_loss / capital * 100),
                reason=f"Daily loss limit reached (${session_obj.daily_loss:.2f})"
            )

            self.logger.info(
                f"⏸️  Auto-trading paused for {config.symbol} until next trading day"
            )

    async def _execute_emergency_shutdown(
        self,
        user_id: str,
        reason: str,
        total_loss: float,
        config_repo,
        session_repo
    ):
        """
        Execute emergency shutdown for a user.

        Args:
            user_id: User ID
            reason: Shutdown reason
            total_loss: Total loss amount
            config_repo: AutoTradingConfigRepository
            session_repo: AutoTradingSessionRepository
        """
        self.logger.error(f"🚨 Executing emergency shutdown for user {user_id}")

        try:
            # 1. Disable all auto-trading configs for this user
            user_configs = await config_repo.get_all_by_user(user_id)

            for config in user_configs:
                if config.enabled:
                    await config_repo.disable(config.id)
                    self.logger.info(f"🔴 Disabled auto-trading for {config.symbol}")

            # 2. Stop all active sessions
            user_sessions = await session_repo.get_user_sessions(
                user_id,
                status=SessionStatus.ACTIVE
            )

            for session_obj in user_sessions:
                await session_repo.stop(session_obj.id)
                self.logger.info(f"🛑 Stopped session for {session_obj.symbol}")

            # 3. Close all open auto-traded positions
            # NOTE: This would require calling Executor Service to close all positions
            # For now, just log - actual implementation would close positions

            self.logger.warning(
                "⚠️  Emergency shutdown executed - all auto-trading disabled. "
                "Manual review required before re-enabling."
            )

            # 4. Send emergency notification
            await self.notification_client.send_emergency_shutdown_notification(
                user_id=user_id,
                reason=reason,
                total_loss=total_loss
            )

        except Exception as e:
            self.logger.error(f"❌ Error during emergency shutdown: {e}", exc_info=True)

    async def stop(self):
        """Stop worker and close clients."""
        await super().stop()

        # Close HTTP clients
        await self.trading_client.close()
        await self.notification_client.close()

    def get_stats(self):
        """Get worker statistics."""
        stats = super().get_stats()
        stats.update({
            "sessions_managed": self.sessions_managed,
            "daily_resets": self.daily_resets,
            "emergency_shutdowns": self.emergency_shutdowns,
            "configs_paused": self.configs_paused,
            "last_reset_day": str(self.last_reset_day) if self.last_reset_day else None
        })
        return stats
