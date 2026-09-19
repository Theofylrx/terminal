"""Smart Money Concepts (SMC) - Complete 14-Pattern Implementation."""

import logging
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timezone
import pandas as pd
import numpy as np


logger = logging.getLogger(__name__)


class StructureType(str, Enum):
    """Market structure types."""

    BOS_BULLISH = "bos_bullish"  # Break of Structure (bullish)
    BOS_BEARISH = "bos_bearish"  # Break of Structure (bearish)
    CHOCH_BULLISH = "choch_bullish"  # Change of Character (bullish)
    CHOCH_BEARISH = "choch_bearish"  # Change of Character (bearish)


class ZoneType(str, Enum):
    """Supply/Demand zone types."""

    DEMAND_ZONE = "demand"  # Support/buying zone
    SUPPLY_ZONE = "supply"  # Resistance/selling zone
    ORDER_BLOCK_BULLISH = "order_block_bullish"
    ORDER_BLOCK_BEARISH = "order_block_bearish"


@dataclass
class BreakOfStructure:
    """Break of Structure or Change of Character."""

    structure_type: StructureType
    break_idx: int
    break_price: float
    previous_level: float
    strength: float  # Percentage of break
    volume_confirmation: bool
    description: str

    @property
    def is_bullish(self) -> bool:
        """Check if structure break is bullish."""
        return self.structure_type in [
            StructureType.BOS_BULLISH,
            StructureType.CHOCH_BULLISH,
        ]


@dataclass
class FairValueGap:
    """Fair Value Gap (FVG) - Imbalance in price."""

    direction: str  # 'bullish' or 'bearish'
    start_idx: int
    end_idx: int
    gap_high: float
    gap_low: float
    filled: bool  # True if gap has been filled
    strength: float

    @property
    def gap_size(self) -> float:
        """Calculate gap size."""
        return self.gap_high - self.gap_low

    @property
    def midpoint(self) -> float:
        """Calculate gap midpoint."""
        return (self.gap_high + self.gap_low) / 2


@dataclass
class SupplyDemandZone:
    """Supply or Demand zone."""

    zone_type: ZoneType
    start_idx: int
    end_idx: int
    zone_high: float
    zone_low: float
    strength: float  # Based on touches and reactions
    active: bool  # True if zone hasn't been violated
    touches: int  # Number of times price touched zone

    @property
    def zone_size(self) -> float:
        """Calculate zone size."""
        return self.zone_high - self.zone_low

    @property
    def midpoint(self) -> float:
        """Calculate zone midpoint."""
        return (self.zone_high + self.zone_low) / 2

    @property
    def is_supply(self) -> bool:
        """Check if zone is supply (resistance)."""
        return self.zone_type in [ZoneType.SUPPLY_ZONE, ZoneType.ORDER_BLOCK_BEARISH]


@dataclass
class EqualHighsLows:
    """Equal Highs/Lows (EQH/EQL) - Multiple swing points at same level."""

    eq_type: str  # 'equal_highs' or 'equal_lows'
    level: float  # Price level
    indices: List[int]  # Candle indices where equal highs/lows occur
    count: int  # Number of equal touches (2+)
    tolerance: float  # Percentage tolerance (e.g., 0.003 = 0.3%)
    swept: bool  # True if level has been swept
    sweep_idx: Optional[int]  # Index where sweep occurred
    strength: float  # Based on count and how tight the cluster is

    @property
    def is_equal_highs(self) -> bool:
        """Check if this is equal highs (resistance)."""
        return self.eq_type == 'equal_highs'

    @property
    def is_equal_lows(self) -> bool:
        """Check if this is equal lows (support)."""
        return self.eq_type == 'equal_lows'


@dataclass
class OrderFlow:
    """Order Flow (OF) - Last opposing move before directional change."""

    of_type: str  # 'bullish_of' or 'bearish_of'
    candle_idx: int  # Index of order flow candle
    zone_high: float  # High of order flow zone
    zone_low: float  # Low of order flow zone
    strength: float  # Strength of subsequent move
    active: bool  # True if zone hasn't been violated
    description: str

    @property
    def is_bullish(self) -> bool:
        """Check if order flow is bullish."""
        return self.of_type == 'bullish_of'


@dataclass
class InstitutionalFundingCandle:
    """IFC - Candle that sweeps liquidity but doesn't close beyond level."""

    ifc_type: str  # 'bullish_ifc' or 'bearish_ifc'
    candle_idx: int  # Index of IFC candle
    swept_level: float  # Level that was swept
    wick_extreme: float  # Highest high or lowest low
    close_price: float  # Close back inside range
    strength: float  # How strong the sweep and reversal
    reversal_confirmed: bool  # True if next candle confirms reversal
    description: str

    @property
    def is_bullish(self) -> bool:
        """Check if IFC is bullish."""
        return self.ifc_type == 'bullish_ifc'


@dataclass
class SessionLiquidity:
    """Session-based liquidity levels (Asia/London/NY)."""

    session_name: str  # 'asia', 'london', 'new_york'
    session_date: str  # Date of session (YYYY-MM-DD)
    session_high: float
    session_low: float
    high_swept: bool  # True if high has been swept
    low_swept: bool  # True if low has been swept
    high_sweep_idx: Optional[int]  # Where high was swept
    low_sweep_idx: Optional[int]  # Where low was swept

    @property
    def range_size(self) -> float:
        """Calculate session range."""
        return self.session_high - self.session_low

    @property
    def midpoint(self) -> float:
        """Calculate session midpoint."""
        return (self.session_high + self.session_low) / 2


class SmartMoneyConceptsDetector:
    """
    Smart Money Concepts (SMC) detector - Complete 14-Pattern Implementation.

    Detects institutional trading patterns:

    Core Patterns (6):
    - BOS (Break of Structure) - Trend continuation
    - CHoCH (Change of Character) - Trend reversal
    - FVG (Fair Value Gap) - Price imbalances
    - Supply/Demand Zones - Institutional S/R areas
    - Order Blocks (OB) - Institutional entry zones
    - Liquidity Sweeps (BSL/SSL) - Stop hunts

    Additional Patterns (8):
    - EQH/EQL (Equal Highs/Lows) - Liquidity pools
    - Order Flow (OF) - General institutional zones
    - IFC (Institutional Funding Candle) - Reversal candles
    - FBOS (False Break of Structure) - False signals
    - Session Liquidity - Asia/London/NY levels
    - PDH/PDL - Previous Day/Week High/Low
    - SMT (Smart Money Trap) - First pullback traps
    - IDM (Inducement) - Retail traps
    """

    def __init__(self, min_structure_break: float = 0.001):
        """
        Initialize SMC detector.

        Args:
            min_structure_break: Minimum % for structure break (0.1%).
        """
        self.min_structure_break = min_structure_break

    def detect_break_of_structure(
        self,
        df: pd.DataFrame,
        lookback: int = 20,
    ) -> List[BreakOfStructure]:
        """
        Detect Break of Structure (BOS) and Change of Character (CHoCH).

        BOS: Price breaks previous high/low in direction of trend.
        CHoCH: Price breaks structure against trend (trend reversal).

        Args:
            df: DataFrame with OHLC data.
            lookback: Bars to look back for structure.

        Returns:
            List of structure breaks.
        """
        breaks = []

        # Find swing highs and lows
        swing_highs, swing_lows = self._find_swing_points(df)

        # Detect bullish BOS
        for i in range(len(df) - 1):
            if i < lookback:
                continue

            # Find previous swing high
            prev_highs = [df['high'].iloc[idx] for idx in swing_highs if idx < i]
            if not prev_highs:
                continue

            recent_high = max(prev_highs[-3:])  # Last 3 swing highs

            # Check if current price broke above
            current_high = df['high'].iloc[i]
            if current_high > recent_high:
                break_strength = (current_high - recent_high) / recent_high

                if break_strength >= self.min_structure_break:
                    # Determine if BOS or CHoCH based on trend
                    is_uptrend = self._is_uptrend(df, i, lookback)

                    structure_type = (
                        StructureType.BOS_BULLISH if is_uptrend
                        else StructureType.CHOCH_BULLISH
                    )

                    volume_conf = self._check_volume_confirmation(df, i)

                    breaks.append(BreakOfStructure(
                        structure_type=structure_type,
                        break_idx=i,
                        break_price=current_high,
                        previous_level=recent_high,
                        strength=break_strength * 100,
                        volume_confirmation=volume_conf,
                        description=f"{'BOS' if is_uptrend else 'CHoCH'} Bullish: Broke ${recent_high:.2f} at ${current_high:.2f}",
                    ))

        # Detect bearish BOS
        for i in range(len(df) - 1):
            if i < lookback:
                continue

            # Find previous swing low
            prev_lows = [df['low'].iloc[idx] for idx in swing_lows if idx < i]
            if not prev_lows:
                continue

            recent_low = min(prev_lows[-3:])  # Last 3 swing lows

            # Check if current price broke below
            current_low = df['low'].iloc[i]
            if current_low < recent_low:
                break_strength = (recent_low - current_low) / recent_low

                if break_strength >= self.min_structure_break:
                    # Determine if BOS or CHoCH
                    is_downtrend = self._is_downtrend(df, i, lookback)

                    structure_type = (
                        StructureType.BOS_BEARISH if is_downtrend
                        else StructureType.CHOCH_BEARISH
                    )

                    volume_conf = self._check_volume_confirmation(df, i)

                    breaks.append(BreakOfStructure(
                        structure_type=structure_type,
                        break_idx=i,
                        break_price=current_low,
                        previous_level=recent_low,
                        strength=break_strength * 100,
                        volume_confirmation=volume_conf,
                        description=f"{'BOS' if is_downtrend else 'CHoCH'} Bearish: Broke ${recent_low:.2f} at ${current_low:.2f}",
                    ))

        return breaks

    def detect_fair_value_gaps(self, df: pd.DataFrame) -> List[FairValueGap]:
        """
        Detect Fair Value Gaps (FVG).

        FVG occurs when there's a gap between candles indicating
        an imbalance that price may return to fill.

        Bullish FVG: Candle 1 high < Candle 3 low (gap between)
        Bearish FVG: Candle 1 low > Candle 3 high (gap between)

        Args:
            df: DataFrame with OHLC data.

        Returns:
            List of Fair Value Gaps.
        """
        fvgs = []

        for i in range(2, len(df)):
            candle1 = df.iloc[i - 2]
            candle2 = df.iloc[i - 1]
            candle3 = df.iloc[i]

            # Bullish FVG
            if candle1['high'] < candle3['low']:
                gap_low = candle1['high']
                gap_high = candle3['low']
                gap_size = gap_high - gap_low

                # Check if gap was filled
                filled = self._check_gap_filled(df, i, gap_low, gap_high, 'bullish')

                strength = gap_size / candle2['close'] * 100

                fvgs.append(FairValueGap(
                    direction='bullish',
                    start_idx=i - 2,
                    end_idx=i,
                    gap_high=gap_high,
                    gap_low=gap_low,
                    filled=filled,
                    strength=strength,
                ))

            # Bearish FVG
            elif candle1['low'] > candle3['high']:
                gap_high = candle1['low']
                gap_low = candle3['high']
                gap_size = gap_high - gap_low

                # Check if gap was filled
                filled = self._check_gap_filled(df, i, gap_low, gap_high, 'bearish')

                strength = gap_size / candle2['close'] * 100

                fvgs.append(FairValueGap(
                    direction='bearish',
                    start_idx=i - 2,
                    end_idx=i,
                    gap_high=gap_high,
                    gap_low=gap_low,
                    filled=filled,
                    strength=strength,
                ))

        return fvgs

    def detect_supply_demand_zones(
        self,
        df: pd.DataFrame,
        min_touches: int = 2,
    ) -> List[SupplyDemandZone]:
        """
        Detect Supply and Demand zones.

        Supply zones: Areas where price reversed down (resistance).
        Demand zones: Areas where price reversed up (support).

        Args:
            df: DataFrame with OHLC data.
            min_touches: Minimum touches to confirm zone.

        Returns:
            List of Supply/Demand zones.
        """
        zones = []

        # Find swing points
        swing_highs, swing_lows = self._find_swing_points(df)

        # Detect demand zones (support)
        for idx in swing_lows:
            if idx >= len(df) - 5:
                continue

            # Define zone around swing low
            zone_low = df['low'].iloc[idx] * 0.995  # 0.5% below
            zone_high = df['low'].iloc[idx] * 1.005  # 0.5% above

            # Count touches
            touches = self._count_zone_touches(df, idx + 1, zone_low, zone_high)

            if touches >= min_touches:
                # Check if zone is still active (not violated)
                active = self._check_zone_active(df, idx, zone_low, zone_high, 'demand')

                strength = min(touches * 20, 100)  # Max 100

                zones.append(SupplyDemandZone(
                    zone_type=ZoneType.DEMAND_ZONE,
                    start_idx=idx,
                    end_idx=idx + 20,  # Zone extends forward
                    zone_high=zone_high,
                    zone_low=zone_low,
                    strength=strength,
                    active=active,
                    touches=touches,
                ))

        # Detect supply zones (resistance)
        for idx in swing_highs:
            if idx >= len(df) - 5:
                continue

            # Define zone around swing high
            zone_low = df['high'].iloc[idx] * 0.995
            zone_high = df['high'].iloc[idx] * 1.005

            # Count touches
            touches = self._count_zone_touches(df, idx + 1, zone_low, zone_high)

            if touches >= min_touches:
                # Check if zone is still active
                active = self._check_zone_active(df, idx, zone_low, zone_high, 'supply')

                strength = min(touches * 20, 100)

                zones.append(SupplyDemandZone(
                    zone_type=ZoneType.SUPPLY_ZONE,
                    start_idx=idx,
                    end_idx=idx + 20,
                    zone_high=zone_high,
                    zone_low=zone_low,
                    strength=strength,
                    active=active,
                    touches=touches,
                ))

        return zones

    def _find_swing_points(
        self,
        df: pd.DataFrame,
        order: int = 5,
    ) -> Tuple[List[int], List[int]]:
        """Find swing highs and lows."""
        swing_highs = []
        swing_lows = []

        for i in range(order, len(df) - order):
            # Swing high
            is_high = all(
                df['high'].iloc[i] > df['high'].iloc[i - j] and
                df['high'].iloc[i] > df['high'].iloc[i + j]
                for j in range(1, order + 1)
            )
            if is_high:
                swing_highs.append(i)

            # Swing low
            is_low = all(
                df['low'].iloc[i] < df['low'].iloc[i - j] and
                df['low'].iloc[i] < df['low'].iloc[i + j]
                for j in range(1, order + 1)
            )
            if is_low:
                swing_lows.append(i)

        return swing_highs, swing_lows

    def _is_uptrend(self, df: pd.DataFrame, idx: int, lookback: int) -> bool:
        """Check if market is in uptrend."""
        if idx < lookback:
            return False

        recent_prices = df['close'].iloc[idx - lookback:idx]
        return recent_prices.iloc[-1] > recent_prices.iloc[0]

    def _is_downtrend(self, df: pd.DataFrame, idx: int, lookback: int) -> bool:
        """Check if market is in downtrend."""
        if idx < lookback:
            return False

        recent_prices = df['close'].iloc[idx - lookback:idx]
        return recent_prices.iloc[-1] < recent_prices.iloc[0]

    def _check_volume_confirmation(self, df: pd.DataFrame, idx: int) -> bool:
        """Check if volume confirms the move."""
        if idx < 5:
            return False

        current_volume = df['volume'].iloc[idx]
        avg_volume = df['volume'].iloc[idx - 5:idx].mean()

        return current_volume > avg_volume * 1.5

    def _check_gap_filled(
        self,
        df: pd.DataFrame,
        start_idx: int,
        gap_low: float,
        gap_high: float,
        direction: str,
    ) -> bool:
        """Check if FVG has been filled."""
        if start_idx >= len(df) - 1:
            return False

        future_data = df.iloc[start_idx + 1:]

        if direction == 'bullish':
            # Check if price came back down to fill gap
            filled = (future_data['low'] <= gap_low).any()
        else:
            # Check if price came back up to fill gap
            filled = (future_data['high'] >= gap_high).any()

        return filled

    def _count_zone_touches(
        self,
        df: pd.DataFrame,
        start_idx: int,
        zone_low: float,
        zone_high: float,
    ) -> int:
        """Count how many times price touched the zone."""
        touches = 0

        for i in range(start_idx, min(start_idx + 50, len(df))):
            low = df['low'].iloc[i]
            high = df['high'].iloc[i]

            # Check if price touched zone
            if low <= zone_high and high >= zone_low:
                touches += 1

        return touches

    def _check_zone_active(
        self,
        df: pd.DataFrame,
        zone_idx: int,
        zone_low: float,
        zone_high: float,
        zone_type: str,
    ) -> bool:
        """Check if zone is still active (not violated)."""
        if zone_idx >= len(df) - 1:
            return True

        future_data = df.iloc[zone_idx + 1:]

        if zone_type == 'demand':
            # Demand zone violated if price closes below zone
            violated = (future_data['close'] < zone_low).any()
        else:
            # Supply zone violated if price closes above zone
            violated = (future_data['close'] > zone_high).any()

        return not violated

    def detect_order_blocks(
        self,
        df: pd.DataFrame,
        min_move_percentage: float = 0.02,  # 2% minimum move
    ) -> List[SupplyDemandZone]:
        """
        Detect Order Blocks (institutional buying/selling zones).

        Order Block characteristics:
        - Bullish Order Block: Last down candle before strong bullish move
        - Bearish Order Block: Last up candle before strong bearish move
        - Represents areas where institutions placed large orders
        - Acts as strong support/resistance when price returns

        Args:
            df: DataFrame with OHLC data.
            min_move_percentage: Minimum % move to qualify as "strong" (default 2%).

        Returns:
            List of Order Block zones.
        """
        order_blocks = []

        for i in range(2, len(df) - 2):
            current_candle = df.iloc[i]
            next_candle = df.iloc[i + 1]
            next_next_candle = df.iloc[i + 2]

            # Calculate move strength
            current_close = current_candle['close']
            future_high = df['high'].iloc[i+1:i+5].max() if i < len(df) - 5 else df['high'].iloc[i+1:].max()
            future_low = df['low'].iloc[i+1:i+5].min() if i < len(df) - 5 else df['low'].iloc[i+1:].min()

            # Bullish Order Block: Last bearish candle before strong bullish move
            if (current_candle['close'] < current_candle['open'] and  # Current candle is bearish
                next_candle['close'] > next_candle['open']):  # Next candle is bullish

                # Check for strong bullish move
                move_percentage = (future_high - current_close) / current_close
                if move_percentage >= min_move_percentage:
                    # Order block is the body of the last bearish candle
                    ob_high = max(current_candle['open'], current_candle['close'])
                    ob_low = min(current_candle['open'], current_candle['close'])

                    # Check if order block is still active
                    active = self._check_zone_active(df, i, ob_low, ob_high, 'demand')

                    # Count touches
                    touches = self._count_zone_touches(df, i + 1, ob_low, ob_high)

                    strength = min((move_percentage * 100) + (touches * 10), 100)

                    order_blocks.append(SupplyDemandZone(
                        zone_type=ZoneType.ORDER_BLOCK_BULLISH,
                        start_idx=i,
                        end_idx=i + 10,  # Order block extends forward
                        zone_high=ob_high,
                        zone_low=ob_low,
                        strength=strength,
                        active=active,
                        touches=touches,
                    ))

            # Bearish Order Block: Last bullish candle before strong bearish move
            elif (current_candle['close'] > current_candle['open'] and  # Current candle is bullish
                  next_candle['close'] < next_candle['open']):  # Next candle is bearish

                # Check for strong bearish move
                move_percentage = (current_close - future_low) / current_close
                if move_percentage >= min_move_percentage:
                    # Order block is the body of the last bullish candle
                    ob_high = max(current_candle['open'], current_candle['close'])
                    ob_low = min(current_candle['open'], current_candle['close'])

                    # Check if order block is still active
                    active = self._check_zone_active(df, i, ob_low, ob_high, 'supply')

                    # Count touches
                    touches = self._count_zone_touches(df, i + 1, ob_low, ob_high)

                    strength = min((move_percentage * 100) + (touches * 10), 100)

                    order_blocks.append(SupplyDemandZone(
                        zone_type=ZoneType.ORDER_BLOCK_BEARISH,
                        start_idx=i,
                        end_idx=i + 10,
                        zone_high=ob_high,
                        zone_low=ob_low,
                        strength=strength,
                        active=active,
                        touches=touches,
                    ))

        return order_blocks

    def detect_liquidity_sweeps(
        self,
        df: pd.DataFrame,
        lookback: int = 20,
    ) -> List[dict]:
        """
        Detect Liquidity Sweeps/Raids (stop hunts).

        Liquidity Sweep characteristics:
        - Price briefly breaks above previous high or below previous low
        - Quickly reverses back (false breakout)
        - Represents institutions "hunting stops" before real move
        - Often precedes strong move in opposite direction

        Args:
            df: DataFrame with OHLC data.
            lookback: Bars to look back for swing highs/lows.

        Returns:
            List of liquidity sweep events.
        """
        sweeps = []

        # Find swing points
        swing_highs, swing_lows = self._find_swing_points(df)

        for i in range(lookback, len(df) - 2):
            current_high = df['high'].iloc[i]
            current_low = df['low'].iloc[i]
            current_close = df['close'].iloc[i]
            next_close = df['close'].iloc[i + 1]

            # Find recent swing high
            recent_highs = [df['high'].iloc[idx] for idx in swing_highs if i - lookback <= idx < i]
            if recent_highs:
                swing_high = max(recent_highs)

                # Bullish Liquidity Sweep: High breaks above swing high, then closes below
                if (current_high > swing_high and  # Wick breaks above
                    current_close < swing_high):  # Closes back below

                    # Check for reversal (next candle bullish)
                    if next_close > current_close:
                        sweeps.append({
                            'type': 'bullish_sweep',
                            'idx': i,
                            'sweep_level': swing_high,
                            'high': current_high,
                            'close': current_close,
                            'description': f'Bullish liquidity sweep above ${swing_high:.2f}, closed at ${current_close:.2f}',
                            'reversal_confirmed': True,
                        })

            # Find recent swing low
            recent_lows = [df['low'].iloc[idx] for idx in swing_lows if i - lookback <= idx < i]
            if recent_lows:
                swing_low = min(recent_lows)

                # Bearish Liquidity Sweep: Low breaks below swing low, then closes above
                if (current_low < swing_low and  # Wick breaks below
                    current_close > swing_low):  # Closes back above

                    # Check for reversal (next candle bearish)
                    if next_close < current_close:
                        sweeps.append({
                            'type': 'bearish_sweep',
                            'idx': i,
                            'sweep_level': swing_low,
                            'low': current_low,
                            'close': current_close,
                            'description': f'Bearish liquidity sweep below ${swing_low:.2f}, closed at ${current_close:.2f}',
                            'reversal_confirmed': True,
                        })

        return sweeps

    def detect_equal_highs_lows(
        self,
        df: pd.DataFrame,
        tolerance: float = 0.003,  # 0.3% tolerance
        min_touches: int = 2,
        lookback: int = 50,
    ) -> List[EqualHighsLows]:
        """
        Detect Equal Highs and Equal Lows (EQH/EQL).

        Equal Highs/Lows are multiple swing points at approximately the same
        price level, representing major liquidity pools that institutions target.

        Args:
            df: DataFrame with OHLC data.
            tolerance: Price tolerance as percentage (0.003 = 0.3%).
            min_touches: Minimum number of equal touches required.
            lookback: Bars to look back for clustering.

        Returns:
            List of Equal Highs/Lows patterns.
        """
        eq_patterns = []

        # Find swing points
        swing_highs, swing_lows = self._find_swing_points(df)

        # Detect Equal Highs (EQH)
        if len(swing_highs) >= min_touches:
            # Group swing highs by proximity
            high_clusters = self._cluster_price_levels(
                [df['high'].iloc[idx] for idx in swing_highs],
                swing_highs,
                tolerance
            )

            for level, indices in high_clusters.items():
                if len(indices) >= min_touches:
                    # Check if level has been swept
                    swept, sweep_idx = self._check_level_swept(
                        df, level, indices, 'high'
                    )

                    # Calculate strength based on count and tightness
                    price_std = np.std([df['high'].iloc[idx] for idx in indices])
                    tightness_score = max(0, 100 - (price_std / level * 10000))
                    strength = min((len(indices) * 20) + tightness_score, 100)

                    eq_patterns.append(EqualHighsLows(
                        eq_type='equal_highs',
                        level=level,
                        indices=indices,
                        count=len(indices),
                        tolerance=tolerance,
                        swept=swept,
                        sweep_idx=sweep_idx,
                        strength=strength,
                    ))

        # Detect Equal Lows (EQL)
        if len(swing_lows) >= min_touches:
            # Group swing lows by proximity
            low_clusters = self._cluster_price_levels(
                [df['low'].iloc[idx] for idx in swing_lows],
                swing_lows,
                tolerance
            )

            for level, indices in low_clusters.items():
                if len(indices) >= min_touches:
                    # Check if level has been swept
                    swept, sweep_idx = self._check_level_swept(
                        df, level, indices, 'low'
                    )

                    # Calculate strength
                    price_std = np.std([df['low'].iloc[idx] for idx in indices])
                    tightness_score = max(0, 100 - (price_std / level * 10000))
                    strength = min((len(indices) * 20) + tightness_score, 100)

                    eq_patterns.append(EqualHighsLows(
                        eq_type='equal_lows',
                        level=level,
                        indices=indices,
                        count=len(indices),
                        tolerance=tolerance,
                        swept=swept,
                        sweep_idx=sweep_idx,
                        strength=strength,
                    ))

        return eq_patterns

    def detect_order_flow(
        self,
        df: pd.DataFrame,
    ) -> List[OrderFlow]:
        """
        Detect Order Flow (OF) - Last opposing move before directional change.

        Order Flow is more general than Order Blocks (no minimum move requirement).
        Represents any opposing candle before a trend change.

        Page 12 of handbook: "Order Block is refined form of Order Flow"

        Args:
            df: DataFrame with OHLC data.

        Returns:
            List of Order Flow zones.
        """
        order_flows = []

        for i in range(2, len(df) - 3):
            current = df.iloc[i]
            prev = df.iloc[i - 1]
            next1 = df.iloc[i + 1]
            next2 = df.iloc[i + 2]
            next3 = df.iloc[i + 3]

            # Bullish Order Flow: Last sell move before bullish momentum
            if (current['close'] < current['open'] and  # Current bearish
                next1['close'] > next1['open'] and  # Next bullish
                next2['close'] > next2['open']):  # Momentum continues

                # Calculate subsequent move strength
                move_strength = (next3['high'] - current['close']) / current['close'] * 100

                # Order flow zone is the current candle body
                zone_high = max(current['open'], current['close'])
                zone_low = min(current['open'], current['close'])

                # Check if still active
                active = self._check_zone_active(df, i, zone_low, zone_high, 'demand')

                order_flows.append(OrderFlow(
                    of_type='bullish_of',
                    candle_idx=i,
                    zone_high=zone_high,
                    zone_low=zone_low,
                    strength=move_strength,
                    active=active,
                    description=f'Bullish Order Flow at ${zone_low:.2f}-${zone_high:.2f}',
                ))

            # Bearish Order Flow: Last buy move before bearish momentum
            elif (current['close'] > current['open'] and  # Current bullish
                  next1['close'] < next1['open'] and  # Next bearish
                  next2['close'] < next2['open']):  # Momentum continues

                # Calculate subsequent move strength
                move_strength = (current['close'] - next3['low']) / current['close'] * 100

                # Order flow zone is the current candle body
                zone_high = max(current['open'], current['close'])
                zone_low = min(current['open'], current['close'])

                # Check if still active
                active = self._check_zone_active(df, i, zone_low, zone_high, 'supply')

                order_flows.append(OrderFlow(
                    of_type='bearish_of',
                    candle_idx=i,
                    zone_high=zone_high,
                    zone_low=zone_low,
                    strength=move_strength,
                    active=active,
                    description=f'Bearish Order Flow at ${zone_low:.2f}-${zone_high:.2f}',
                ))

        return order_flows

    def detect_institutional_funding_candles(
        self,
        df: pd.DataFrame,
        lookback: int = 20,
    ) -> List[InstitutionalFundingCandle]:
        """
        Detect Institutional Funding Candles (IFC).

        IFC: Candle that sweeps a major swing high/low with its wick but
        closes back inside the range. Shows institutions funded positions
        by hitting stops.

        Page 15 of handbook: "Price breaks but cannot close beyond level"

        Args:
            df: DataFrame with OHLC data.
            lookback: Bars to look back for swing levels.

        Returns:
            List of IFC patterns.
        """
        ifcs = []

        # Find swing points
        swing_highs, swing_lows = self._find_swing_points(df)

        for i in range(lookback, len(df) - 1):
            current = df.iloc[i]
            next_candle = df.iloc[i + 1]

            # Find recent swing high
            recent_highs = [df['high'].iloc[idx] for idx in swing_highs if i - lookback <= idx < i]
            if recent_highs:
                swing_high = max(recent_highs)

                # Bullish IFC: Wick breaks above swing high, closes back below
                if (current['high'] > swing_high and  # Wick sweeps high
                    current['close'] < swing_high):  # But closes below

                    # Calculate strength of sweep
                    wick_extension = (current['high'] - swing_high) / swing_high * 100
                    close_back = (swing_high - current['close']) / swing_high * 100

                    # Check reversal confirmation
                    reversal_confirmed = next_candle['close'] > current['close']

                    strength = min(wick_extension * 10 + close_back * 10, 100)

                    ifcs.append(InstitutionalFundingCandle(
                        ifc_type='bullish_ifc',
                        candle_idx=i,
                        swept_level=swing_high,
                        wick_extreme=current['high'],
                        close_price=current['close'],
                        strength=strength,
                        reversal_confirmed=reversal_confirmed,
                        description=f'Bullish IFC: Swept ${swing_high:.2f}, closed at ${current["close"]:.2f}',
                    ))

            # Find recent swing low
            recent_lows = [df['low'].iloc[idx] for idx in swing_lows if i - lookback <= idx < i]
            if recent_lows:
                swing_low = min(recent_lows)

                # Bearish IFC: Wick breaks below swing low, closes back above
                if (current['low'] < swing_low and  # Wick sweeps low
                    current['close'] > swing_low):  # But closes above

                    # Calculate strength of sweep
                    wick_extension = (swing_low - current['low']) / swing_low * 100
                    close_back = (current['close'] - swing_low) / swing_low * 100

                    # Check reversal confirmation
                    reversal_confirmed = next_candle['close'] < current['close']

                    strength = min(wick_extension * 10 + close_back * 10, 100)

                    ifcs.append(InstitutionalFundingCandle(
                        ifc_type='bearish_ifc',
                        candle_idx=i,
                        swept_level=swing_low,
                        wick_extreme=current['low'],
                        close_price=current['close'],
                        strength=strength,
                        reversal_confirmed=reversal_confirmed,
                        description=f'Bearish IFC: Swept ${swing_low:.2f}, closed at ${current["close"]:.2f}',
                    ))

        return ifcs

    def detect_false_break_of_structure(
        self,
        df: pd.DataFrame,
        lookback: int = 20,
        invalidation_candles: int = 5,
    ) -> List[dict]:
        """
        Detect False Break of Structure (FBOS).

        FBOS: Structure break that quickly fails and reverses.
        Traps retail traders who entered on the BOS.

        Args:
            df: DataFrame with OHLC data.
            lookback: Bars to look back for structure.
            invalidation_candles: Max candles for BOS to be invalidated.

        Returns:
            List of FBOS events.
        """
        fbos_list = []

        # First detect all BOS
        all_bos = self.detect_break_of_structure(df, lookback)

        for bos in all_bos:
            idx = bos.break_idx

            # Check if BOS gets invalidated within next N candles
            if idx + invalidation_candles >= len(df):
                continue

            if bos.is_bullish:
                # Bullish BOS invalidated if price breaks below previous level
                future_lows = df['low'].iloc[idx+1:idx+invalidation_candles+1]
                if (future_lows < bos.previous_level).any():
                    # Find where it was invalidated
                    invalid_idx = idx + 1 + (future_lows < bos.previous_level).idxmax()

                    fbos_list.append({
                        'fbos_type': 'false_bullish_bos',
                        'bos_idx': idx,
                        'invalidation_idx': int(invalid_idx),
                        'break_level': bos.break_price,
                        'previous_level': bos.previous_level,
                        'description': f'False Bullish BOS at ${bos.break_price:.2f}, invalidated at candle {invalid_idx}',
                        'trap_signal': 'bearish',  # False bullish BOS = bearish signal
                    })
            else:
                # Bearish BOS invalidated if price breaks above previous level
                future_highs = df['high'].iloc[idx+1:idx+invalidation_candles+1]
                if (future_highs > bos.previous_level).any():
                    invalid_idx = idx + 1 + (future_highs > bos.previous_level).idxmax()

                    fbos_list.append({
                        'fbos_type': 'false_bearish_bos',
                        'bos_idx': idx,
                        'invalidation_idx': int(invalid_idx),
                        'break_level': bos.break_price,
                        'previous_level': bos.previous_level,
                        'description': f'False Bearish BOS at ${bos.break_price:.2f}, invalidated at candle {invalid_idx}',
                        'trap_signal': 'bullish',  # False bearish BOS = bullish signal
                    })

        return fbos_list

    def detect_session_liquidity(
        self,
        df: pd.DataFrame,
    ) -> List[SessionLiquidity]:
        """
        Detect Session Liquidity (Asia/London/NY session highs/lows).

        Pages 19-20 of handbook: Session-based liquidity analysis.
        "At least one session per day will be manipulative"

        Sessions (UTC):
        - Asia: 00:00-09:00
        - London: 08:00-17:00
        - New York: 13:00-22:00

        Args:
            df: DataFrame with OHLC data and datetime index.

        Returns:
            List of session liquidity levels.
        """
        sessions = []

        # Ensure datetime index
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'timestamp' in df.columns:
                df = df.set_index('timestamp')
            else:
                logger.warning("Cannot detect session liquidity without datetime index")
                return sessions

        # Define session times (UTC)
        session_times = {
            'asia': (0, 9),
            'london': (8, 17),
            'new_york': (13, 22),
        }

        # Group by date
        for date, day_data in df.groupby(df.index.date):
            for session_name, (start_hour, end_hour) in session_times.items():
                # Filter session data
                session_data = day_data[
                    (day_data.index.hour >= start_hour) &
                    (day_data.index.hour < end_hour)
                ]

                if len(session_data) < 2:
                    continue

                session_high = session_data['high'].max()
                session_low = session_data['low'].min()

                # Check if highs/lows were swept after session
                future_data = df[df.index > session_data.index[-1]]

                if len(future_data) > 0:
                    high_swept = (future_data['high'] > session_high).any()
                    low_swept = (future_data['low'] < session_low).any()

                    high_sweep_idx = None
                    low_sweep_idx = None

                    if high_swept:
                        high_sweep_idx = future_data[future_data['high'] > session_high].index[0]
                    if low_swept:
                        low_sweep_idx = future_data[future_data['low'] < session_low].index[0]
                else:
                    high_swept = False
                    low_swept = False
                    high_sweep_idx = None
                    low_sweep_idx = None

                sessions.append(SessionLiquidity(
                    session_name=session_name,
                    session_date=str(date),
                    session_high=session_high,
                    session_low=session_low,
                    high_swept=high_swept,
                    low_swept=low_swept,
                    high_sweep_idx=high_sweep_idx,
                    low_sweep_idx=low_sweep_idx,
                ))

        return sessions

    def detect_daily_liquidity(
        self,
        df: pd.DataFrame,
    ) -> Dict[str, float]:
        """
        Detect Daily Candle Liquidity (PDH/PDL, PWH/PWL).

        Page 21 of handbook: Previous Day/Week High/Low as major levels.

        Returns:
            Dictionary with liquidity levels:
            - pdh: Previous Day High
            - pdl: Previous Day Low
            - pwh: Previous Week High
            - pwl: Previous Week Low
        """
        liquidity_levels = {}

        # Ensure datetime index
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'timestamp' in df.columns:
                df = df.set_index('timestamp')
            else:
                logger.warning("Cannot detect daily liquidity without datetime index")
                return liquidity_levels

        # Get current date
        if len(df) == 0:
            return liquidity_levels

        current_date = df.index[-1].date()

        # Previous Day High/Low
        yesterday_data = df[df.index.date < current_date]
        if len(yesterday_data) > 0:
            last_day_data = yesterday_data[yesterday_data.index.date == yesterday_data.index[-1].date()]
            if len(last_day_data) > 0:
                liquidity_levels['pdh'] = float(last_day_data['high'].max())
                liquidity_levels['pdl'] = float(last_day_data['low'].min())

        # Previous Week High/Low
        current_week = df.index[-1].isocalendar()[1]
        current_year = df.index[-1].year
        prev_week_data = df[
            (df.index.map(lambda x: x.isocalendar()[1]) == current_week - 1) &
            (df.index.year == current_year)
        ]
        if len(prev_week_data) > 0:
            liquidity_levels['pwh'] = float(prev_week_data['high'].max())
            liquidity_levels['pwl'] = float(prev_week_data['low'].min())

        return liquidity_levels

    def detect_smart_money_trap(
        self,
        df: pd.DataFrame,
        lookback: int = 20,
    ) -> List[dict]:
        """
        Detect Smart Money Trap (SMT) - First pullback manipulation.

        SMT: After major trend move, first pullback traps retail traders
        entering "with the trend" before reversal.

        Args:
            df: DataFrame with OHLC data.
            lookback: Bars to look back for trend.

        Returns:
            List of SMT events.
        """
        smt_list = []

        # Detect BOS first (major trend moves)
        all_bos = self.detect_break_of_structure(df, lookback)

        for bos in all_bos:
            idx = bos.break_idx

            if idx + 10 >= len(df):
                continue

            # After BOS, look for first pullback that reverses
            if bos.is_bullish:
                # After bullish BOS, look for pullback down (trap)
                future_data = df.iloc[idx+1:idx+10]

                # Find first pullback (lower low than BOS candle)
                pullbacks = future_data[future_data['low'] < df['low'].iloc[idx]]
                if len(pullbacks) > 0:
                    pullback_idx = pullbacks.index[0]
                    pullback_low = pullbacks.iloc[0]['low']

                    # Check if pullback reverses (SMT confirmed)
                    after_pullback = df.iloc[pullback_idx+1:pullback_idx+5]
                    if len(after_pullback) > 0 and (after_pullback['close'] < pullback_low).any():
                        smt_list.append({
                            'smt_type': 'bearish_smt',
                            'bos_idx': idx,
                            'pullback_idx': int(pullback_idx),
                            'trap_level': pullback_low,
                            'description': f'Bearish SMT: Bullish BOS at {idx}, trapped at ${pullback_low:.2f}',
                            'signal': 'bearish',
                        })

            else:
                # After bearish BOS, look for pullback up (trap)
                future_data = df.iloc[idx+1:idx+10]

                # Find first pullback (higher high than BOS candle)
                pullbacks = future_data[future_data['high'] > df['high'].iloc[idx]]
                if len(pullbacks) > 0:
                    pullback_idx = pullbacks.index[0]
                    pullback_high = pullbacks.iloc[0]['high']

                    # Check if pullback reverses (SMT confirmed)
                    after_pullback = df.iloc[pullback_idx+1:pullback_idx+5]
                    if len(after_pullback) > 0 and (after_pullback['close'] > pullback_high).any():
                        smt_list.append({
                            'smt_type': 'bullish_smt',
                            'bos_idx': idx,
                            'pullback_idx': int(pullback_idx),
                            'trap_level': pullback_high,
                            'description': f'Bullish SMT: Bearish BOS at {idx}, trapped at ${pullback_high:.2f}',
                            'signal': 'bullish',
                        })

        return smt_list

    def detect_inducement(
        self,
        df: pd.DataFrame,
        min_move: float = 0.005,  # 0.5% minimum move
    ) -> List[dict]:
        """
        Detect Inducement (IDM) - Small moves that trap retail before reversal.

        IDM: Minor structure breaks that induce retail entries before
        price reverses against them.

        Args:
            df: DataFrame with OHLC data.
            min_move: Minimum % move to qualify as inducement.

        Returns:
            List of inducement events.
        """
        inducements = []

        for i in range(10, len(df) - 5):
            current_close = df['close'].iloc[i]
            prev_close = df['close'].iloc[i - 1]

            # Calculate move percentage
            move_pct = abs(current_close - prev_close) / prev_close

            # Small directional move (inducement)
            if min_move <= move_pct < 0.015:  # Between 0.5% and 1.5%
                # Check for quick reversal in next 3-5 candles
                future_data = df.iloc[i+1:i+5]

                if len(future_data) > 0:
                    if current_close > prev_close:
                        # Bullish inducement - check for bearish reversal
                        if (future_data['close'] < prev_close).any():
                            reversal_idx = i + 1 + (future_data['close'] < prev_close).idxmax()
                            inducements.append({
                                'idm_type': 'bearish_idm',
                                'inducement_idx': i,
                                'reversal_idx': int(reversal_idx),
                                'inducement_price': current_close,
                                'move_percentage': move_pct * 100,
                                'description': f'Bearish IDM: Small bullish move to ${current_close:.2f} trapped traders',
                                'signal': 'bearish',
                            })

                    else:
                        # Bearish inducement - check for bullish reversal
                        if (future_data['close'] > prev_close).any():
                            reversal_idx = i + 1 + (future_data['close'] > prev_close).idxmax()
                            inducements.append({
                                'idm_type': 'bullish_idm',
                                'inducement_idx': i,
                                'reversal_idx': int(reversal_idx),
                                'inducement_price': current_close,
                                'move_percentage': move_pct * 100,
                                'description': f'Bullish IDM: Small bearish move to ${current_close:.2f} trapped traders',
                                'signal': 'bullish',
                            })

        return inducements

    def _cluster_price_levels(
        self,
        prices: List[float],
        indices: List[int],
        tolerance: float,
    ) -> Dict[float, List[int]]:
        """
        Cluster price levels within tolerance.

        Used for detecting Equal Highs/Lows.

        Args:
            prices: List of prices to cluster.
            indices: Corresponding indices.
            tolerance: Percentage tolerance for clustering.

        Returns:
            Dictionary mapping cluster center to list of indices.
        """
        if len(prices) == 0:
            return {}

        # Sort by price
        sorted_pairs = sorted(zip(prices, indices))
        clusters = {}

        for price, idx in sorted_pairs:
            # Find if price belongs to existing cluster
            added = False
            for cluster_center in list(clusters.keys()):
                if abs(price - cluster_center) / cluster_center <= tolerance:
                    clusters[cluster_center].append(idx)
                    added = True
                    break

            if not added:
                # Create new cluster
                clusters[price] = [idx]

        return clusters

    def _check_level_swept(
        self,
        df: pd.DataFrame,
        level: float,
        level_indices: List[int],
        level_type: str,
    ) -> Tuple[bool, Optional[int]]:
        """
        Check if a price level (EQH/EQL) has been swept.

        Args:
            df: DataFrame with OHLC data.
            level: Price level to check.
            level_indices: Indices where level occurred.
            level_type: 'high' or 'low'.

        Returns:
            Tuple of (swept: bool, sweep_idx: Optional[int]).
        """
        last_level_idx = max(level_indices)

        if last_level_idx >= len(df) - 1:
            return False, None

        future_data = df.iloc[last_level_idx + 1:]

        if level_type == 'high':
            # Check if high was swept (price went above)
            swept_candles = future_data[future_data['high'] > level]
            if len(swept_candles) > 0:
                return True, swept_candles.index[0]
        else:
            # Check if low was swept (price went below)
            swept_candles = future_data[future_data['low'] < level]
            if len(swept_candles) > 0:
                return True, swept_candles.index[0]

        return False, None
