"""Pattern detection engine."""

import logging
from typing import List, Optional
import pandas as pd
import numpy as np

from .models import PatternType, PatternSignal, PatternResult


logger = logging.getLogger(__name__)


class PatternDetector:
    """
    Chart and candlestick pattern detector.

    Detects common technical analysis patterns in price data.
    """

    @staticmethod
    def detect_doji(
        open_price: float,
        high: float,
        low: float,
        close: float,
        threshold: float = 0.001,
    ) -> bool:
        """
        Detect Doji candlestick pattern.

        Args:
            open_price: Open price.
            high: High price.
            low: Low price.
            close: Close price.
            threshold: Body size threshold (% of range).

        Returns:
            True if Doji detected.
        """
        body = abs(close - open_price)
        range_val = high - low

        if range_val == 0:
            return False

        body_ratio = body / range_val
        return body_ratio <= threshold

    @staticmethod
    def detect_hammer(
        open_price: float,
        high: float,
        low: float,
        close: float,
    ) -> bool:
        """
        Detect Hammer candlestick pattern (bullish).

        Args:
            open_price: Open price.
            high: High price.
            low: Low price.
            close: Close price.

        Returns:
            True if Hammer detected.
        """
        body = abs(close - open_price)
        upper_shadow = high - max(open_price, close)
        lower_shadow = min(open_price, close) - low
        range_val = high - low

        if range_val == 0:
            return False

        # Hammer characteristics:
        # - Small body (< 30% of range)
        # - Long lower shadow (> 2x body)
        # - Little to no upper shadow
        body_ratio = body / range_val
        return (
            body_ratio < 0.3
            and lower_shadow > 2 * body
            and upper_shadow < body * 0.5
        )

    @staticmethod
    def detect_shooting_star(
        open_price: float,
        high: float,
        low: float,
        close: float,
    ) -> bool:
        """
        Detect Shooting Star candlestick pattern (bearish).

        Args:
            open_price: Open price.
            high: High price.
            low: Low price.
            close: Close price.

        Returns:
            True if Shooting Star detected.
        """
        body = abs(close - open_price)
        upper_shadow = high - max(open_price, close)
        lower_shadow = min(open_price, close) - low
        range_val = high - low

        if range_val == 0:
            return False

        # Shooting Star characteristics:
        # - Small body (< 30% of range)
        # - Long upper shadow (> 2x body)
        # - Little to no lower shadow
        body_ratio = body / range_val
        return (
            body_ratio < 0.3
            and upper_shadow > 2 * body
            and lower_shadow < body * 0.5
        )

    @staticmethod
    def detect_engulfing(
        prev_open: float,
        prev_close: float,
        curr_open: float,
        curr_close: float,
    ) -> Optional[str]:
        """
        Detect Engulfing pattern.

        Args:
            prev_open: Previous candle open.
            prev_close: Previous candle close.
            curr_open: Current candle open.
            curr_close: Current candle close.

        Returns:
            'bullish' for bullish engulfing, 'bearish' for bearish, None otherwise.
        """
        prev_bullish = prev_close > prev_open
        curr_bullish = curr_close > curr_open

        # Bullish Engulfing
        if not prev_bullish and curr_bullish:
            if curr_open <= prev_close and curr_close >= prev_open:
                return "bullish"

        # Bearish Engulfing
        if prev_bullish and not curr_bullish:
            if curr_open >= prev_close and curr_close <= prev_open:
                return "bearish"

        return None

    @staticmethod
    def detect_morning_star(
        df: pd.DataFrame,
        index: int,
    ) -> bool:
        """
        Detect Morning Star pattern (bullish reversal).

        Args:
            df: DataFrame with OHLC data.
            index: Current candle index.

        Returns:
            True if Morning Star detected.
        """
        if index < 2:
            return False

        # Get three candles
        candle1 = df.iloc[index - 2]
        candle2 = df.iloc[index - 1]
        candle3 = df.iloc[index]

        # Candle 1: Long bearish
        bearish1 = candle1['close'] < candle1['open']
        long1 = abs(candle1['close'] - candle1['open']) > (candle1['high'] - candle1['low']) * 0.6

        # Candle 2: Small body (star)
        small_body = abs(candle2['close'] - candle2['open']) < (candle2['high'] - candle2['low']) * 0.3

        # Candle 3: Long bullish
        bullish3 = candle3['close'] > candle3['open']
        long3 = abs(candle3['close'] - candle3['open']) > (candle3['high'] - candle3['low']) * 0.6

        # Candle 3 closes above midpoint of Candle 1
        closes_above = candle3['close'] > (candle1['open'] + candle1['close']) / 2

        return bearish1 and long1 and small_body and bullish3 and long3 and closes_above

    @staticmethod
    def detect_evening_star(
        df: pd.DataFrame,
        index: int,
    ) -> bool:
        """
        Detect Evening Star pattern (bearish reversal).

        Args:
            df: DataFrame with OHLC data.
            index: Current candle index.

        Returns:
            True if Evening Star detected.
        """
        if index < 2:
            return False

        # Get three candles
        candle1 = df.iloc[index - 2]
        candle2 = df.iloc[index - 1]
        candle3 = df.iloc[index]

        # Candle 1: Long bullish
        bullish1 = candle1['close'] > candle1['open']
        long1 = abs(candle1['close'] - candle1['open']) > (candle1['high'] - candle1['low']) * 0.6

        # Candle 2: Small body (star)
        small_body = abs(candle2['close'] - candle2['open']) < (candle2['high'] - candle2['low']) * 0.3

        # Candle 3: Long bearish
        bearish3 = candle3['close'] < candle3['open']
        long3 = abs(candle3['close'] - candle3['open']) > (candle3['high'] - candle3['low']) * 0.6

        # Candle 3 closes below midpoint of Candle 1
        closes_below = candle3['close'] < (candle1['open'] + candle1['close']) / 2

        return bullish1 and long1 and small_body and bearish3 and long3 and closes_below

    @staticmethod
    def detect_double_top(
        df: pd.DataFrame,
        lookback: int = 20,
        tolerance: float = 0.02,
    ) -> Optional[int]:
        """
        Detect Double Top pattern (bearish).

        Args:
            df: DataFrame with OHLC data.
            lookback: Lookback period for peak detection.
            tolerance: Price tolerance for peak matching (%).

        Returns:
            Index of second peak if detected, None otherwise.
        """
        if len(df) < lookback:
            return None

        # Find peaks in the lookback period
        highs = df['high'].values[-lookback:]
        peaks = []

        for i in range(1, len(highs) - 1):
            if highs[i] > highs[i - 1] and highs[i] > highs[i + 1]:
                peaks.append((i, highs[i]))

        # Need at least 2 peaks
        if len(peaks) < 2:
            return None

        # Check if last two peaks are similar (double top)
        peak1_idx, peak1_price = peaks[-2]
        peak2_idx, peak2_price = peaks[-1]

        price_diff = abs(peak1_price - peak2_price) / peak1_price
        if price_diff <= tolerance:
            return len(df) - lookback + peak2_idx

        return None

    @staticmethod
    def detect_double_bottom(
        df: pd.DataFrame,
        lookback: int = 20,
        tolerance: float = 0.02,
    ) -> Optional[int]:
        """
        Detect Double Bottom pattern (bullish).

        Args:
            df: DataFrame with OHLC data.
            lookback: Lookback period for trough detection.
            tolerance: Price tolerance for trough matching (%).

        Returns:
            Index of second trough if detected, None otherwise.
        """
        if len(df) < lookback:
            return None

        # Find troughs in the lookback period
        lows = df['low'].values[-lookback:]
        troughs = []

        for i in range(1, len(lows) - 1):
            if lows[i] < lows[i - 1] and lows[i] < lows[i + 1]:
                troughs.append((i, lows[i]))

        # Need at least 2 troughs
        if len(troughs) < 2:
            return None

        # Check if last two troughs are similar (double bottom)
        trough1_idx, trough1_price = troughs[-2]
        trough2_idx, trough2_price = troughs[-1]

        price_diff = abs(trough1_price - trough2_price) / trough1_price
        if price_diff <= tolerance:
            return len(df) - lookback + trough2_idx

        return None

    @classmethod
    def scan_patterns(
        cls,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str,
    ) -> List[PatternResult]:
        """
        Scan for all patterns in price data.

        Args:
            df: DataFrame with OHLC data (columns: open, high, low, close, timestamp).
            symbol: Trading symbol.
            timeframe: Timeframe.

        Returns:
            List of detected patterns.
        """
        patterns = []

        if len(df) < 3:
            return patterns

        latest_idx = len(df) - 1
        latest = df.iloc[latest_idx]

        # Check single candle patterns
        if cls.detect_doji(latest['open'], latest['high'], latest['low'], latest['close']):
            patterns.append(
                PatternResult(
                    pattern_type=PatternType.DOJI,
                    signal=PatternSignal.NEUTRAL,
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=latest['timestamp'],
                    confidence=70.0,
                    description="Doji candlestick indicates indecision",
                )
            )

        if cls.detect_hammer(latest['open'], latest['high'], latest['low'], latest['close']):
            patterns.append(
                PatternResult(
                    pattern_type=PatternType.HAMMER,
                    signal=PatternSignal.BULLISH,
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=latest['timestamp'],
                    confidence=75.0,
                    description="Hammer pattern suggests bullish reversal",
                )
            )

        if cls.detect_shooting_star(latest['open'], latest['high'], latest['low'], latest['close']):
            patterns.append(
                PatternResult(
                    pattern_type=PatternType.SHOOTING_STAR,
                    signal=PatternSignal.BEARISH,
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=latest['timestamp'],
                    confidence=75.0,
                    description="Shooting Star pattern suggests bearish reversal",
                )
            )

        # Check multi-candle patterns
        if latest_idx >= 1:
            prev = df.iloc[latest_idx - 1]
            engulfing = cls.detect_engulfing(
                prev['open'], prev['close'],
                latest['open'], latest['close'],
            )

            if engulfing == "bullish":
                patterns.append(
                    PatternResult(
                        pattern_type=PatternType.BULLISH_ENGULFING,
                        signal=PatternSignal.BULLISH,
                        symbol=symbol,
                        timeframe=timeframe,
                        timestamp=latest['timestamp'],
                        confidence=80.0,
                        description="Bullish Engulfing pattern indicates strong buying pressure",
                    )
                )
            elif engulfing == "bearish":
                patterns.append(
                    PatternResult(
                        pattern_type=PatternType.BEARISH_ENGULFING,
                        signal=PatternSignal.BEARISH,
                        symbol=symbol,
                        timeframe=timeframe,
                        timestamp=latest['timestamp'],
                        confidence=80.0,
                        description="Bearish Engulfing pattern indicates strong selling pressure",
                    )
                )

        # Check complex patterns
        if cls.detect_morning_star(df, latest_idx):
            patterns.append(
                PatternResult(
                    pattern_type=PatternType.MORNING_STAR,
                    signal=PatternSignal.BULLISH,
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=latest['timestamp'],
                    confidence=85.0,
                    description="Morning Star pattern is a strong bullish reversal signal",
                )
            )

        if cls.detect_evening_star(df, latest_idx):
            patterns.append(
                PatternResult(
                    pattern_type=PatternType.EVENING_STAR,
                    signal=PatternSignal.BEARISH,
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=latest['timestamp'],
                    confidence=85.0,
                    description="Evening Star pattern is a strong bearish reversal signal",
                )
            )

        # Chart patterns
        double_top_idx = cls.detect_double_top(df)
        if double_top_idx is not None:
            patterns.append(
                PatternResult(
                    pattern_type=PatternType.DOUBLE_TOP,
                    signal=PatternSignal.BEARISH,
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=df.iloc[double_top_idx]['timestamp'],
                    confidence=75.0,
                    description="Double Top pattern suggests bearish reversal",
                )
            )

        double_bottom_idx = cls.detect_double_bottom(df)
        if double_bottom_idx is not None:
            patterns.append(
                PatternResult(
                    pattern_type=PatternType.DOUBLE_BOTTOM,
                    signal=PatternSignal.BULLISH,
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=df.iloc[double_bottom_idx]['timestamp'],
                    confidence=75.0,
                    description="Double Bottom pattern suggests bullish reversal",
                )
            )

        return patterns
