"""
Symbol Monitor Worker
Monitors enabled symbols for entry signals
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


class SymbolMonitorWorker(BaseWorker):
    """
    Symbol Monitor Worker.

    Continuously monitors all enabled symbols for entry opportunities.

    Flow:
    1. Get all enabled auto-trading configurations
    2. For each symbol:
       - Request latest quote from Market Data Service
       - Request technical analysis from Technical Analyst Service
       - Request fundamental analysis (if enabled)
       - Evaluate entry signal using Decision Engine
       - If signal is strong enough, execute trade via Executor Service
    3. Sleep and repeat
    """

    def __init__(self):
        """Initialize Symbol Monitor Worker."""
        super().__init__(
            name="SymbolMonitor",
            interval_seconds=settings.SYMBOL_MONITOR_INTERVAL_SECONDS
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
        self.symbols_monitored = 0
        self.signals_detected = 0
        self.trades_executed = 0
        self.trades_rejected = 0

    async def run(self):
        """Run one iteration of symbol monitoring."""
        self.logger.debug("🔍 Monitoring enabled symbols...")

        try:
            # Get database session
            session_maker = get_session_maker()
            async with session_maker() as session:
                config_repo = AutoTradingConfigRepository(session)
                session_repo = AutoTradingSessionRepository(session)

                # Get all enabled configurations
                configs = await config_repo.get_all_enabled()

                if not configs:
                    self.logger.debug("ℹ️  No enabled symbols to monitor")
                    return

                self.logger.info(f"📊 Monitoring {len(configs)} enabled symbols")

                # Monitor each symbol
                for config in configs:
                    try:
                        await self._monitor_symbol(config, session_repo)
                        self.symbols_monitored += 1

                    except Exception as e:
                        self.logger.error(
                            f"❌ Error monitoring {config.symbol}: {e}",
                            exc_info=True
                        )
                        # Continue with other symbols

        except Exception as e:
            self.logger.error(f"❌ Error in symbol monitoring: {e}", exc_info=True)

    async def _monitor_symbol(self, config, session_repo):
        """
        Monitor a single symbol for entry opportunities.

        Args:
            config: AutoTradingConfig
            session_repo: AutoTradingSessionRepository
        """
        symbol = config.symbol

        # Check if within trading hours
        from datetime import datetime
        current_hour = datetime.utcnow().hour
        if not config.is_within_trading_hours(current_hour):
            self.logger.debug(f"⏰ {symbol} outside trading hours")
            return

        # Check if we've hit max concurrent positions
        open_positions = await self.trading_client.get_open_positions(
            user_id=config.user_id,
            auto_trade_only=True
        )

        if len(open_positions) >= config.max_concurrent_positions:
            self.logger.debug(
                f"📊 {symbol} max concurrent positions reached "
                f"({len(open_positions)}/{config.max_concurrent_positions})"
            )
            return

        # 1. Get latest market price
        quote = await self.market_data_client.get_latest_quote(symbol)
        if not quote:
            self.logger.warning(f"⚠️  No quote available for {symbol}")
            return

        current_price = quote.get('price')

        # 2. Get technical analysis
        technical_analysis = await self.technical_analyst_client.analyze(
            symbol=symbol,
            timeframes=["5m", "15m", "1h"],
            include_reasoning=True
        )

        if not technical_analysis:
            self.logger.warning(f"⚠️  No technical analysis for {symbol}")
            return

        # 3. Get fundamental analysis (if enabled)
        fundamental_analysis = None
        # TODO: Call fundamental analyst service when implemented
        # if config.use_fundamental_filter:
        #     fundamental_analysis = await fundamental_analyst_client.analyze(symbol)

        # 4. Evaluate entry signal using Decision Engine
        decision = await self.decision_engine.evaluate_entry_signal(
            symbol=symbol,
            technical_analysis=technical_analysis,
            fundamental_analysis=fundamental_analysis,
            config=config,
            current_price=current_price
        )

        # 5. Act on decision
        if decision.action == DecisionAction.ENTER:
            self.signals_detected += 1
            self.logger.info(
                f"🎯 Entry signal detected for {symbol}: {decision.side} "
                f"(confidence: {decision.confidence}%)"
            )

            # Execute trade
            success = await self._execute_entry(
                config=config,
                decision=decision,
                current_price=current_price,
                session_repo=session_repo
            )

            if success:
                self.trades_executed += 1
            else:
                self.trades_rejected += 1

        else:
            self.logger.debug(f"⏳ {symbol}: {decision.reason}")

    async def _execute_entry(
        self,
        config,
        decision,
        current_price: float,
        session_repo
    ):
        """
        Execute trade entry.

        Args:
            config: AutoTradingConfig
            decision: Decision object
            current_price: Current market price
            session_repo: AutoTradingSessionRepository

        Returns:
            True if trade executed successfully
        """
        symbol = config.symbol

        try:
            # 1. Get user capital
            capital = await self.trading_client.get_user_capital(config.user_id)
            if not capital:
                self.logger.error(f"❌ Cannot get capital for user {config.user_id}")
                return False

            # 2. Calculate position size (with risk multiplier from decision)
            base_risk_percent = config.risk_per_trade_percent * decision.risk_multiplier

            position_size = await self.executor_client.calculate_position_size(
                user_id=config.user_id,
                symbol=symbol,
                entry_price=current_price,
                risk_percent=base_risk_percent,
                stop_loss_percent=config.stop_loss_percent
            )

            if not position_size:
                self.logger.error(f"❌ Cannot calculate position size for {symbol}")
                return False

            # 3. Execute market order
            order = await self.executor_client.execute_market_order(
                user_id=config.user_id,
                symbol=symbol,
                side=decision.side,
                quantity=position_size['quantity'],
                stop_loss=position_size.get('stop_loss_price'),
                take_profit=position_size.get('take_profit_price'),
                metadata={
                    'auto_trade': True,
                    'config_id': config.id,
                    'signal_confidence': decision.confidence,
                    'technical_confidence': decision.technical_confidence,
                    'fundamental_boost': decision.fundamental_boost,
                    'risk_multiplier': decision.risk_multiplier,
                    'reasoning': decision.reason
                }
            )

            if not order:
                self.logger.error(f"❌ Failed to execute order for {symbol}")
                return False

            # 4. Get or create session
            session = await session_repo.get_by_config(config.id)
            if session:
                await session_repo.update_activity(session.id)
            # else: Session will be created when needed

            # 5. Send notification
            await self.notification_client.send_trade_entry_notification(
                user_id=config.user_id,
                symbol=symbol,
                side=decision.side,
                quantity=position_size['quantity'],
                entry_price=current_price,
                confidence=decision.confidence
            )

            self.logger.info(
                f"✅ Trade executed for {symbol}: {decision.side} "
                f"{position_size['quantity']} units @ ${current_price}"
            )

            return True

        except Exception as e:
            self.logger.error(f"❌ Error executing trade for {symbol}: {e}", exc_info=True)
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
            "symbols_monitored": self.symbols_monitored,
            "signals_detected": self.signals_detected,
            "trades_executed": self.trades_executed,
            "trades_rejected": self.trades_rejected
        })
        return stats
