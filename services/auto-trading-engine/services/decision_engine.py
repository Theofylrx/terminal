"""
Decision Engine
Core AI logic for autonomous trading decisions
"""

import logging
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass

from ..core.config import settings

logger = logging.getLogger("auto-trading-engine.decision_engine")


class DecisionAction(str, Enum):
    """Possible decision actions."""
    ENTER = "ENTER"
    HOLD = "HOLD"
    CLOSE = "CLOSE"
    ADJUST_STOP = "ADJUST_STOP"


@dataclass
class Decision:
    """Trading decision with reasoning."""
    action: DecisionAction
    confidence: float
    reason: str
    side: Optional[str] = None  # LONG/SHORT (for ENTER action)
    new_stop_loss: Optional[float] = None  # For ADJUST_STOP action
    risk_multiplier: float = 1.0  # Position size multiplier
    technical_confidence: Optional[float] = None
    fundamental_boost: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class DecisionEngine:
    """
    Decision Engine for autonomous trading.

    Makes intelligent entry/exit decisions based on:
    - Technical analysis signals
    - Fundamental analysis (optional)
    - Position P&L and market conditions
    - Risk management rules
    """

    def __init__(self):
        """Initialize Decision Engine."""
        self.logger = logger

    async def evaluate_entry_signal(
        self,
        symbol: str,
        technical_analysis: Dict[str, Any],
        fundamental_analysis: Optional[Dict[str, Any]],
        config: Any,  # AutoTradingConfig
        current_price: float
    ) -> Decision:
        """
        Evaluate if we should enter a trade.

        Args:
            symbol: Trading symbol
            technical_analysis: Technical analysis data from TA service
            fundamental_analysis: Fundamental data (optional)
            config: User's auto-trading configuration
            current_price: Current market price

        Returns:
            Decision object
        """
        self.logger.info(f"🤔 Evaluating entry signal for {symbol}")

        # 1. Check if fundamental filter enabled
        if fundamental_analysis and hasattr(config, 'use_fundamental_filter') and config.use_fundamental_filter:
            filter_result = self._apply_fundamental_filter(fundamental_analysis, config)

            if not filter_result['passed']:
                self.logger.info(f"❌ {symbol} failed fundamental filter: {filter_result['reason']}")
                return Decision(
                    action=DecisionAction.HOLD,
                    confidence=0.0,
                    reason=f"Fundamental filter failed: {filter_result['reason']}"
                )

        # 2. Check technical signal strength
        technical_confidence = technical_analysis.get('confidence', 0.0)
        technical_direction = technical_analysis.get('direction', 'NEUTRAL')

        if technical_confidence < config.entry_confidence_threshold:
            self.logger.info(
                f"❌ {symbol} technical confidence too low: "
                f"{technical_confidence}% < {config.entry_confidence_threshold}%"
            )
            return Decision(
                action=DecisionAction.HOLD,
                confidence=technical_confidence,
                reason=f"Technical confidence below threshold ({technical_confidence}% < {config.entry_confidence_threshold}%)",
                technical_confidence=technical_confidence
            )

        # 3. Apply fundamental confluence boost (if available)
        final_confidence = technical_confidence
        fundamental_boost = 0.0

        if fundamental_analysis:
            fundamental_boost = self._calculate_confluence_boost(
                fundamental_analysis,
                technical_analysis
            )
            final_confidence += fundamental_boost

            self.logger.info(
                f"📊 Confidence boost for {symbol}: "
                f"{technical_confidence}% + {fundamental_boost}% = {final_confidence}%"
            )

        # 4. Calculate risk multiplier based on fundamentals
        risk_multiplier = 1.0
        if fundamental_analysis:
            risk_multiplier = self._calculate_risk_multiplier(fundamental_analysis)

        # 5. Determine trading side
        side = "LONG" if technical_direction == "BULLISH" else "SHORT"

        # 6. Generate reasoning
        reasoning = self._generate_entry_reasoning(
            symbol,
            technical_analysis,
            fundamental_analysis,
            final_confidence,
            fundamental_boost,
            risk_multiplier
        )

        self.logger.info(
            f"✅ ENTER signal for {symbol}: {side} @ ${current_price} "
            f"(confidence: {final_confidence}%, risk_mult: {risk_multiplier}x)"
        )

        return Decision(
            action=DecisionAction.ENTER,
            confidence=final_confidence,
            reason=reasoning,
            side=side,
            risk_multiplier=risk_multiplier,
            technical_confidence=technical_confidence,
            fundamental_boost=fundamental_boost,
            metadata={
                "entry_price": current_price,
                "technical_direction": technical_direction,
                "patterns_detected": technical_analysis.get('patterns', [])
            }
        )

    async def evaluate_exit_signal(
        self,
        position: Dict[str, Any],
        current_price: float,
        pnl_data: Dict[str, Any],
        technical_analysis: Dict[str, Any],
        config: Any  # AutoTradingConfig
    ) -> Decision:
        """
        Make autonomous exit decision for an open position.

        Args:
            position: Position data
            current_price: Current market price
            pnl_data: P&L calculation data
            technical_analysis: Latest technical analysis
            config: User's auto-trading configuration

        Returns:
            Decision object (HOLD, CLOSE, or ADJUST_STOP)
        """
        symbol = position.get('symbol')
        position_side = position.get('side')
        pnl_percent = pnl_data.get('pnl_percent', 0.0)

        self.logger.info(
            f"🤔 Evaluating exit for {symbol} position "
            f"(P&L: {pnl_percent:+.2f}%)"
        )

        # Get technical indicators
        direction = technical_analysis.get('direction', 'NEUTRAL')
        correction_probability = technical_analysis.get('correction_probability', 0.0)
        reversal_probability = technical_analysis.get('reversal_probability', 0.0)

        # SCENARIO 1: In Profit + Correction Detected
        if pnl_percent > 0 and correction_probability > 0.7 and config.auto_close_on_correction:
            reasoning = (
                f"Position in profit (+{pnl_percent:.2f}%). "
                f"Correction probability {correction_probability*100:.0f}%. "
                f"Protecting profit by closing."
            )
            self.logger.info(f"💰 CLOSE {symbol}: Profit protection (correction detected)")

            return Decision(
                action=DecisionAction.CLOSE,
                confidence=correction_probability * 100,
                reason=reasoning,
                metadata={"exit_type": "PROFIT_PROTECTION", "pnl_percent": pnl_percent}
            )

        # SCENARIO 2: In Profit + Trend Continues (Trailing Stop)
        if pnl_percent > 0 and self._trend_aligns_with_position(direction, position_side):
            if config.trailing_stop_enabled:
                new_stop = self._calculate_trailing_stop(
                    current_price,
                    position_side,
                    config.trailing_stop_percent
                )

                current_stop = position.get('stop_loss_price')

                # Only adjust if new stop is better
                should_adjust = (
                    (position_side == 'LONG' and new_stop > current_stop) or
                    (position_side == 'SHORT' and new_stop < current_stop)
                )

                if should_adjust:
                    reasoning = (
                        f"Position in profit (+{pnl_percent:.2f}%), trend continues. "
                        f"Adjusting trailing stop to ${new_stop:.2f}."
                    )
                    self.logger.info(f"📈 ADJUST_STOP {symbol}: Trailing stop to ${new_stop:.2f}")

                    return Decision(
                        action=DecisionAction.ADJUST_STOP,
                        confidence=80.0,
                        reason=reasoning,
                        new_stop_loss=new_stop,
                        metadata={"previous_stop": current_stop}
                    )

        # SCENARIO 3: In Loss + Reversal Likely (Hold)
        if pnl_percent < 0 and reversal_probability > 0.6:
            reasoning = (
                f"Position in loss ({pnl_percent:+.2f}%), but reversal likely "
                f"({reversal_probability*100:.0f}%). Holding for recovery."
            )
            self.logger.info(f"⏳ HOLD {symbol}: Potential reversal detected")

            return Decision(
                action=DecisionAction.HOLD,
                confidence=reversal_probability * 100,
                reason=reasoning
            )

        # SCENARIO 4: In Loss + No Recovery Signal (Cut Loss)
        if pnl_percent < 0 and not reversal_probability > 0.5:
            max_loss_percent = config.stop_loss_percent
            if abs(pnl_percent) >= max_loss_percent * 0.8:  # 80% of max loss
                reasoning = (
                    f"Position in loss ({pnl_percent:+.2f}%), approaching max loss "
                    f"({max_loss_percent}%). No reversal signal. Cutting loss."
                )
                self.logger.info(f"🔴 CLOSE {symbol}: Stop loss (no recovery signal)")

                return Decision(
                    action=DecisionAction.CLOSE,
                    confidence=80.0,
                    reason=reasoning,
                    metadata={"exit_type": "STOP_LOSS", "pnl_percent": pnl_percent}
                )

        # SCENARIO 5: Strong Opposite Trend (Immediate Exit)
        if not self._trend_aligns_with_position(direction, position_side):
            if abs(pnl_percent) > 1.0 or correction_probability > 0.6:
                reasoning = (
                    f"Strong opposite trend detected ({direction} vs {position_side}). "
                    f"Exiting position to prevent further loss."
                )
                self.logger.info(f"🔴 CLOSE {symbol}: Strong opposite trend")

                return Decision(
                    action=DecisionAction.CLOSE,
                    confidence=75.0,
                    reason=reasoning,
                    metadata={"exit_type": "TREND_REVERSAL", "pnl_percent": pnl_percent}
                )

        # DEFAULT: HOLD
        reasoning = f"Position within acceptable range ({pnl_percent:+.2f}%). Continuing to monitor."
        self.logger.debug(f"⏳ HOLD {symbol}: Monitoring")

        return Decision(
            action=DecisionAction.HOLD,
            confidence=60.0,
            reason=reasoning
        )

    def _apply_fundamental_filter(
        self,
        fundamental: Dict[str, Any],
        config: Any
    ) -> Dict[str, Any]:
        """Apply fundamental screening filter."""
        reasons = []

        # Check fundamental score
        score = fundamental.get('fundamental_score', 0)
        if score < config.min_fundamental_score:
            reasons.append(f"Low fundamental score: {score}/100")

        # Check earnings blackout
        days_until_earnings = fundamental.get('days_until_earnings', 999)
        if days_until_earnings <= config.earnings_blackout_days:
            reasons.append(f"Earnings in {days_until_earnings} days (blackout period)")

        # Check sentiment
        sentiment = fundamental.get('sentiment_score', 0)
        if sentiment < config.min_sentiment_score:
            reasons.append(f"Negative sentiment: {sentiment}")

        # Check financial health
        debt_to_equity = fundamental.get('debt_to_equity', 0)
        if debt_to_equity > 3.0:
            reasons.append(f"High debt/equity: {debt_to_equity}")

        passed = len(reasons) == 0

        return {
            'passed': passed,
            'reason': "; ".join(reasons) if not passed else "All checks passed"
        }

    def _calculate_confluence_boost(
        self,
        fundamental: Dict[str, Any],
        technical: Dict[str, Any]
    ) -> float:
        """Calculate confidence boost from fundamental confluence."""
        boost = 0.0

        # Fundamental score boost
        score = fundamental.get('fundamental_score', 0)
        if score >= 80:
            boost += settings.FUNDAMENTAL_SCORE_HIGH_BOOST
        elif score >= 70:
            boost += settings.FUNDAMENTAL_SCORE_MED_BOOST

        # Analyst rating boost
        rating = fundamental.get('analyst_rating', '')
        if rating == "Strong Buy":
            boost += settings.ANALYST_STRONG_BUY_BOOST
        elif rating == "Buy":
            boost += settings.ANALYST_BUY_BOOST

        # Sentiment boost
        sentiment = fundamental.get('sentiment_score', 0)
        if sentiment >= 0.5:
            boost += settings.SENTIMENT_HIGH_BOOST
        elif sentiment >= 0.3:
            boost += settings.SENTIMENT_MED_BOOST

        # Growth boost
        revenue_growth = fundamental.get('revenue_growth_yoy', 0)
        if revenue_growth >= 0.20:  # 20%+
            boost += settings.REVENUE_GROWTH_BOOST

        # Penalties
        days_until_earnings = fundamental.get('days_until_earnings', 999)
        if days_until_earnings <= 3:
            boost += settings.EARNINGS_SOON_PENALTY
        elif days_until_earnings <= 7:
            boost += settings.EARNINGS_APPROACHING_PENALTY

        if sentiment < -0.3:
            boost += settings.NEGATIVE_SENTIMENT_PENALTY

        debt_to_equity = fundamental.get('debt_to_equity', 0)
        if debt_to_equity > 2.5:
            boost += settings.HIGH_DEBT_PENALTY

        return boost

    def _calculate_risk_multiplier(self, fundamental: Dict[str, Any]) -> float:
        """Calculate position size multiplier based on fundamental strength."""
        score = fundamental.get('fundamental_score', 50)

        if score >= 80:
            return 1.2  # Increase position 20%
        elif score >= 60:
            return 1.0  # Standard position
        elif score >= 40:
            return 0.8  # Reduce position 20%
        else:
            return 0.5  # Minimal position

    def _trend_aligns_with_position(self, trend_direction: str, position_side: str) -> bool:
        """Check if trend aligns with position direction."""
        if position_side == "LONG":
            return trend_direction == "BULLISH"
        else:  # SHORT
            return trend_direction == "BEARISH"

    def _calculate_trailing_stop(
        self,
        current_price: float,
        position_side: str,
        trailing_percent: float
    ) -> float:
        """Calculate trailing stop price."""
        trail_amount = current_price * (trailing_percent / 100)

        if position_side == "LONG":
            return current_price - trail_amount
        else:  # SHORT
            return current_price + trail_amount

    def _generate_entry_reasoning(
        self,
        symbol: str,
        technical: Dict[str, Any],
        fundamental: Optional[Dict[str, Any]],
        final_confidence: float,
        fundamental_boost: float,
        risk_multiplier: float
    ) -> str:
        """Generate human-readable entry reasoning."""
        lines = [
            f"Strong {technical.get('direction', 'BULLISH').lower()} signal detected on {symbol}.",
            f"Technical confidence: {technical.get('confidence')}%."
        ]

        # Add patterns
        patterns = technical.get('patterns', [])
        if patterns:
            pattern_names = [p.get('type', '') for p in patterns[:3]]
            lines.append(f"Patterns: {', '.join(pattern_names)}.")

        # Add fundamental boost
        if fundamental and fundamental_boost != 0:
            if fundamental_boost > 0:
                lines.append(f"Fundamental analysis boosts confidence by +{fundamental_boost}%.")
            else:
                lines.append(f"Fundamental concerns reduce confidence by {fundamental_boost}%.")

            score = fundamental.get('fundamental_score', 0)
            lines.append(f"Fundamental score: {score}/100.")

        # Add risk adjustment
        if risk_multiplier != 1.0:
            if risk_multiplier > 1.0:
                lines.append(f"Strong fundamentals justify {risk_multiplier}x position size.")
            else:
                lines.append(f"Weak fundamentals warrant reduced {risk_multiplier}x position size.")

        lines.append(f"Final confidence: {final_confidence:.1f}%.")

        return " ".join(lines)
