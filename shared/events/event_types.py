"""
Event Type Definitions
Centralizes all event types used across the system
"""

from enum import Enum


class EventType(str, Enum):
    """
    All event types in the Terminal trading system.
    Use these constants instead of hardcoded strings.
    """

    # ========== MARKET DATA EVENTS ==========
    MARKET_DATA_TICK = "market.data.{symbol}.tick"
    MARKET_DATA_CANDLE = "market.data.{symbol}.{timeframe}"
    MARKET_DATA_ORDERBOOK = "market.data.{symbol}.orderbook"
    MARKET_DATA_TRADES = "market.data.{symbol}.trades"

    # ========== TECHNICAL ANALYSIS EVENTS ==========
    TECHNICAL_SIGNAL_GENERATED = "analysis.technical.{symbol}.signal"
    TECHNICAL_INDICATOR_UPDATED = "analysis.technical.{symbol}.indicator"
    TECHNICAL_PATTERN_DETECTED = "analysis.technical.{symbol}.pattern"

    # ========== FUNDAMENTAL ANALYSIS EVENTS ==========
    FUNDAMENTAL_NEWS_RECEIVED = "analysis.fundamental.{symbol}.news"
    FUNDAMENTAL_SENTIMENT_UPDATED = "analysis.fundamental.{symbol}.sentiment"
    FUNDAMENTAL_EVENT_SCHEDULED = "analysis.fundamental.{symbol}.event"

    # ========== EXECUTION EVENTS ==========
    ORDER_CREATED = "execution.order.created"
    ORDER_SUBMITTED = "execution.order.submitted"
    ORDER_FILLED = "execution.order.filled"
    ORDER_PARTIALLY_FILLED = "execution.order.partially_filled"
    ORDER_CANCELLED = "execution.order.cancelled"
    ORDER_REJECTED = "execution.order.rejected"
    ORDER_EXPIRED = "execution.order.expired"

    # ========== POSITION EVENTS ==========
    POSITION_OPENED = "position.opened"
    POSITION_UPDATED = "position.updated"
    POSITION_CLOSED = "position.closed"
    POSITION_LIQUIDATED = "position.liquidated"

    # ========== RISK MANAGEMENT EVENTS ==========
    RISK_LIMIT_WARNING = "risk.limit.warning"
    RISK_LIMIT_BREACHED = "risk.limit.breached"
    RISK_STOP_LOSS_TRIGGERED = "risk.stop_loss.triggered"
    RISK_TAKE_PROFIT_TRIGGERED = "risk.take_profit.triggered"
    RISK_CIRCUIT_BREAKER_ACTIVATED = "risk.circuit_breaker.activated"

    # ========== PORTFOLIO EVENTS ==========
    PORTFOLIO_UPDATED = "portfolio.updated"
    PORTFOLIO_REBALANCED = "portfolio.rebalanced"

    # ========== STRATEGY EVENTS ==========
    STRATEGY_STARTED = "strategy.started"
    STRATEGY_STOPPED = "strategy.stopped"
    STRATEGY_PAUSED = "strategy.paused"
    STRATEGY_RESUMED = "strategy.resumed"
    STRATEGY_ERROR = "strategy.error"

    # ========== SYSTEM EVENTS ==========
    SYSTEM_STARTED = "system.started"
    SYSTEM_STOPPED = "system.stopped"
    SYSTEM_HEALTH_CHECK = "system.health_check"
    SYSTEM_ERROR = "system.error"

    # ========== NOTIFICATION EVENTS ==========
    NOTIFICATION_ALERT = "notification.alert"
    NOTIFICATION_EMAIL = "notification.email"
    NOTIFICATION_SMS = "notification.sms"
    NOTIFICATION_TELEGRAM = "notification.telegram"

    @classmethod
    def format(cls, event_type: str, **kwargs) -> str:
        """
        Format event type with variables.

        Args:
            event_type: Event type with placeholders
            **kwargs: Values to replace placeholders

        Returns:
            Formatted event type

        Example:
            event = EventType.format(
                EventType.MARKET_DATA_CANDLE,
                symbol="BTCUSDT",
                timeframe="1m"
            )
            # Returns: "market.data.btcusdt.1m"
        """
        return event_type.format(**{k: v.lower() for k, v in kwargs.items()})


class EventPriority(str, Enum):
    """Event priority levels."""
    CRITICAL = "critical"  # System-critical events (circuit breakers, errors)
    HIGH = "high"          # Important events (order fills, risk alerts)
    MEDIUM = "medium"      # Normal events (signals, updates)
    LOW = "low"            # Background events (health checks, metrics)


class EventCategory(str, Enum):
    """Event categories for filtering and monitoring."""
    MARKET_DATA = "market_data"
    ANALYSIS = "analysis"
    EXECUTION = "execution"
    RISK = "risk"
    SYSTEM = "system"
    NOTIFICATION = "notification"
