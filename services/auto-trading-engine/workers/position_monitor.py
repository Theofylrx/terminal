"""
Position Monitor Worker
Monitors open positions for exit signals
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from .base_worker import BaseWorker
from ..core.config import settings
from ..services import (
    MarketDataClient,
    TechnicalAnalystClient,
    ExecutorClient,
    TradingClient,
    NotificationClient,
    DecisionEngine,
    DecisionAction
)
from ..repositories import AutoTradingConfigRepository, AutoTradingSessionRepository
from shared.database.connection import get_session_maker


class PositionMonitorWorker(BaseWorker):
    """
    Position Monitor Worker.

    Continuously monitors all auto-traded positions for exit opportunities.

    Flow:
    1. Get all open auto-traded positions from Trading Service
    2. For each position:
       - Get current market price from Market Data Service
       - Calculate current P&L
       - Request latest technical analysis from Technical Analyst Service
       - Make autonomous exit decision using Decision Engine
       - If decision is to exit, close position via Executor Service
       - If decision is to adjust stop, update stop-loss
    3. Sleep and repeat
    """

    def __init__(self):
        """Initialize Position Monitor Worker."""
        super().__init__(
            name="PositionMonitor",
            interval_seconds=settings.POSITION_MONITOR_INTERVAL_SECONDS
        )

        # Initialize service clients
        self.market_data_client = MarketDataClient()
        self.technical_analyst_client = TechnicalAnalystClient()
        self.executor_client = ExecutorClient()
        self.trading_client = TradingClient()
        self.notification_client = NotificationClient()

        # Initialize decision engine
        self.decision_engine = DecisionEngine()

        # Stats
        self.positions_monitored = 0
        self.positions_closed = 0
        self.stops_adjusted = 0
        self.profit_protections = 0
        self.stop_losses = 0

    async def run(self):
        """Run one iteration of position monitoring."""
        self.logger.debug("📊 Monitoring open positions...")

        try:
            # Get all open auto-traded positions
            positions = await self.trading_client.get_open_positions(
                auto_trade_only=True
            )

            if not positions:
                self.logger.debug("ℹ️  No open auto-traded positions")
                return

            self.logger.info(f"📊 Monitoring {len(positions)} open positions")

            # Get database session for config lookups
            session_maker = get_session_maker()
            async with session_maker() as session:
                config_repo = AutoTradingConfigRepository(session)
                session_repo = AutoTradingSessionRepository(session)

                # Monitor each position
                for position in positions:
                    try:
                        await self._monitor_position(position, config_repo, session_repo)
                        self.positions_monitored += 1

                    except Exception as e:
                        self.logger.error(
                            f"❌ Error monitoring position {position.get('id')}: {e}",
                            exc_info=True
                        )
                        # Continue with other positions

        except Exception as e:
            self.logger.error(f"❌ Error in position monitoring: {e}", exc_info=True)

    async def _monitor_position(self, position, config_repo, session_repo):
        """
        Monitor a single position for exit opportunities.

        Args:
            position: Position data
            config_repo: AutoTradingConfigRepository
            session_repo: AutoTradingSessionRepository
        """
        position_id = position.get('id')
        symbol = position.get('symbol')
        user_id = position.get('user_id')

        # Get configuration
        config = await config_repo.get_by_user_and_symbol(user_id, symbol)
        if not config or not config.enabled:
            self.logger.debug(f"⏸️  {symbol} auto-trading disabled, skipping")
            return

        # 1. Get current market price
        quote = await self.market_data_client.get_latest_quote(symbol)
        if not quote:
            self.logger.warning(f"⚠️  No quote available for {symbol}")
            return

        current_price = quote.get('price')

        # 2. Calculate current P&L
        pnl_data = await self.trading_client.calculate_pnl(
            position_id=position_id,
            current_price=current_price
        )

        if not pnl_data:
            self.logger.warning(f"⚠️  Cannot calculate P&L for {symbol}")
            return

        pnl_percent = pnl_data.get('pnl_percent', 0.0)

        self.logger.debug(
            f"📊 {symbol} position: P&L {pnl_percent:+.2f}% @ ${current_price}"
        )

        # 3. Get latest technical analysis
        technical_analysis = await self.technical_analyst_client.analyze(
            symbol=symbol,
            timeframes=["5m", "15m", "1h"],
            include_reasoning=True
        )

        if not technical_analysis:
            self.logger.warning(f"⚠️  No technical analysis for {symbol}")
            return

        # 4. Make autonomous exit decision
        decision = await self.decision_engine.evaluate_exit_signal(
            position=position,
            current_price=current_price,
            pnl_data=pnl_data,
            technical_analysis=technical_analysis,
            config=config
        )

        # 5. Act on decision
        if decision.action == DecisionAction.CLOSE:
            self.logger.info(
                f"🔴 Closing {symbol}: {decision.reason} "
                f"(confidence: {decision.confidence}%)"
            )

            success = await self._execute_exit(
                position=position,
                decision=decision,
                pnl_data=pnl_data,
                session_repo=session_repo
            )

            if success:
                self.positions_closed += 1

                # Track type of exit
                exit_type = decision.metadata.get('exit_type')
                if exit_type == 'PROFIT_PROTECTION':
                    self.profit_protections += 1
                elif exit_type == 'STOP_LOSS':
                    self.stop_losses += 1

        elif decision.action == DecisionAction.ADJUST_STOP:
            self.logger.info(
                f"📈 Adjusting stop for {symbol}: ${decision.new_stop_loss:.2f}"
            )

            success = await self._adjust_stop_loss(
                position=position,
                decision=decision
            )

            if success:
                self.stops_adjusted += 1

        else:  # HOLD
            self.logger.debug(f"⏳ {symbol}: {decision.reason}")

    async def _execute_exit(self, position, decision, pnl_data, session_repo):
        """
        Execute position exit.

        Args:
            position: Position data
            decision: Decision object
            pnl_data: P&L data
            session_repo: AutoTradingSessionRepository

        Returns:
            True if exit executed successfully
        """
        position_id = position.get('id')
        symbol = position.get('symbol')
        user_id = position.get('user_id')

        try:
            # 1. Close position
            result = await self.executor_client.close_position(
                position_id=position_id,
                reason=decision.reason,
                confidence=decision.confidence
            )

            if not result:
                self.logger.error(f"❌ Failed to close position {symbol}")
                return False

            # 2. Update session stats
            session_id = position.get('metadata', {}).get('session_id')
            if session_id:
                pnl = pnl_data.get('pnl', 0.0)
                await session_repo.record_trade(session_id, pnl)

            # 3. Send notification
            await self.notification_client.send_trade_exit_notification(
                user_id=user_id,
                symbol=symbol,
                pnl=pnl_data.get('pnl', 0.0),
                pnl_percent=pnl_data.get('pnl_percent', 0.0),
                reason=decision.reason
            )

            self.logger.info(
                f"✅ Position closed for {symbol}: "
                f"{pnl_data.get('pnl_percent'):+.2f}% P&L"
            )

            return True

        except Exception as e:
            self.logger.error(f"❌ Error closing position {symbol}: {e}", exc_info=True)
            return False

    async def _adjust_stop_loss(self, position, decision):
        """
        Adjust stop-loss for a position.

        Args:
            position: Position data
            decision: Decision object

        Returns:
            True if adjustment successful
        """
        position_id = position.get('id')
        symbol = position.get('symbol')

        try:
            result = await self.executor_client.update_stop_loss(
                position_id=position_id,
                new_stop_loss=decision.new_stop_loss,
                reason="TRAILING_STOP"
            )

            if result:
                self.logger.info(
                    f"✅ Stop-loss adjusted for {symbol}: ${decision.new_stop_loss:.2f}"
                )
                return True
            else:
                self.logger.warning(f"⚠️  Failed to adjust stop for {symbol}")
                return False

        except Exception as e:
            self.logger.error(f"❌ Error adjusting stop for {symbol}: {e}", exc_info=True)
            return False

    async def stop(self):
        """Stop worker and close clients."""
        await super().stop()

        # Close HTTP clients
        await self.market_data_client.close()
        await self.technical_analyst_client.close()
        await self.executor_client.close()
        await self.trading_client.close()
        await self.notification_client.close()

    def get_stats(self):
        """Get worker statistics."""
        stats = super().get_stats()
        stats.update({
            "positions_monitored": self.positions_monitored,
            "positions_closed": self.positions_closed,
            "stops_adjusted": self.stops_adjusted,
            "profit_protections": self.profit_protections,
            "stop_losses": self.stop_losses
        })
        return stats
