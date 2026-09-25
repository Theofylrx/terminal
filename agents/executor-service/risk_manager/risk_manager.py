"""
Risk Manager Service
Validates orders against risk management rules before execution
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime, timedelta


@dataclass
class RiskCheckResult:
    """Result of a risk check."""
    approved: bool
    risk_score: float  # 0-100, lower is safer
    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)


class RiskManager:
    """
    Risk management service.

    Validates orders against:
    - Position limits
    - Account risk limits
    - Daily loss limits
    - Margin usage
    - Account balance requirements
    """

    def __init__(
        self,
        max_risk_per_trade_percent: float = 5.0,
        max_account_risk_percent: float = 20.0,
        max_positions_per_symbol: int = 1,
        max_total_positions: int = 10,
        max_daily_loss_percent: float = 5.0,
        max_daily_trades: int = 50,
        min_account_balance: float = 1000.0,
        margin_usage_limit_percent: float = 80.0,
        emergency_shutdown_loss_percent: float = 10.0
    ):
        """
        Initialize risk manager.

        Args:
            max_risk_per_trade_percent: Max risk per single trade (%)
            max_account_risk_percent: Max total account risk (%)
            max_positions_per_symbol: Max positions in same symbol
            max_total_positions: Max total open positions
            max_daily_loss_percent: Max daily loss (%)
            max_daily_trades: Max trades per day
            min_account_balance: Minimum account balance required
            margin_usage_limit_percent: Maximum margin usage (%)
            emergency_shutdown_loss_percent: Emergency shutdown threshold (%)
        """
        self.logger = logging.getLogger(__name__)

        # Risk limits
        self.max_risk_per_trade_percent = max_risk_per_trade_percent
        self.max_account_risk_percent = max_account_risk_percent
        self.max_positions_per_symbol = max_positions_per_symbol
        self.max_total_positions = max_total_positions
        self.max_daily_loss_percent = max_daily_loss_percent
        self.max_daily_trades = max_daily_trades
        self.min_account_balance = min_account_balance
        self.margin_usage_limit_percent = margin_usage_limit_percent
        self.emergency_shutdown_loss_percent = emergency_shutdown_loss_percent

    async def check_risk(
        self,
        user_id: str,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        stop_loss_price: Optional[float],
        account_balance: float,
        open_positions: List[dict],
        daily_trades_count: int = 0,
        daily_pnl: float = 0.0,
        margin_used: float = 0.0
    ) -> RiskCheckResult:
        """
        Perform comprehensive risk check on an order.

        Args:
            user_id: User ID
            symbol: Trading symbol
            side: BUY or SELL
            quantity: Quantity to trade
            entry_price: Entry price
            stop_loss_price: Stop loss price (optional)
            account_balance: Current account balance
            open_positions: List of open positions
            daily_trades_count: Number of trades today
            daily_pnl: P&L for today
            margin_used: Currently used margin

        Returns:
            RiskCheckResult with approval status and details
        """
        violations = []
        warnings = []
        risk_score = 0.0

        try:
            self.logger.info(f"Running risk check for {user_id}: {symbol} {side} {quantity}")

            # 1. Account balance check
            if account_balance < self.min_account_balance:
                violations.append(
                    f"Account balance ${account_balance:.2f} below minimum ${self.min_account_balance:.2f}"
                )
                risk_score += 30

            # 2. Position risk check
            position_value = quantity * entry_price
            position_risk = 0.0

            if stop_loss_price:
                position_risk = quantity * abs(entry_price - stop_loss_price)
                position_risk_percent = (position_risk / account_balance) * 100

                if position_risk_percent > self.max_risk_per_trade_percent:
                    violations.append(
                        f"Position risk {position_risk_percent:.2f}% exceeds max {self.max_risk_per_trade_percent}%"
                    )
                    risk_score += 25
                elif position_risk_percent > self.max_risk_per_trade_percent * 0.8:
                    warnings.append(
                        f"Position risk {position_risk_percent:.2f}% approaching max {self.max_risk_per_trade_percent}%"
                    )
                    risk_score += 10

            else:
                warnings.append("No stop loss provided - undefined risk")
                risk_score += 15

            # 3. Total account risk check
            total_account_risk = position_risk
            for pos in open_positions:
                if pos.get("stop_loss_price"):
                    pos_risk = abs(pos["quantity"] * (pos["entry_price"] - pos["stop_loss_price"]))
                    total_account_risk += pos_risk

            total_account_risk_percent = (total_account_risk / account_balance) * 100

            if total_account_risk_percent > self.max_account_risk_percent:
                violations.append(
                    f"Total account risk {total_account_risk_percent:.2f}% exceeds max {self.max_account_risk_percent}%"
                )
                risk_score += 20
            elif total_account_risk_percent > self.max_account_risk_percent * 0.8:
                warnings.append(
                    f"Total account risk {total_account_risk_percent:.2f}% approaching max"
                )
                risk_score += 10

            # 4. Position count checks
            positions_count = len(open_positions)

            # Total positions limit
            if positions_count >= self.max_total_positions:
                violations.append(
                    f"Already at max positions ({positions_count}/{self.max_total_positions})"
                )
                risk_score += 20

            # Positions in same symbol limit
            positions_in_symbol = sum(
                1 for pos in open_positions
                if pos["symbol"] == symbol and pos["status"] == "OPEN"
            )

            if positions_in_symbol >= self.max_positions_per_symbol:
                violations.append(
                    f"Already at max positions for {symbol} ({positions_in_symbol}/{self.max_positions_per_symbol})"
                )
                risk_score += 15

            # 5. Daily loss limit check
            daily_loss_percent = abs(daily_pnl / account_balance) * 100

            if daily_pnl < 0 and daily_loss_percent >= self.max_daily_loss_percent:
                violations.append(
                    f"Daily loss {daily_loss_percent:.2f}% exceeds max {self.max_daily_loss_percent}%"
                )
                risk_score += 30
            elif daily_pnl < 0 and daily_loss_percent >= self.max_daily_loss_percent * 0.8:
                warnings.append(
                    f"Daily loss {daily_loss_percent:.2f}% approaching max"
                )
                risk_score += 15

            # 6. Emergency shutdown check
            if daily_pnl < 0 and daily_loss_percent >= self.emergency_shutdown_loss_percent:
                violations.append(
                    f"EMERGENCY SHUTDOWN: Daily loss {daily_loss_percent:.2f}% exceeds emergency threshold {self.emergency_shutdown_loss_percent}%"
                )
                risk_score += 50

            # 7. Daily trades limit check
            if daily_trades_count >= self.max_daily_trades:
                violations.append(
                    f"Daily trades limit reached ({daily_trades_count}/{self.max_daily_trades})"
                )
                risk_score += 20
            elif daily_trades_count >= self.max_daily_trades * 0.9:
                warnings.append(
                    f"Daily trades approaching limit ({daily_trades_count}/{self.max_daily_trades})"
                )
                risk_score += 5

            # 8. Margin usage check
            projected_margin = margin_used + (position_value * 0.5)  # Assume 50% margin requirement
            margin_usage_percent = (projected_margin / account_balance) * 100

            if margin_usage_percent > self.margin_usage_limit_percent:
                violations.append(
                    f"Margin usage {margin_usage_percent:.2f}% exceeds max {self.margin_usage_limit_percent}%"
                )
                risk_score += 25
            elif margin_usage_percent > self.margin_usage_limit_percent * 0.8:
                warnings.append(
                    f"Margin usage {margin_usage_percent:.2f}% approaching max"
                )
                risk_score += 10

            # 9. Position size sanity check
            position_size_percent = (position_value / account_balance) * 100

            if position_size_percent > 50:  # Position > 50% of account
                warnings.append(
                    f"Large position size: {position_size_percent:.2f}% of account"
                )
                risk_score += 10
            elif position_size_percent > 80:  # Position > 80% of account
                violations.append(
                    f"Excessive position size: {position_size_percent:.2f}% of account"
                )
                risk_score += 20

            # Determine approval
            approved = len(violations) == 0

            # Build metrics
            metrics = {
                "position_risk_percent": position_risk_percent if stop_loss_price else 0.0,
                "total_account_risk_percent": total_account_risk_percent,
                "margin_usage_percent": margin_usage_percent,
                "positions_count": positions_count,
                "max_positions_allowed": self.max_total_positions,
                "positions_in_symbol": positions_in_symbol,
                "daily_trades_count": daily_trades_count,
                "daily_loss_percent": daily_loss_percent,
                "position_size_percent": position_size_percent
            }

            result = RiskCheckResult(
                approved=approved,
                risk_score=min(risk_score, 100.0),  # Cap at 100
                violations=violations,
                warnings=warnings,
                metrics=metrics
            )

            if approved:
                self.logger.info(
                    f"Risk check PASSED for {symbol} (risk score: {result.risk_score:.1f})"
                )
            else:
                self.logger.warning(
                    f"Risk check FAILED for {symbol}: {len(violations)} violations"
                )

            return result

        except Exception as e:
            self.logger.error(f"Risk check error: {e}")
            return RiskCheckResult(
                approved=False,
                risk_score=100.0,
                violations=[f"Risk check error: {str(e)}"],
                warnings=[],
                metrics={}
            )

    def is_emergency_shutdown_triggered(
        self,
        account_balance: float,
        daily_pnl: float
    ) -> bool:
        """
        Check if emergency shutdown should be triggered.

        Args:
            account_balance: Current account balance
            daily_pnl: Daily P&L

        Returns:
            True if emergency shutdown should trigger
        """
        if daily_pnl >= 0:
            return False

        daily_loss_percent = abs(daily_pnl / account_balance) * 100
        return daily_loss_percent >= self.emergency_shutdown_loss_percent

    def calculate_max_position_size(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss_price: float
    ) -> float:
        """
        Calculate maximum allowed position size.

        Args:
            account_balance: Account balance
            entry_price: Entry price
            stop_loss_price: Stop loss price

        Returns:
            Maximum quantity allowed
        """
        max_risk_amount = account_balance * (self.max_risk_per_trade_percent / 100)
        price_diff = abs(entry_price - stop_loss_price)

        if price_diff == 0:
            return 0.0

        max_quantity = max_risk_amount / price_diff
        return max_quantity
