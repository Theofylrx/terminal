"""Signal generation service."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
import pandas as pd

# Add shared to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.database.models.signal import Signal, SignalType, SignalStatus

from ..indicators.calculator import IndicatorCalculator
from ..patterns.detector import PatternDetector
from ..patterns.models import PatternSignal
from ..core.config import settings


logger = logging.getLogger(__name__)


class SignalGenerator:
    """
    Trading signal generator.

    Combines technical indicators and pattern detection to generate
    trading signals with confidence scores.
    """

    def __init__(self):
        """Initialize signal generator."""
        self.indicator_calc = IndicatorCalculator()
        self.pattern_detector = PatternDetector()

    async def generate_signal(
        self,
        symbol: str,
        timeframe: str,
        df: pd.DataFrame,
    ) -> Optional[Signal]:
        """
        Generate trading signal from price data.

        Args:
            symbol: Trading symbol.
            timeframe: Timeframe.
            df: DataFrame with OHLCV data (columns: open, high, low, close, volume, timestamp).

        Returns:
            Signal object if conditions met, None otherwise.
        """
        if len(df) < 50:  # Need enough data for indicators
            logger.warning(f"Insufficient data for {symbol} ({len(df)} bars)")
            return None

        try:
            # Calculate indicators
            indicators = self._calculate_indicators(df)

            # Detect patterns
            patterns = self.pattern_detector.scan_patterns(df, symbol, timeframe)

            # Generate signal from indicators and patterns
            signal = self._combine_signals(symbol, timeframe, df, indicators, patterns)

            return signal

        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {e}")
            return None

    def _calculate_indicators(self, df: pd.DataFrame) -> dict:
        """Calculate all technical indicators."""
        close = df['close']
        high = df['high']
        low = df['low']
        volume = df['volume']

        indicators = {}

        # RSI
        rsi = self.indicator_calc.calculate_rsi(close, settings.RSI_PERIOD)
        indicators['rsi'] = rsi.iloc[-1] if not rsi.empty else None

        # MACD
        macd_df = self.indicator_calc.calculate_macd(
            close,
            settings.MACD_FAST,
            settings.MACD_SLOW,
            settings.MACD_SIGNAL,
        )
        indicators['macd_line'] = macd_df['macd_line'].iloc[-1] if not macd_df.empty else None
        indicators['macd_signal'] = macd_df['signal_line'].iloc[-1] if not macd_df.empty else None
        indicators['macd_histogram'] = macd_df['histogram'].iloc[-1] if not macd_df.empty else None

        # Bollinger Bands
        bb_df = self.indicator_calc.calculate_bollinger_bands(
            close,
            settings.BB_PERIOD,
            settings.BB_STD_DEV,
        )
        indicators['bb_upper'] = bb_df['upper_band'].iloc[-1] if not bb_df.empty else None
        indicators['bb_middle'] = bb_df['middle_band'].iloc[-1] if not bb_df.empty else None
        indicators['bb_lower'] = bb_df['lower_band'].iloc[-1] if not bb_df.empty else None
        indicators['bb_percent_b'] = bb_df['percent_b'].iloc[-1] if not bb_df.empty else None

        # Moving Averages
        indicators['ema_9'] = self.indicator_calc.calculate_ema(close, 9).iloc[-1]
        indicators['ema_21'] = self.indicator_calc.calculate_ema(close, 21).iloc[-1]
        indicators['sma_50'] = self.indicator_calc.calculate_sma(close, 50).iloc[-1]

        # ATR (volatility)
        atr = self.indicator_calc.calculate_atr(high, low, close, settings.ATR_PERIOD)
        indicators['atr'] = atr.iloc[-1] if not atr.empty else None

        return indicators

    def _combine_signals(
        self,
        symbol: str,
        timeframe: str,
        df: pd.DataFrame,
        indicators: dict,
        patterns: list,
    ) -> Optional[Signal]:
        """
        Combine indicator and pattern signals to generate final signal.

        Args:
            symbol: Trading symbol.
            timeframe: Timeframe.
            df: Price data DataFrame.
            indicators: Calculated indicators.
            patterns: Detected patterns.

        Returns:
            Signal object if conditions met.
        """
        current_price = df['close'].iloc[-1]
        bullish_score = 0
        bearish_score = 0
        reasons = []

        # RSI signals
        if indicators.get('rsi'):
            if indicators['rsi'] < settings.RSI_OVERSOLD:
                bullish_score += 20
                reasons.append(f"RSI oversold ({indicators['rsi']:.1f})")
            elif indicators['rsi'] > settings.RSI_OVERBOUGHT:
                bearish_score += 20
                reasons.append(f"RSI overbought ({indicators['rsi']:.1f})")

        # MACD signals
        if indicators.get('macd_histogram'):
            # MACD crossover
            if indicators['macd_histogram'] > 0:
                if indicators['macd_line'] > indicators['macd_signal']:
                    bullish_score += 15
                    reasons.append("MACD bullish crossover")
            else:
                if indicators['macd_line'] < indicators['macd_signal']:
                    bearish_score += 15
                    reasons.append("MACD bearish crossover")

        # Bollinger Bands signals
        if indicators.get('bb_percent_b'):
            if indicators['bb_percent_b'] < 0.2:
                bullish_score += 15
                reasons.append("Price near lower Bollinger Band")
            elif indicators['bb_percent_b'] > 0.8:
                bearish_score += 15
                reasons.append("Price near upper Bollinger Band")

        # Moving Average signals
        if indicators.get('ema_9') and indicators.get('ema_21'):
            if indicators['ema_9'] > indicators['ema_21']:
                bullish_score += 10
                reasons.append("EMA 9 above EMA 21 (bullish trend)")
            else:
                bearish_score += 10
                reasons.append("EMA 9 below EMA 21 (bearish trend)")

        # Pattern signals
        for pattern in patterns:
            if pattern.signal == PatternSignal.BULLISH:
                bullish_score += pattern.confidence * 0.3  # 30% weight
                reasons.append(f"{pattern.pattern_type.value} pattern (bullish)")
            elif pattern.signal == PatternSignal.BEARISH:
                bearish_score += pattern.confidence * 0.3
                reasons.append(f"{pattern.pattern_type.value} pattern (bearish)")

        # Determine signal type and confidence
        if bullish_score > bearish_score and bullish_score >= settings.MIN_CONFIDENCE:
            signal_type = SignalType.BUY
            confidence = min(bullish_score, 100.0)
        elif bearish_score > bullish_score and bearish_score >= settings.MIN_CONFIDENCE:
            signal_type = SignalType.SELL
            confidence = min(bearish_score, 100.0)
        else:
            # Not enough confidence for a signal
            return None

        # Calculate stop loss and target using ATR
        atr = indicators.get('atr', current_price * 0.02)  # Default 2% if no ATR

        if signal_type == SignalType.BUY:
            stop_loss = current_price - (2 * atr)
            target_price = current_price + (3 * atr)  # 1.5:1 reward/risk
        else:  # SELL
            stop_loss = current_price + (2 * atr)
            target_price = current_price - (3 * atr)

        # Create signal
        signal = Signal(
            symbol=symbol,
            timeframe=timeframe,
            signal_type=signal_type,
            status=SignalStatus.ACTIVE,
            entry_price=current_price,
            current_price=current_price,
            target_price=target_price,
            stop_loss=stop_loss,
            confidence=confidence,
            strategy="multi_indicator_pattern",
            description="; ".join(reasons),
            generated_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=settings.SIGNAL_COOLDOWN_MINUTES),
        )

        logger.info(
            f"Generated {signal_type.value} signal for {symbol} "
            f"with {confidence:.1f}% confidence"
        )

        return signal

    def calculate_risk_reward(self, signal: Signal) -> float:
        """
        Calculate risk/reward ratio for signal.

        Args:
            signal: Trading signal.

        Returns:
            Risk/reward ratio.
        """
        if signal.signal_type == SignalType.BUY:
            risk = signal.entry_price - signal.stop_loss
            reward = signal.target_price - signal.entry_price
        else:  # SELL
            risk = signal.stop_loss - signal.entry_price
            reward = signal.entry_price - signal.target_price

        if risk == 0:
            return 0.0

        return reward / risk
