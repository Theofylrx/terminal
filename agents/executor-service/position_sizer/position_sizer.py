"""
Position Sizer Service
Calculates optimal position sizes based on risk management parameters
"""

import logging
from typing import Optional, Tuple
from enum import Enum


class PositionSizeMethod(str, Enum):
    """Position sizing method."""
    FIXED_RISK = "fixed_risk"  # Risk fixed % of account
    FIXED_AMOUNT = "fixed_amount"  # Trade fixed dollar amount
    KELLY_CRITERION = "kelly_criterion"  # Kelly formula (requires win rate)


class PositionSizer:
    """
    Position sizing calculator.

    Calculates position sizes based on:
    - Account balance
    - Risk tolerance
    - Stop loss distance
    - Risk multipliers
    """

    def __init__(self):
        """Initialize position sizer."""
        self.logger = logging.getLogger(__name__)

    def calculate_position_size(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss_price: float,
        risk_per_trade_percent: float = 1.0,
        method: PositionSizeMethod = PositionSizeMethod.FIXED_RISK,
        risk_multiplier: float = 1.0,
        min_position_size_usd: float = 10.0,
        max_position_size_usd: float = 100000.0,
        win_rate: Optional[float] = None,
        reward_risk_ratio: Optional[float] = None
    ) -> Tuple[float, dict]:
        """
        Calculate optimal position size.

        Args:
            account_balance: Total account balance
            entry_price: Expected entry price
            stop_loss_price: Stop loss price
            risk_per_trade_percent: % of account to risk (default 1%)
            method: Position sizing method
            risk_multiplier: Multiplier from strategy (e.g., 1.5x for high confidence)
            min_position_size_usd: Minimum position size
            max_position_size_usd: Maximum position size
            win_rate: Win rate (0-1, for Kelly criterion)
            reward_risk_ratio: Reward/Risk ratio (for Kelly criterion)

        Returns:
            Tuple of (quantity, details_dict)

        Example:
            >>> sizer = PositionSizer()
            >>> qty, details = sizer.calculate_position_size(
            ...     account_balance=10000,
            ...     entry_price=50.0,
            ...     stop_loss_price=48.0,
            ...     risk_per_trade_percent=1.0
            ... )
            >>> print(f"Buy {qty} shares at $50")
        """
        try:
            # Validate inputs
            if account_balance <= 0:
                raise ValueError("Account balance must be positive")
            if entry_price <= 0:
                raise ValueError("Entry price must be positive")
            if stop_loss_price <= 0:
                raise ValueError("Stop loss price must be positive")
            if entry_price == stop_loss_price:
                raise ValueError("Entry price and stop loss cannot be the same")
            if risk_per_trade_percent <= 0 or risk_per_trade_percent > 100:
                raise ValueError("Risk per trade must be between 0 and 100")
            if risk_multiplier <= 0:
                raise ValueError("Risk multiplier must be positive")

            # Calculate stop loss distance (as %)
            stop_loss_distance_pct = abs(
                (entry_price - stop_loss_price) / entry_price
            ) * 100

            # Calculate position size based on method
            if method == PositionSizeMethod.FIXED_RISK:
                quantity, risk_amount = self._fixed_risk_sizing(
                    account_balance=account_balance,
                    entry_price=entry_price,
                    stop_loss_price=stop_loss_price,
                    risk_per_trade_percent=risk_per_trade_percent,
                    risk_multiplier=risk_multiplier
                )

            elif method == PositionSizeMethod.FIXED_AMOUNT:
                quantity, risk_amount = self._fixed_amount_sizing(
                    account_balance=account_balance,
                    entry_price=entry_price,
                    stop_loss_price=stop_loss_price,
                    risk_per_trade_percent=risk_per_trade_percent
                )

            elif method == PositionSizeMethod.KELLY_CRITERION:
                if win_rate is None or reward_risk_ratio is None:
                    raise ValueError("Kelly criterion requires win_rate and reward_risk_ratio")

                quantity, risk_amount = self._kelly_criterion_sizing(
                    account_balance=account_balance,
                    entry_price=entry_price,
                    stop_loss_price=stop_loss_price,
                    win_rate=win_rate,
                    reward_risk_ratio=reward_risk_ratio
                )

            else:
                raise ValueError(f"Unknown position sizing method: {method}")

            # Calculate position value
            position_value = quantity * entry_price

            # Apply min/max constraints
            if position_value < min_position_size_usd:
                self.logger.warning(
                    f"Position value ${position_value:.2f} below minimum ${min_position_size_usd:.2f}, "
                    f"adjusting to minimum"
                )
                position_value = min_position_size_usd
                quantity = position_value / entry_price

            if position_value > max_position_size_usd:
                self.logger.warning(
                    f"Position value ${position_value:.2f} above maximum ${max_position_size_usd:.2f}, "
                    f"adjusting to maximum"
                )
                position_value = max_position_size_usd
                quantity = position_value / entry_price

            # Recalculate after constraints
            position_value = quantity * entry_price
            risk_amount = quantity * abs(entry_price - stop_loss_price)
            risk_percent = (risk_amount / account_balance) * 100

            # Build details
            details = {
                "method": method.value,
                "account_balance": account_balance,
                "entry_price": entry_price,
                "stop_loss_price": stop_loss_price,
                "stop_loss_distance_pct": stop_loss_distance_pct,
                "quantity": quantity,
                "position_value": position_value,
                "risk_amount": risk_amount,
                "risk_percent": risk_percent,
                "risk_multiplier": risk_multiplier,
                "min_position_size_usd": min_position_size_usd,
                "max_position_size_usd": max_position_size_usd
            }

            self.logger.info(
                f"Position size calculated: {quantity:.8f} units "
                f"(${position_value:.2f}, ${risk_amount:.2f} at risk)"
            )

            return quantity, details

        except Exception as e:
            self.logger.error(f"Position size calculation failed: {e}")
            raise Exception(f"Position sizing error: {e}")

    def _fixed_risk_sizing(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss_price: float,
        risk_per_trade_percent: float,
        risk_multiplier: float
    ) -> Tuple[float, float]:
        """
        Fixed risk position sizing.

        Risk a fixed percentage of account balance on each trade.
        Formula: Position Size = (Account Balance × Risk %) / (Entry Price - Stop Loss)

        Args:
            account_balance: Account balance
            entry_price: Entry price
            stop_loss_price: Stop loss price
            risk_per_trade_percent: Risk percentage
            risk_multiplier: Risk multiplier from strategy

        Returns:
            Tuple of (quantity, risk_amount)
        """
        # Apply risk multiplier (e.g., 1.5x for high confidence trades)
        adjusted_risk_percent = risk_per_trade_percent * risk_multiplier

        # Calculate risk amount in dollars
        risk_amount = account_balance * (adjusted_risk_percent / 100)

        # Calculate position size
        # Risk Amount = Quantity × (Entry Price - Stop Loss)
        # Therefore: Quantity = Risk Amount / (Entry Price - Stop Loss)
        price_diff = abs(entry_price - stop_loss_price)
        quantity = risk_amount / price_diff

        return quantity, risk_amount

    def _fixed_amount_sizing(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss_price: float,
        risk_per_trade_percent: float
    ) -> Tuple[float, float]:
        """
        Fixed amount position sizing.

        Trade a fixed dollar amount each time.
        Formula: Position Size = (Account Balance × Risk %) / Entry Price

        Args:
            account_balance: Account balance
            entry_price: Entry price
            stop_loss_price: Stop loss price
            risk_per_trade_percent: Risk percentage (used as position size %)

        Returns:
            Tuple of (quantity, risk_amount)
        """
        # Calculate position value
        position_value = account_balance * (risk_per_trade_percent / 100)

        # Calculate quantity
        quantity = position_value / entry_price

        # Calculate actual risk
        risk_amount = quantity * abs(entry_price - stop_loss_price)

        return quantity, risk_amount

    def _kelly_criterion_sizing(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss_price: float,
        win_rate: float,
        reward_risk_ratio: float
    ) -> Tuple[float, float]:
        """
        Kelly Criterion position sizing.

        Optimal position sizing based on edge and odds.
        Formula: Kelly % = W - [(1 - W) / R]
        Where:
          W = Win rate (probability of winning)
          R = Reward/Risk ratio (average win / average loss)

        Args:
            account_balance: Account balance
            entry_price: Entry price
            stop_loss_price: Stop loss price
            win_rate: Win rate (0-1)
            reward_risk_ratio: Reward/Risk ratio

        Returns:
            Tuple of (quantity, risk_amount)
        """
        # Calculate Kelly percentage
        # Kelly % = W - [(1 - W) / R]
        kelly_percent = win_rate - ((1 - win_rate) / reward_risk_ratio)

        # Kelly can suggest negative sizing (no edge), clamp to 0
        if kelly_percent <= 0:
            self.logger.warning("Kelly criterion suggests no edge (negative sizing)")
            kelly_percent = 0.01  # Use minimal 1%

        # Kelly can be aggressive, use fractional Kelly (e.g., 0.25 Kelly)
        fractional_kelly = kelly_percent * 0.25  # Quarter Kelly for safety

        # Cap at 10% max
        fractional_kelly = min(fractional_kelly, 0.10)

        # Calculate risk amount
        risk_amount = account_balance * fractional_kelly

        # Calculate quantity
        price_diff = abs(entry_price - stop_loss_price)
        quantity = risk_amount / price_diff

        self.logger.info(
            f"Kelly sizing: win_rate={win_rate:.2%}, R/R={reward_risk_ratio:.2f}, "
            f"Kelly={kelly_percent:.2%}, Fractional={fractional_kelly:.2%}"
        )

        return quantity, risk_amount

    def calculate_stop_loss_from_atr(
        self,
        entry_price: float,
        atr: float,
        atr_multiplier: float = 2.0,
        side: str = "long"
    ) -> float:
        """
        Calculate stop loss price based on ATR (Average True Range).

        Args:
            entry_price: Entry price
            atr: Average True Range value
            atr_multiplier: ATR multiplier (e.g., 2.0 means 2 × ATR)
            side: Position side ("long" or "short")

        Returns:
            Stop loss price
        """
        stop_distance = atr * atr_multiplier

        if side.lower() == "long":
            stop_loss_price = entry_price - stop_distance
        else:  # short
            stop_loss_price = entry_price + stop_distance

        return stop_loss_price

    def calculate_take_profit_from_risk_reward(
        self,
        entry_price: float,
        stop_loss_price: float,
        risk_reward_ratio: float = 2.0,
        side: str = "long"
    ) -> float:
        """
        Calculate take profit price based on risk/reward ratio.

        Args:
            entry_price: Entry price
            stop_loss_price: Stop loss price
            risk_reward_ratio: Risk/Reward ratio (e.g., 2.0 means 2:1 R/R)
            side: Position side ("long" or "short")

        Returns:
            Take profit price
        """
        risk_distance = abs(entry_price - stop_loss_price)
        reward_distance = risk_distance * risk_reward_ratio

        if side.lower() == "long":
            take_profit_price = entry_price + reward_distance
        else:  # short
            take_profit_price = entry_price - reward_distance

        return take_profit_price
