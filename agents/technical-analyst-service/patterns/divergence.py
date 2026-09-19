"""RSI Divergence detection - Supply/Demand and Break of Structure strategy."""

import logging
from typing import List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np


logger = logging.getLogger(__name__)


class DivergenceType(str, Enum):
    """Types of RSI divergence."""

    REGULAR_BULLISH = "regular_bullish"  # Price LL, RSI HL → Reversal UP
    REGULAR_BEARISH = "regular_bearish"  # Price HH, RSI LH → Reversal DOWN
    HIDDEN_BULLISH = "hidden_bullish"    # Price HL, RSI LL → Continuation UP
    HIDDEN_BEARISH = "hidden_bearish"    # Price LH, RSI HL → Continuation DOWN


@dataclass
class Divergence:
    """RSI Divergence pattern."""

    divergence_type: DivergenceType
    start_idx: int
    end_idx: int
    price_start: float
    price_end: float
    rsi_start: float
    rsi_end: float
    confirmed: bool  # True if structure broken
    confidence: float
    description: str

    @property
    def is_bullish(self) -> bool:
        """Check if divergence is bullish."""
        return self.divergence_type in [
            DivergenceType.REGULAR_BULLISH,
            DivergenceType.HIDDEN_BULLISH,
        ]

    @property
    def is_reversal(self) -> bool:
        """Check if divergence signals reversal."""
        return self.divergence_type in [
            DivergenceType.REGULAR_BULLISH,
            DivergenceType.REGULAR_BEARISH,
        ]


@dataclass
class StructureBreak:
    """Break of Structure (BOS) or Change of Character (CHoCH)."""

    break_type: str  # 'BOS' or 'CHoCH'
    direction: str  # 'bullish' or 'bearish'
    break_idx: int
    break_price: float
    previous_level: float
    strength: float  # How strongly it broke (%)


class RSIDivergenceDetector:
    """
    RSI Divergence detector - Supply/Demand strategy.

    Detects regular and hidden divergences between price and RSI,
    confirms with Break of Structure (BOS).
    """

    def __init__(
        self,
        min_pivot_distance: int = 5,
        rsi_threshold: float = 5.0,  # Minimum RSI difference
    ):
        """
        Initialize divergence detector.

        Args:
            min_pivot_distance: Minimum bars between pivots.
            rsi_threshold: Minimum RSI difference for divergence.
        """
        self.min_pivot_distance = min_pivot_distance
        self.rsi_threshold = rsi_threshold

    def find_pivots(
        self,
        prices: pd.Series,
        order: int = 5,
    ) -> Tuple[List[int], List[int]]:
        """
        Find pivot highs and lows in price series.

        Args:
            prices: Price series.
            order: Number of bars to left/right for pivot.

        Returns:
            Tuple of (pivot_high_indices, pivot_low_indices).
        """
        pivot_highs = []
        pivot_lows = []

        for i in range(order, len(prices) - order):
            # Pivot high
            is_high = True
            for j in range(1, order + 1):
                if prices.iloc[i] <= prices.iloc[i - j] or prices.iloc[i] <= prices.iloc[i + j]:
                    is_high = False
                    break
            if is_high:
                pivot_highs.append(i)

            # Pivot low
            is_low = True
            for j in range(1, order + 1):
                if prices.iloc[i] >= prices.iloc[i - j] or prices.iloc[i] >= prices.iloc[i + j]:
                    is_low = False
                    break
            if is_low:
                pivot_lows.append(i)

        return pivot_highs, pivot_lows

    def detect_regular_bullish_divergence(
        self,
        df: pd.DataFrame,
        rsi: pd.Series,
    ) -> List[Divergence]:
        """
        Detect Regular Bullish Divergence.

        Price makes lower low (LL), RSI makes higher low (HL).
        Signals potential reversal to the upside.

        Args:
            df: DataFrame with price data.
            rsi: RSI series.

        Returns:
            List of detected divergences.
        """
        divergences = []

        # Find price lows
        _, price_lows = self.find_pivots(df['low'])

        if len(price_lows) < 2:
            return divergences

        # Check consecutive lows
        for i in range(len(price_lows) - 1):
            idx1 = price_lows[i]
            idx2 = price_lows[i + 1]

            # Must be far enough apart
            if idx2 - idx1 < self.min_pivot_distance:
                continue

            price1 = df['low'].iloc[idx1]
            price2 = df['low'].iloc[idx2]
            rsi1 = rsi.iloc[idx1]
            rsi2 = rsi.iloc[idx2]

            # Check for divergence: Price LL, RSI HL
            if price2 < price1 and rsi2 > rsi1 + self.rsi_threshold:
                # Check if structure broken (price broke above previous high)
                confirmed = self._check_structure_break_bullish(df, idx2)

                confidence = self._calculate_divergence_confidence(
                    price1, price2, rsi1, rsi2, confirmed
                )

                divergences.append(Divergence(
                    divergence_type=DivergenceType.REGULAR_BULLISH,
                    start_idx=idx1,
                    end_idx=idx2,
                    price_start=price1,
                    price_end=price2,
                    rsi_start=rsi1,
                    rsi_end=rsi2,
                    confirmed=confirmed,
                    confidence=confidence,
                    description=f"Regular Bullish Divergence: Price LL ({price1:.2f}→{price2:.2f}), RSI HL ({rsi1:.1f}→{rsi2:.1f})",
                ))

        return divergences

    def detect_regular_bearish_divergence(
        self,
        df: pd.DataFrame,
        rsi: pd.Series,
    ) -> List[Divergence]:
        """
        Detect Regular Bearish Divergence.

        Price makes higher high (HH), RSI makes lower high (LH).
        Signals potential reversal to the downside.

        Args:
            df: DataFrame with price data.
            rsi: RSI series.

        Returns:
            List of detected divergences.
        """
        divergences = []

        # Find price highs
        price_highs, _ = self.find_pivots(df['high'])

        if len(price_highs) < 2:
            return divergences

        # Check consecutive highs
        for i in range(len(price_highs) - 1):
            idx1 = price_highs[i]
            idx2 = price_highs[i + 1]

            # Must be far enough apart
            if idx2 - idx1 < self.min_pivot_distance:
                continue

            price1 = df['high'].iloc[idx1]
            price2 = df['high'].iloc[idx2]
            rsi1 = rsi.iloc[idx1]
            rsi2 = rsi.iloc[idx2]

            # Check for divergence: Price HH, RSI LH
            if price2 > price1 and rsi2 < rsi1 - self.rsi_threshold:
                # Check if structure broken (price broke below previous low)
                confirmed = self._check_structure_break_bearish(df, idx2)

                confidence = self._calculate_divergence_confidence(
                    price1, price2, rsi1, rsi2, confirmed
                )

                divergences.append(Divergence(
                    divergence_type=DivergenceType.REGULAR_BEARISH,
                    start_idx=idx1,
                    end_idx=idx2,
                    price_start=price1,
                    price_end=price2,
                    rsi_start=rsi1,
                    rsi_end=rsi2,
                    confirmed=confirmed,
                    confidence=confidence,
                    description=f"Regular Bearish Divergence: Price HH ({price1:.2f}→{price2:.2f}), RSI LH ({rsi1:.1f}→{rsi2:.1f})",
                ))

        return divergences

    def detect_hidden_bullish_divergence(
        self,
        df: pd.DataFrame,
        rsi: pd.Series,
    ) -> List[Divergence]:
        """
        Detect Hidden Bullish Divergence.

        Price makes higher low (HL), RSI makes lower low (LL).
        Signals trend continuation to the upside.

        Args:
            df: DataFrame with price data.
            rsi: RSI series.

        Returns:
            List of detected divergences.
        """
        divergences = []

        _, price_lows = self.find_pivots(df['low'])

        if len(price_lows) < 2:
            return divergences

        for i in range(len(price_lows) - 1):
            idx1 = price_lows[i]
            idx2 = price_lows[i + 1]

            if idx2 - idx1 < self.min_pivot_distance:
                continue

            price1 = df['low'].iloc[idx1]
            price2 = df['low'].iloc[idx2]
            rsi1 = rsi.iloc[idx1]
            rsi2 = rsi.iloc[idx2]

            # Check for divergence: Price HL, RSI LL
            if price2 > price1 and rsi2 < rsi1 - self.rsi_threshold:
                confirmed = self._check_structure_break_bullish(df, idx2)

                confidence = self._calculate_divergence_confidence(
                    price1, price2, rsi1, rsi2, confirmed
                )

                divergences.append(Divergence(
                    divergence_type=DivergenceType.HIDDEN_BULLISH,
                    start_idx=idx1,
                    end_idx=idx2,
                    price_start=price1,
                    price_end=price2,
                    rsi_start=rsi1,
                    rsi_end=rsi2,
                    confirmed=confirmed,
                    confidence=confidence,
                    description=f"Hidden Bullish Divergence: Price HL ({price1:.2f}→{price2:.2f}), RSI LL ({rsi1:.1f}→{rsi2:.1f})",
                ))

        return divergences

    def detect_hidden_bearish_divergence(
        self,
        df: pd.DataFrame,
        rsi: pd.Series,
    ) -> List[Divergence]:
        """
        Detect Hidden Bearish Divergence.

        Price makes lower high (LH), RSI makes higher high (HH).
        Signals trend continuation to the downside.

        Args:
            df: DataFrame with price data.
            rsi: RSI series.

        Returns:
            List of detected divergences.
        """
        divergences = []

        price_highs, _ = self.find_pivots(df['high'])

        if len(price_highs) < 2:
            return divergences

        for i in range(len(price_highs) - 1):
            idx1 = price_highs[i]
            idx2 = price_highs[i + 1]

            if idx2 - idx1 < self.min_pivot_distance:
                continue

            price1 = df['high'].iloc[idx1]
            price2 = df['high'].iloc[idx2]
            rsi1 = rsi.iloc[idx1]
            rsi2 = rsi.iloc[idx2]

            # Check for divergence: Price LH, RSI HH
            if price2 < price1 and rsi2 > rsi1 + self.rsi_threshold:
                confirmed = self._check_structure_break_bearish(df, idx2)

                confidence = self._calculate_divergence_confidence(
                    price1, price2, rsi1, rsi2, confirmed
                )

                divergences.append(Divergence(
                    divergence_type=DivergenceType.HIDDEN_BEARISH,
                    start_idx=idx1,
                    end_idx=idx2,
                    price_start=price1,
                    price_end=price2,
                    rsi_start=rsi1,
                    rsi_end=rsi2,
                    confirmed=confirmed,
                    confidence=confidence,
                    description=f"Hidden Bearish Divergence: Price LH ({price1:.2f}→{price2:.2f}), RSI HH ({rsi1:.1f}→{rsi2:.1f})",
                ))

        return divergences

    def detect_all_divergences(
        self,
        df: pd.DataFrame,
        rsi: pd.Series,
    ) -> List[Divergence]:
        """
        Detect all types of RSI divergences.

        Args:
            df: DataFrame with OHLC data.
            rsi: RSI indicator series.

        Returns:
            List of all detected divergences.
        """
        all_divergences = []

        # Regular divergences (reversals)
        all_divergences.extend(self.detect_regular_bullish_divergence(df, rsi))
        all_divergences.extend(self.detect_regular_bearish_divergence(df, rsi))

        # Hidden divergences (continuations)
        all_divergences.extend(self.detect_hidden_bullish_divergence(df, rsi))
        all_divergences.extend(self.detect_hidden_bearish_divergence(df, rsi))

        # Sort by index
        all_divergences.sort(key=lambda d: d.end_idx, reverse=True)

        return all_divergences

    def _check_structure_break_bullish(self, df: pd.DataFrame, pivot_idx: int) -> bool:
        """
        Check if bullish structure was broken (BOS).

        Price should break above the previous high after divergence.

        Args:
            df: DataFrame with price data.
            pivot_idx: Index of the divergence pivot.

        Returns:
            True if structure broken.
        """
        if pivot_idx >= len(df) - 5:
            return False

        # Find previous high before pivot
        lookback_start = max(0, pivot_idx - 20)
        previous_high = df['high'].iloc[lookback_start:pivot_idx].max()

        # Check if price broke above after pivot
        future_prices = df['high'].iloc[pivot_idx:pivot_idx + 10]
        broke_above = (future_prices > previous_high).any()

        return broke_above

    def _check_structure_break_bearish(self, df: pd.DataFrame, pivot_idx: int) -> bool:
        """
        Check if bearish structure was broken (BOS).

        Price should break below the previous low after divergence.

        Args:
            df: DataFrame with price data.
            pivot_idx: Index of the divergence pivot.

        Returns:
            True if structure broken.
        """
        if pivot_idx >= len(df) - 5:
            return False

        # Find previous low before pivot
        lookback_start = max(0, pivot_idx - 20)
        previous_low = df['low'].iloc[lookback_start:pivot_idx].min()

        # Check if price broke below after pivot
        future_prices = df['low'].iloc[pivot_idx:pivot_idx + 10]
        broke_below = (future_prices < previous_low).any()

        return broke_below

    def _calculate_divergence_confidence(
        self,
        price1: float,
        price2: float,
        rsi1: float,
        rsi2: float,
        confirmed: bool,
    ) -> float:
        """
        Calculate confidence score for divergence.

        Args:
            price1: First price point.
            price2: Second price point.
            rsi1: First RSI value.
            rsi2: Second RSI value.
            confirmed: True if structure broken.

        Returns:
            Confidence score (0-100).
        """
        confidence = 50.0

        # RSI divergence strength
        rsi_diff = abs(rsi2 - rsi1)
        if rsi_diff > 10:
            confidence += 15
        elif rsi_diff > 20:
            confidence += 25

        # Price divergence strength
        price_diff_pct = abs(price2 - price1) / price1 * 100
        if price_diff_pct > 2:
            confidence += 10

        # Structure break confirmation
        if confirmed:
            confidence += 25

        return min(confidence, 100.0)
