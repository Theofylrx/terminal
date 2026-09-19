"""Elliott Wave pattern detection with Fibonacci levels."""

import logging
from typing import List, Optional, Tuple
import pandas as pd
import numpy as np
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class Wave:
    """Represents a single Elliott Wave."""

    wave_number: int  # 1, 2, 3, 4, 5 or A, B, C
    start_idx: int
    end_idx: int
    start_price: float
    end_price: float
    move_type: str  # 'impulse' or 'correction'

    @property
    def magnitude(self) -> float:
        """Calculate wave magnitude."""
        return abs(self.end_price - self.start_price)

    @property
    def is_up(self) -> bool:
        """Check if wave is upward."""
        return self.end_price > self.start_price


@dataclass
class FibonacciLevel:
    """Fibonacci retracement or extension level."""

    level: float  # 0.382, 0.5, 0.618, 1.618, etc.
    price: float
    level_type: str  # 'retracement' or 'extension'


@dataclass
class ElliottWavePattern:
    """Complete Elliott Wave pattern (5 waves or 3 waves)."""

    waves: List[Wave]
    pattern_type: str  # 'impulse', 'leading_diagonal', 'ending_diagonal', 'zigzag', 'flat', 'triangle'
    direction: str  # 'bullish' or 'bearish'
    current_wave: int
    fib_levels: List[FibonacciLevel]
    confidence: float
    subtype: Optional[str] = None  # For variants like 'expanded_flat', 'running_flat', 'contracting_triangle'
    is_truncated: bool = False  # True if Wave 5 is truncated
    extended_wave: Optional[int] = None  # Which wave is extended (1, 3, or 5)

    @property
    def is_complete(self) -> bool:
        """Check if pattern is complete."""
        if self.pattern_type in ['impulse', 'leading_diagonal', 'ending_diagonal']:
            return len(self.waves) == 5
        elif self.pattern_type in ['zigzag', 'flat']:
            return len(self.waves) == 3
        elif self.pattern_type == 'triangle':
            return len(self.waves) == 5  # A-B-C-D-E
        else:
            return False


class FibonacciCalculator:
    """
    Fibonacci retracement and extension calculator.
    """

    # Common Fibonacci ratios
    RETRACEMENT_LEVELS = [0.236, 0.382, 0.5, 0.618, 0.786]
    EXTENSION_LEVELS = [1.0, 1.272, 1.618, 2.0, 2.618]

    @staticmethod
    def calculate_retracements(
        start_price: float,
        end_price: float,
        is_uptrend: bool = True,
    ) -> List[FibonacciLevel]:
        """
        Calculate Fibonacci retracement levels.

        Args:
            start_price: Starting price of the move.
            end_price: Ending price of the move.
            is_uptrend: True for uptrend, False for downtrend.

        Returns:
            List of Fibonacci retracement levels.
        """
        diff = end_price - start_price

        levels = []
        for ratio in FibonacciCalculator.RETRACEMENT_LEVELS:
            if is_uptrend:
                price = end_price - (diff * ratio)
            else:
                price = end_price + (diff * ratio)

            levels.append(FibonacciLevel(
                level=ratio,
                price=price,
                level_type='retracement'
            ))

        return levels

    @staticmethod
    def calculate_extensions(
        wave1_start: float,
        wave1_end: float,
        wave2_end: float,
        is_uptrend: bool = True,
    ) -> List[FibonacciLevel]:
        """
        Calculate Fibonacci extension levels for Wave 3 or Wave 5.

        Args:
            wave1_start: Start of Wave 1.
            wave1_end: End of Wave 1 (also start of Wave 2).
            wave2_end: End of Wave 2 (start of Wave 3).
            is_uptrend: True for bullish pattern.

        Returns:
            List of Fibonacci extension levels.
        """
        wave1_magnitude = abs(wave1_end - wave1_start)

        levels = []
        for ratio in FibonacciCalculator.EXTENSION_LEVELS:
            if is_uptrend:
                price = wave2_end + (wave1_magnitude * ratio)
            else:
                price = wave2_end - (wave1_magnitude * ratio)

            levels.append(FibonacciLevel(
                level=ratio,
                price=price,
                level_type='extension'
            ))

        return levels

    @staticmethod
    def check_fib_level_hit(
        current_price: float,
        fib_level: FibonacciLevel,
        tolerance: float = 0.005,  # 0.5% tolerance
    ) -> bool:
        """
        Check if current price is near a Fibonacci level.

        Args:
            current_price: Current price to check.
            fib_level: Fibonacci level to check against.
            tolerance: Price tolerance (default 0.5%).

        Returns:
            True if price is near the level.
        """
        price_diff = abs(current_price - fib_level.price) / fib_level.price
        return price_diff <= tolerance


class ElliottWaveDetector:
    """
    Elliott Wave pattern detector.

    Identifies 5-wave impulse patterns and 3-wave corrective patterns
    using pivot points and Fibonacci relationships.
    """

    def __init__(self, min_wave_size: int = 5):
        """
        Initialize Elliott Wave detector.

        Args:
            min_wave_size: Minimum number of bars for a wave.
        """
        self.min_wave_size = min_wave_size
        self.fib_calc = FibonacciCalculator()

    def find_pivots(self, df: pd.DataFrame, order: int = 5) -> Tuple[List[int], List[int]]:
        """
        Find pivot highs and lows in price data.

        Args:
            df: DataFrame with OHLC data.
            order: Number of bars to left and right for pivot.

        Returns:
            Tuple of (pivot_high_indices, pivot_low_indices).
        """
        highs = df['high'].values
        lows = df['low'].values

        pivot_highs = []
        pivot_lows = []

        for i in range(order, len(df) - order):
            # Check for pivot high
            is_pivot_high = True
            for j in range(1, order + 1):
                if highs[i] <= highs[i - j] or highs[i] <= highs[i + j]:
                    is_pivot_high = False
                    break

            if is_pivot_high:
                pivot_highs.append(i)

            # Check for pivot low
            is_pivot_low = True
            for j in range(1, order + 1):
                if lows[i] >= lows[i - j] or lows[i] >= lows[i + j]:
                    is_pivot_low = False
                    break

            if is_pivot_low:
                pivot_lows.append(i)

        return pivot_highs, pivot_lows

    def detect_impulse_wave(
        self,
        df: pd.DataFrame,
        is_bullish: bool = True,
    ) -> Optional[ElliottWavePattern]:
        """
        Detect 5-wave impulse Elliott Wave pattern.

        Args:
            df: DataFrame with OHLC data.
            is_bullish: True for bullish impulse, False for bearish.

        Returns:
            ElliottWavePattern if detected, None otherwise.
        """
        pivot_highs, pivot_lows = self.find_pivots(df)

        if is_bullish:
            # Look for pattern: low, high, low, high, low, high
            pivots = self._alternate_pivots(pivot_lows, pivot_highs, start_with_low=True)
        else:
            # Look for pattern: high, low, high, low, high, low
            pivots = self._alternate_pivots(pivot_highs, pivot_lows, start_with_low=False)

        if len(pivots) < 6:
            return None

        # Try to identify 5 waves
        waves = []
        for i in range(5):
            start_idx = pivots[i]
            end_idx = pivots[i + 1]

            wave = Wave(
                wave_number=i + 1,
                start_idx=start_idx,
                end_idx=end_idx,
                start_price=df.iloc[start_idx]['close'],
                end_price=df.iloc[end_idx]['close'],
                move_type='impulse',
            )
            waves.append(wave)

        # Validate Elliott Wave rules
        if not self._validate_impulse_waves(waves, is_bullish):
            return None

        # Calculate Fibonacci levels
        fib_levels = self._calculate_wave_fibs(waves, is_bullish)

        # Determine current wave
        current_wave = self._determine_current_wave(waves, df)

        # Calculate confidence
        confidence = self._calculate_wave_confidence(waves, fib_levels, df)

        return ElliottWavePattern(
            waves=waves,
            pattern_type='impulse',
            direction='bullish' if is_bullish else 'bearish',
            current_wave=current_wave,
            fib_levels=fib_levels,
            confidence=confidence,
        )

    def _alternate_pivots(
        self,
        pivots1: List[int],
        pivots2: List[int],
        start_with_low: bool,
    ) -> List[int]:
        """Alternate between two pivot lists."""
        result = []
        i1, i2 = 0, 0

        use_first = start_with_low

        while i1 < len(pivots1) and i2 < len(pivots2):
            if use_first:
                result.append(pivots1[i1])
                i1 += 1
            else:
                result.append(pivots2[i2])
                i2 += 1
            use_first = not use_first

        return result

    def _validate_impulse_waves(self, waves: List[Wave], is_bullish: bool) -> bool:
        """
        Validate Elliott Wave rules for impulse pattern.

        Rules:
        1. Wave 2 cannot retrace more than 100% of Wave 1
        2. Wave 3 cannot be the shortest among waves 1, 3, and 5
        3. Wave 4 cannot overlap Wave 1's price territory
        """
        if len(waves) < 5:
            return False

        wave1, wave2, wave3, wave4, wave5 = waves[:5]

        # Rule 1: Wave 2 retracement
        wave1_mag = wave1.magnitude
        wave2_mag = wave2.magnitude

        if wave2_mag >= wave1_mag:
            return False

        # Rule 2: Wave 3 is not the shortest
        wave3_mag = wave3.magnitude
        wave5_mag = wave5.magnitude

        if wave3_mag < wave1_mag or wave3_mag < wave5_mag:
            return False

        # Rule 3: Wave 4 doesn't overlap Wave 1
        if is_bullish:
            if wave4.end_price < wave1.end_price:
                return False
        else:
            if wave4.end_price > wave1.end_price:
                return False

        return True

    def _calculate_wave_fibs(
        self,
        waves: List[Wave],
        is_bullish: bool,
    ) -> List[FibonacciLevel]:
        """Calculate Fibonacci levels for waves."""
        fib_levels = []

        if len(waves) >= 2:
            # Wave 2 retracements
            wave2_fibs = self.fib_calc.calculate_retracements(
                waves[0].start_price,
                waves[0].end_price,
                is_uptrend=is_bullish,
            )
            fib_levels.extend(wave2_fibs)

        if len(waves) >= 4:
            # Wave 4 retracements
            wave4_fibs = self.fib_calc.calculate_retracements(
                waves[2].start_price,
                waves[2].end_price,
                is_uptrend=is_bullish,
            )
            fib_levels.extend(wave4_fibs)

        if len(waves) >= 3:
            # Wave 3 extensions
            wave3_fibs = self.fib_calc.calculate_extensions(
                waves[0].start_price,
                waves[0].end_price,
                waves[1].end_price,
                is_uptrend=is_bullish,
            )
            fib_levels.extend(wave3_fibs)

        if len(waves) >= 5:
            # Wave 5 extensions
            wave5_fibs = self.fib_calc.calculate_extensions(
                waves[0].start_price,
                waves[0].end_price,
                waves[3].end_price,
                is_uptrend=is_bullish,
            )
            fib_levels.extend(wave5_fibs)

        return fib_levels

    def _determine_current_wave(self, waves: List[Wave], df: pd.DataFrame) -> int:
        """Determine which wave is currently active."""
        latest_idx = len(df) - 1

        for i, wave in enumerate(waves):
            if wave.start_idx <= latest_idx <= wave.end_idx:
                return i + 1

        # If past all waves, pattern is complete
        return len(waves)

    def _calculate_wave_confidence(
        self,
        waves: List[Wave],
        fib_levels: List[FibonacciLevel],
        df: pd.DataFrame,
    ) -> float:
        """Calculate confidence score for Elliott Wave pattern."""
        confidence = 50.0  # Base confidence

        # Check Wave 2 Fibonacci retracement
        if len(waves) >= 2:
            wave2 = waves[1]
            retracement_ratio = wave2.magnitude / waves[0].magnitude

            # Check if Wave 2 is near common Fibonacci levels
            if 0.35 <= retracement_ratio <= 0.42:  # Near 38.2%
                confidence += 10
            elif 0.48 <= retracement_ratio <= 0.52:  # Near 50%
                confidence += 10
            elif 0.60 <= retracement_ratio <= 0.65:  # Near 61.8%
                confidence += 15

        # Check Wave 3 extension
        if len(waves) >= 3:
            wave3 = waves[2]
            extension_ratio = wave3.magnitude / waves[0].magnitude

            # Wave 3 is often 1.618x Wave 1
            if 1.5 <= extension_ratio <= 1.7:
                confidence += 15

        # Check Wave 4 Fibonacci retracement
        if len(waves) >= 4:
            wave4 = waves[3]
            retracement_ratio = wave4.magnitude / waves[2].magnitude

            if 0.35 <= retracement_ratio <= 0.42:  # Near 38.2%
                confidence += 10

        return min(confidence, 100.0)

    def detect_leading_diagonal(
        self,
        df: pd.DataFrame,
        is_bullish: bool = True,
    ) -> Optional[ElliottWavePattern]:
        """
        Detect Leading Diagonal pattern (Wave 1 or Wave A).

        Leading Diagonal characteristics:
        - 5-wave structure with 3-3-3-3-3 or 5-3-5-3-5 subdivisions
        - Wave 4 overlaps with Wave 1 (key difference from impulse)
        - Wedge shape with converging trendlines
        - Wave 1 is typically the longest
        - Occurs at the start of a trend (Wave 1 or Wave A)

        Args:
            df: DataFrame with OHLC data.
            is_bullish: True for bullish diagonal, False for bearish.

        Returns:
            ElliottWavePattern if detected, None otherwise.
        """
        pivot_highs, pivot_lows = self.find_pivots(df)

        if is_bullish:
            pivots = self._alternate_pivots(pivot_lows, pivot_highs, start_with_low=True)
        else:
            pivots = self._alternate_pivots(pivot_highs, pivot_lows, start_with_low=False)

        if len(pivots) < 6:
            return None

        # Build 5 waves
        waves = []
        for i in range(5):
            start_idx = pivots[i]
            end_idx = pivots[i + 1]

            wave = Wave(
                wave_number=i + 1,
                start_idx=start_idx,
                end_idx=end_idx,
                start_price=df.iloc[start_idx]['close'],
                end_price=df.iloc[end_idx]['close'],
                move_type='diagonal',
            )
            waves.append(wave)

        # Validate leading diagonal rules
        if not self._validate_leading_diagonal(waves, is_bullish):
            return None

        # Calculate Fibonacci levels
        fib_levels = self._calculate_wave_fibs(waves, is_bullish)

        # Determine current wave
        current_wave = self._determine_current_wave(waves, df)

        # Calculate confidence
        confidence = self._calculate_diagonal_confidence(waves, is_bullish)

        return ElliottWavePattern(
            waves=waves,
            pattern_type='leading_diagonal',
            direction='bullish' if is_bullish else 'bearish',
            current_wave=current_wave,
            fib_levels=fib_levels,
            confidence=confidence,
        )

    def _validate_leading_diagonal(self, waves: List[Wave], is_bullish: bool) -> bool:
        """
        Validate Leading Diagonal rules.

        Rules:
        1. Wave 4 overlaps with Wave 1 (key characteristic)
        2. Wave 1 is usually the longest, Wave 3 > Wave 5
        3. Wedge shape (converging trendlines)
        """
        if len(waves) < 5:
            return False

        wave1, wave2, wave3, wave4, wave5 = waves[:5]

        # Rule 1: Wave 4 MUST overlap with Wave 1 (opposite of impulse)
        if is_bullish:
            # For bullish, Wave 4 low should be below Wave 1 high
            if wave4.end_price >= wave1.end_price:
                return False
        else:
            # For bearish, Wave 4 high should be above Wave 1 low
            if wave4.end_price <= wave1.end_price:
                return False

        # Rule 2: Wave 1 is typically longest, Wave 3 > Wave 5
        wave1_mag = wave1.magnitude
        wave3_mag = wave3.magnitude
        wave5_mag = wave5.magnitude

        if wave3_mag < wave5_mag:
            return False

        # Rule 3: Check for wedge shape (Wave 5 < Wave 3 < Wave 1)
        if not (wave5_mag < wave3_mag <= wave1_mag):
            # Allow some tolerance
            if not (wave5_mag < wave1_mag):
                return False

        return True

    def detect_ending_diagonal(
        self,
        df: pd.DataFrame,
        is_bullish: bool = True,
    ) -> Optional[ElliottWavePattern]:
        """
        Detect Ending Diagonal pattern (Wave 5 or Wave C).

        Ending Diagonal characteristics:
        - 5-wave structure with 3-3-3-3-3 subdivisions
        - Wave 4 overlaps with Wave 1
        - Wedge shape with converging trendlines
        - Wave 1 is longest, Wave 3 can't be shorter than Wave 5
        - Occurs at end of trend (exhaustion pattern)
        - Often accompanied by RSI/MACD divergence

        Args:
            df: DataFrame with OHLC data.
            is_bullish: True for bullish diagonal, False for bearish.

        Returns:
            ElliottWavePattern if detected, None otherwise.
        """
        pivot_highs, pivot_lows = self.find_pivots(df)

        if is_bullish:
            pivots = self._alternate_pivots(pivot_lows, pivot_highs, start_with_low=True)
        else:
            pivots = self._alternate_pivots(pivot_highs, pivot_lows, start_with_low=False)

        if len(pivots) < 6:
            return None

        # Build 5 waves
        waves = []
        for i in range(5):
            start_idx = pivots[i]
            end_idx = pivots[i + 1]

            wave = Wave(
                wave_number=i + 1,
                start_idx=start_idx,
                end_idx=end_idx,
                start_price=df.iloc[start_idx]['close'],
                end_price=df.iloc[end_idx]['close'],
                move_type='diagonal',
            )
            waves.append(wave)

        # Validate ending diagonal rules
        if not self._validate_ending_diagonal(waves, is_bullish):
            return None

        # Calculate Fibonacci levels
        fib_levels = self._calculate_wave_fibs(waves, is_bullish)

        # Determine current wave
        current_wave = self._determine_current_wave(waves, df)

        # Calculate confidence (ending diagonals are high-value patterns)
        confidence = self._calculate_diagonal_confidence(waves, is_bullish, is_ending=True)

        return ElliottWavePattern(
            waves=waves,
            pattern_type='ending_diagonal',
            direction='bullish' if is_bullish else 'bearish',
            current_wave=current_wave,
            fib_levels=fib_levels,
            confidence=confidence,
        )

    def _validate_ending_diagonal(self, waves: List[Wave], is_bullish: bool) -> bool:
        """
        Validate Ending Diagonal rules.

        Rules:
        1. Wave 4 overlaps with Wave 1 (key characteristic)
        2. Wave 1 > Wave 3 > Wave 5 (contracting pattern)
        3. Converging wedge shape
        """
        if len(waves) < 5:
            return False

        wave1, wave2, wave3, wave4, wave5 = waves[:5]

        # Rule 1: Wave 4 overlaps with Wave 1
        if is_bullish:
            if wave4.end_price >= wave1.end_price:
                return False
        else:
            if wave4.end_price <= wave1.end_price:
                return False

        # Rule 2: Contracting pattern - Wave 1 longest, Wave 5 shortest
        wave1_mag = wave1.magnitude
        wave3_mag = wave3.magnitude
        wave5_mag = wave5.magnitude

        # Wave 3 cannot be shorter than Wave 5
        if wave3_mag < wave5_mag:
            return False

        # Wave 1 should be longest
        if wave1_mag < wave3_mag or wave1_mag < wave5_mag:
            return False

        return True

    def _calculate_diagonal_confidence(
        self,
        waves: List[Wave],
        is_bullish: bool,
        is_ending: bool = False,
    ) -> float:
        """Calculate confidence for diagonal patterns."""
        confidence = 60.0  # Base confidence for diagonals

        if len(waves) < 5:
            return 0.0

        wave1, wave2, wave3, wave4, wave5 = waves[:5]

        # Check for proper wedge shape
        wave1_mag = wave1.magnitude
        wave3_mag = wave3.magnitude
        wave5_mag = wave5.magnitude

        # Perfect wedge: Wave 1 > Wave 3 > Wave 5
        if wave1_mag > wave3_mag > wave5_mag:
            confidence += 20

        # Check Wave 4 retracement (should be smaller than Wave 2)
        wave2_retracement = wave2.magnitude / wave1_mag
        wave4_retracement = wave4.magnitude / wave3.magnitude

        if wave4_retracement < wave2_retracement:
            confidence += 10

        # Ending diagonals are high-value reversal signals
        if is_ending:
            confidence += 10

        return min(confidence, 100.0)

    def detect_truncation(
        self,
        waves: List[Wave],
        is_bullish: bool,
    ) -> bool:
        """
        Detect if Wave 5 is truncated (fails to exceed Wave 3).

        Truncation characteristics:
        - Wave 5 has 5 sub-waves but doesn't exceed Wave 3 high/low
        - Usually occurs after a very strong extended Wave 3
        - Often forms a double top/bottom pattern

        Args:
            waves: List of 5 waves (impulse pattern).
            is_bullish: True for bullish pattern.

        Returns:
            True if Wave 5 is truncated.
        """
        if len(waves) < 5:
            return False

        wave3 = waves[2]
        wave5 = waves[4]

        if is_bullish:
            # Bullish truncation: Wave 5 fails to exceed Wave 3 high
            return wave5.end_price < wave3.end_price
        else:
            # Bearish truncation: Wave 5 fails to exceed Wave 3 low
            return wave5.end_price > wave3.end_price

    def identify_extended_wave(
        self,
        waves: List[Wave],
    ) -> Optional[int]:
        """
        Identify which wave is extended (1, 3, or 5).

        Extension characteristics:
        - Most impulses have one extended wave
        - Wave 3 is most commonly extended (161.8%-261.8% of Wave 1)
        - Only one wave can be extended
        - Extended wave is significantly larger than others

        Args:
            waves: List of 5 waves (impulse pattern).

        Returns:
            Wave number that is extended (1, 3, or 5), or None.
        """
        if len(waves) < 5:
            return None

        wave1_mag = waves[0].magnitude
        wave3_mag = waves[2].magnitude
        wave5_mag = waves[4].magnitude

        # Calculate extension ratios
        w3_to_w1 = wave3_mag / wave1_mag if wave1_mag > 0 else 0
        w5_to_w1 = wave5_mag / wave1_mag if wave1_mag > 0 else 0
        w5_to_w3 = wave5_mag / wave3_mag if wave3_mag > 0 else 0

        # Wave 3 extended (most common)
        if w3_to_w1 >= 1.5 and wave3_mag > wave5_mag:
            return 3

        # Wave 5 extended
        elif w5_to_w3 >= 1.3 and wave5_mag > wave3_mag and wave5_mag > wave1_mag:
            return 5

        # Wave 1 extended (rare)
        elif wave1_mag > wave3_mag and wave1_mag > wave5_mag:
            return 1

        return None

    def detect_zigzag_correction(
        self,
        df: pd.DataFrame,
        is_bullish: bool = False,  # Corrections move against trend
    ) -> Optional[ElliottWavePattern]:
        """
        Detect Zig-Zag correction pattern (A-B-C).

        Zig-Zag characteristics:
        - 5-3-5 structure (Wave A has 5 sub-waves, B has 3, C has 5)
        - Sharp correction against major trend
        - Wave B < Wave A (Wave B doesn't retrace 100% of A)
        - Wave C = 100%-161.8% of Wave A
        - Most common corrective pattern

        Args:
            df: DataFrame with OHLC data.
            is_bullish: False for correction (moves opposite to trend).

        Returns:
            ElliottWavePattern if detected, None otherwise.
        """
        pivot_highs, pivot_lows = self.find_pivots(df)

        # Zig-zag moves opposite to trend
        if is_bullish:
            # Bullish zig-zag (correction in downtrend)
            pivots = self._alternate_pivots(pivot_lows, pivot_highs, start_with_low=True)
        else:
            # Bearish zig-zag (correction in uptrend)
            pivots = self._alternate_pivots(pivot_highs, pivot_lows, start_with_low=False)

        if len(pivots) < 4:
            return None

        # Build A-B-C waves
        waves = []
        wave_labels = ['A', 'B', 'C']
        for i in range(3):
            start_idx = pivots[i]
            end_idx = pivots[i + 1]

            wave = Wave(
                wave_number=i,  # Store as 0, 1, 2 (will use A, B, C for display)
                start_idx=start_idx,
                end_idx=end_idx,
                start_price=df.iloc[start_idx]['close'],
                end_price=df.iloc[end_idx]['close'],
                move_type='correction',
            )
            waves.append(wave)

        # Validate zig-zag rules
        if not self._validate_zigzag(waves, is_bullish):
            return None

        # Calculate Fibonacci levels
        fib_levels = self._calculate_correction_fibs(waves, is_bullish)

        # Determine current wave
        current_wave = self._determine_current_wave(waves, df)

        # Calculate confidence
        confidence = self._calculate_correction_confidence(waves, fib_levels)

        return ElliottWavePattern(
            waves=waves,
            pattern_type='zigzag',
            direction='bullish' if is_bullish else 'bearish',
            current_wave=current_wave,
            fib_levels=fib_levels,
            confidence=confidence,
        )

    def _validate_zigzag(self, waves: List[Wave], is_bullish: bool) -> bool:
        """
        Validate Zig-Zag correction rules.

        Rules:
        1. Wave B must be shorter than Wave A
        2. Wave B cannot retrace more than 100% of Wave A
        3. Wave C typically 100%-161.8% of Wave A
        """
        if len(waves) < 3:
            return False

        waveA, waveB, waveC = waves[:3]

        # Rule 1 & 2: Wave B < Wave A
        if waveB.magnitude >= waveA.magnitude:
            return False

        # Wave B shouldn't go beyond Wave A start (100% retracement)
        if is_bullish:
            if waveB.end_price <= waveA.start_price:
                return False
        else:
            if waveB.end_price >= waveA.start_price:
                return False

        # Rule 3: Wave C typically between 100%-200% of Wave A
        wave_c_ratio = waveC.magnitude / waveA.magnitude
        if wave_c_ratio < 0.8 or wave_c_ratio > 2.5:
            return False

        return True

    def detect_flat_correction(
        self,
        df: pd.DataFrame,
        is_bullish: bool = False,
    ) -> Optional[ElliottWavePattern]:
        """
        Detect Flat correction pattern (A-B-C).

        Flat characteristics:
        - 3-3-5 structure (Wave A has 3 sub-waves, B has 3, C has 5)
        - Sideways correction
        - Wave B retraces most or all of Wave A
        - Three types: Regular, Expanded, Running

        Args:
            df: DataFrame with OHLC data.
            is_bullish: False for correction.

        Returns:
            ElliottWavePattern if detected, None otherwise.
        """
        pivot_highs, pivot_lows = self.find_pivots(df)

        if is_bullish:
            pivots = self._alternate_pivots(pivot_lows, pivot_highs, start_with_low=True)
        else:
            pivots = self._alternate_pivots(pivot_highs, pivot_lows, start_with_low=False)

        if len(pivots) < 4:
            return None

        # Build A-B-C waves
        waves = []
        for i in range(3):
            start_idx = pivots[i]
            end_idx = pivots[i + 1]

            wave = Wave(
                wave_number=i,
                start_idx=start_idx,
                end_idx=end_idx,
                start_price=df.iloc[start_idx]['close'],
                end_price=df.iloc[end_idx]['close'],
                move_type='correction',
            )
            waves.append(wave)

        # Validate flat and determine subtype
        flat_subtype = self._validate_and_classify_flat(waves, is_bullish)
        if not flat_subtype:
            return None

        # Calculate Fibonacci levels
        fib_levels = self._calculate_correction_fibs(waves, is_bullish)

        # Determine current wave
        current_wave = self._determine_current_wave(waves, df)

        # Calculate confidence
        confidence = self._calculate_correction_confidence(waves, fib_levels)

        return ElliottWavePattern(
            waves=waves,
            pattern_type='flat',
            direction='bullish' if is_bullish else 'bearish',
            current_wave=current_wave,
            fib_levels=fib_levels,
            confidence=confidence,
            subtype=flat_subtype,
        )

    def _validate_and_classify_flat(self, waves: List[Wave], is_bullish: bool) -> Optional[str]:
        """
        Validate and classify flat correction type.

        Returns:
            'regular_flat', 'expanded_flat', or 'running_flat', or None if invalid.
        """
        if len(waves) < 3:
            return None

        waveA, waveB, waveC = waves[:3]

        # Wave B should retrace most of Wave A (80%+)
        wave_b_retracement = waveB.magnitude / waveA.magnitude
        if wave_b_retracement < 0.8:
            return None

        # Classify based on Wave B and C relative to Wave A
        if is_bullish:
            # Regular Flat: B near A start, C near A end
            if (waveB.end_price <= waveA.start_price * 1.05 and
                waveC.end_price >= waveA.end_price * 0.95):
                return 'regular_flat'

            # Expanded Flat: B exceeds A start, C exceeds A end
            elif (waveB.end_price > waveA.start_price and
                  waveC.end_price < waveA.end_price):
                return 'expanded_flat'

            # Running Flat: B exceeds A start, C above A end
            elif (waveB.end_price > waveA.start_price and
                  waveC.end_price > waveA.end_price):
                return 'running_flat'
        else:
            # Bearish variations
            if (waveB.end_price >= waveA.start_price * 0.95 and
                waveC.end_price <= waveA.end_price * 1.05):
                return 'regular_flat'
            elif (waveB.end_price < waveA.start_price and
                  waveC.end_price > waveA.end_price):
                return 'expanded_flat'
            elif (waveB.end_price < waveA.start_price and
                  waveC.end_price < waveA.end_price):
                return 'running_flat'

        return None

    def detect_triangle_pattern(
        self,
        df: pd.DataFrame,
        is_bullish: bool = False,
    ) -> Optional[ElliottWavePattern]:
        """
        Detect Triangle correction pattern (A-B-C-D-E).

        Triangle characteristics:
        - 3-3-3-3-3 structure (5 overlapping waves, all corrective)
        - Converging or diverging trendlines
        - Represents balance between buyers and sellers
        - Wave E often overshoots trendline
        - Only occurs as Wave 4, B, X, or Y (never Wave 2 or A)

        Types:
        - Contracting (most common)
        - Barrier (one flat side)
        - Expanding (rare)

        Args:
            df: DataFrame with OHLC data.
            is_bullish: Pattern direction.

        Returns:
            ElliottWavePattern if detected, None otherwise.
        """
        pivot_highs, pivot_lows = self.find_pivots(df, order=3)  # Smaller order for triangles

        if is_bullish:
            pivots = self._alternate_pivots(pivot_lows, pivot_highs, start_with_low=True)
        else:
            pivots = self._alternate_pivots(pivot_highs, pivot_lows, start_with_low=False)

        if len(pivots) < 6:
            return None

        # Build A-B-C-D-E waves
        waves = []
        for i in range(5):
            start_idx = pivots[i]
            end_idx = pivots[i + 1]

            wave = Wave(
                wave_number=i,  # A=0, B=1, C=2, D=3, E=4
                start_idx=start_idx,
                end_idx=end_idx,
                start_price=df.iloc[start_idx]['close'],
                end_price=df.iloc[end_idx]['close'],
                move_type='correction',
            )
            waves.append(wave)

        # Validate triangle and determine subtype
        triangle_subtype = self._validate_and_classify_triangle(waves)
        if not triangle_subtype:
            return None

        # Calculate Fibonacci levels
        fib_levels = []  # Triangles don't use standard Fibonacci relationships

        # Determine current wave
        current_wave = self._determine_current_wave(waves, df)

        # Calculate confidence
        confidence = self._calculate_triangle_confidence(waves, triangle_subtype)

        return ElliottWavePattern(
            waves=waves,
            pattern_type='triangle',
            direction='bullish' if is_bullish else 'bearish',
            current_wave=current_wave,
            fib_levels=fib_levels,
            confidence=confidence,
            subtype=triangle_subtype,
        )

    def _validate_and_classify_triangle(self, waves: List[Wave]) -> Optional[str]:
        """
        Validate and classify triangle type.

        Returns:
            'contracting_triangle', 'barrier_triangle', or 'expanding_triangle', or None.
        """
        if len(waves) < 5:
            return None

        # Check if waves are getting progressively smaller (contracting)
        # or larger (expanding)
        magnitudes = [w.magnitude for w in waves]

        # Contracting: Each wave smaller than previous
        is_contracting = all(magnitudes[i] > magnitudes[i+1] for i in range(len(magnitudes)-1))

        # Expanding: Each wave larger than previous (rare)
        is_expanding = all(magnitudes[i] < magnitudes[i+1] for i in range(len(magnitudes)-1))

        # Check for overlapping waves (key triangle characteristic)
        has_overlaps = self._check_triangle_overlaps(waves)
        if not has_overlaps:
            return None

        if is_contracting:
            return 'contracting_triangle'
        elif is_expanding:
            return 'expanding_triangle'
        else:
            # Barrier or irregular triangle
            return 'barrier_triangle'

    def _check_triangle_overlaps(self, waves: List[Wave]) -> bool:
        """Check if triangle waves overlap (key characteristic)."""
        # In triangles, waves should overlap with each other
        # This is different from impulses where overlap is forbidden
        overlap_count = 0

        for i in range(len(waves) - 1):
            wave_a = waves[i]
            wave_b = waves[i + 1]

            # Check if price ranges overlap
            if (min(wave_a.start_price, wave_a.end_price) <=
                max(wave_b.start_price, wave_b.end_price) and
                max(wave_a.start_price, wave_a.end_price) >=
                min(wave_b.start_price, wave_b.end_price)):
                overlap_count += 1

        # At least 3 of the 4 connections should overlap
        return overlap_count >= 3

    def _calculate_triangle_confidence(self, waves: List[Wave], subtype: str) -> float:
        """Calculate confidence for triangle pattern."""
        confidence = 55.0  # Base confidence

        # Contracting triangles are most common and reliable
        if subtype == 'contracting_triangle':
            confidence += 15

        # Check for progressively smaller waves
        magnitudes = [w.magnitude for w in waves]
        if all(magnitudes[i] >= magnitudes[i+1] for i in range(len(magnitudes)-1)):
            confidence += 15

        # Check for 5 waves
        if len(waves) == 5:
            confidence += 10

        return min(confidence, 100.0)

    def _calculate_correction_fibs(
        self,
        waves: List[Wave],
        is_bullish: bool,
    ) -> List[FibonacciLevel]:
        """Calculate Fibonacci levels for corrections (A-B-C)."""
        fib_levels = []

        if len(waves) >= 2:
            # Wave B retracements of Wave A
            waveB_fibs = self.fib_calc.calculate_retracements(
                waves[0].start_price,
                waves[0].end_price,
                is_uptrend=is_bullish,
            )
            fib_levels.extend(waveB_fibs)

        if len(waves) >= 3:
            # Wave C targets (100%, 161.8% of Wave A)
            waveC_targets = self.fib_calc.calculate_extensions(
                waves[0].start_price,
                waves[0].end_price,
                waves[1].end_price,
                is_uptrend=is_bullish,
            )
            fib_levels.extend(waveC_targets)

        return fib_levels

    def _calculate_correction_confidence(
        self,
        waves: List[Wave],
        fib_levels: List[FibonacciLevel],
    ) -> float:
        """Calculate confidence for correction patterns."""
        confidence = 50.0

        if len(waves) >= 3:
            waveA, waveB, waveC = waves[:3]

            # Check Wave C = Wave A (common ratio)
            wave_c_ratio = waveC.magnitude / waveA.magnitude
            if 0.95 <= wave_c_ratio <= 1.05:  # Wave C ≈ 100% of Wave A
                confidence += 15
            elif 1.55 <= wave_c_ratio <= 1.65:  # Wave C ≈ 161.8% of Wave A
                confidence += 20

            # Check Wave B retracement
            wave_b_retracement = waveB.magnitude / waveA.magnitude
            if 0.48 <= wave_b_retracement <= 0.52:  # 50% retracement
                confidence += 10
            elif 0.60 <= wave_b_retracement <= 0.65:  # 61.8% retracement
                confidence += 10

        return min(confidence, 100.0)
