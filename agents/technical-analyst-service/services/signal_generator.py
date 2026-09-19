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
from ..patterns.elliott_wave import ElliottWaveDetector
from ..patterns.divergence import RSIDivergenceDetector
from ..patterns.smart_money import SmartMoneyConceptsDetector
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
        self.elliott_wave_detector = ElliottWaveDetector()
        self.divergence_detector = RSIDivergenceDetector()
        self.smc_detector = SmartMoneyConceptsDetector()

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

            # Detect candlestick and chart patterns
            patterns = self.pattern_detector.scan_patterns(df, symbol, timeframe)

            # Detect Elliott Wave patterns (all types)
            elliott_wave_bullish = self.elliott_wave_detector.detect_impulse_wave(df, is_bullish=True)
            elliott_wave_bearish = self.elliott_wave_detector.detect_impulse_wave(df, is_bullish=False)

            # Detect Leading Diagonal (Wave 1 or A)
            leading_diagonal_bullish = self.elliott_wave_detector.detect_leading_diagonal(df, is_bullish=True)
            leading_diagonal_bearish = self.elliott_wave_detector.detect_leading_diagonal(df, is_bullish=False)

            # Detect Ending Diagonal (Wave 5 or C) - high-value reversal signal
            ending_diagonal_bullish = self.elliott_wave_detector.detect_ending_diagonal(df, is_bullish=True)
            ending_diagonal_bearish = self.elliott_wave_detector.detect_ending_diagonal(df, is_bullish=False)

            # Detect Corrections (Zig-Zag, Flat, Triangle)
            zigzag_correction = self.elliott_wave_detector.detect_zigzag_correction(df, is_bullish=False)
            flat_correction = self.elliott_wave_detector.detect_flat_correction(df, is_bullish=False)
            triangle_pattern = self.elliott_wave_detector.detect_triangle_pattern(df, is_bullish=False)

            # Detect RSI divergences
            rsi_series = self.indicator_calc.calculate_rsi(df['close'], settings.RSI_PERIOD)
            divergences = self.divergence_detector.detect_all_divergences(df, rsi_series)

            # Detect Smart Money Concepts (All 14 Patterns)

            # Core 6 patterns
            structure_breaks = self.smc_detector.detect_break_of_structure(df)
            fvgs = self.smc_detector.detect_fair_value_gaps(df)
            supply_demand_zones = self.smc_detector.detect_supply_demand_zones(df)
            order_blocks = self.smc_detector.detect_order_blocks(df)
            liquidity_sweeps = self.smc_detector.detect_liquidity_sweeps(df)

            # New 8 patterns
            equal_highs_lows = self.smc_detector.detect_equal_highs_lows(df)
            order_flow = self.smc_detector.detect_order_flow(df)
            institutional_funding_candles = self.smc_detector.detect_institutional_funding_candles(df)
            false_bos = self.smc_detector.detect_false_break_of_structure(df)
            session_liquidity = self.smc_detector.detect_session_liquidity(df)
            daily_liquidity = self.smc_detector.detect_daily_liquidity(df)
            smart_money_traps = self.smc_detector.detect_smart_money_trap(df)
            inducements = self.smc_detector.detect_inducement(df)

            # Generate signal from all analysis
            signal = self._combine_signals(
                symbol, timeframe, df, indicators, patterns,
                elliott_wave_bullish, elliott_wave_bearish,
                leading_diagonal_bullish, leading_diagonal_bearish,
                ending_diagonal_bullish, ending_diagonal_bearish,
                zigzag_correction, flat_correction, triangle_pattern,
                divergences, structure_breaks, fvgs, supply_demand_zones,
                order_blocks, liquidity_sweeps,
                equal_highs_lows, order_flow, institutional_funding_candles,
                false_bos, session_liquidity, daily_liquidity,
                smart_money_traps, inducements
            )

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
        elliott_wave_bullish,
        elliott_wave_bearish,
        leading_diagonal_bullish,
        leading_diagonal_bearish,
        ending_diagonal_bullish,
        ending_diagonal_bearish,
        zigzag_correction,
        flat_correction,
        triangle_pattern,
        divergences: list,
        structure_breaks: list,
        fvgs: list,
        supply_demand_zones: list,
        order_blocks: list,
        liquidity_sweeps: list,
        equal_highs_lows: list,
        order_flow: list,
        institutional_funding_candles: list,
        false_bos: list,
        session_liquidity: list,
        daily_liquidity: dict,
        smart_money_traps: list,
        inducements: list,
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

        # Candlestick & Chart pattern signals
        for pattern in patterns:
            if pattern.signal == PatternSignal.BULLISH:
                bullish_score += pattern.confidence * 0.3  # 30% weight
                reasons.append(f"{pattern.pattern_type.value} pattern (bullish)")
            elif pattern.signal == PatternSignal.BEARISH:
                bearish_score += pattern.confidence * 0.3
                reasons.append(f"{pattern.pattern_type.value} pattern (bearish)")

        # Elliott Wave Impulse signals (HIGHEST PRIORITY - 25 points)
        if elliott_wave_bullish and elliott_wave_bullish.confidence > 70:
            wave_num = elliott_wave_bullish.current_wave
            score_add = 30 if elliott_wave_bullish.extended_wave == 3 else 25
            bullish_score += score_add
            ext_info = f", Wave {elliott_wave_bullish.extended_wave} extended" if elliott_wave_bullish.extended_wave else ""
            trunc_info = " (truncated)" if elliott_wave_bullish.is_truncated else ""
            reasons.append(f"Elliott Wave bullish impulse (Wave {wave_num}{ext_info}{trunc_info}, {elliott_wave_bullish.confidence:.0f}% confidence)")

        if elliott_wave_bearish and elliott_wave_bearish.confidence > 70:
            wave_num = elliott_wave_bearish.current_wave
            score_add = 30 if elliott_wave_bearish.extended_wave == 3 else 25
            bearish_score += score_add
            ext_info = f", Wave {elliott_wave_bearish.extended_wave} extended" if elliott_wave_bearish.extended_wave else ""
            trunc_info = " (truncated)" if elliott_wave_bearish.is_truncated else ""
            reasons.append(f"Elliott Wave bearish impulse (Wave {wave_num}{ext_info}{trunc_info}, {elliott_wave_bearish.confidence:.0f}% confidence)")

        # Leading Diagonal signals (HIGH PRIORITY - 20 points) - Trend start
        if leading_diagonal_bullish and leading_diagonal_bullish.confidence > 60:
            bullish_score += 20
            reasons.append(f"Leading Diagonal bullish (Wave {leading_diagonal_bullish.current_wave}, {leading_diagonal_bullish.confidence:.0f}% confidence)")

        if leading_diagonal_bearish and leading_diagonal_bearish.confidence > 60:
            bearish_score += 20
            reasons.append(f"Leading Diagonal bearish (Wave {leading_diagonal_bearish.current_wave}, {leading_diagonal_bearish.confidence:.0f}% confidence)")

        # Ending Diagonal signals (VERY HIGH PRIORITY - 30 points) - Trend exhaustion/reversal
        if ending_diagonal_bullish and ending_diagonal_bullish.confidence > 60:
            bearish_score += 30  # Ending diagonal bullish = trend exhaustion, expect reversal down
            reasons.append(f"Ending Diagonal exhaustion (bullish trend ending, {ending_diagonal_bullish.confidence:.0f}% confidence)")

        if ending_diagonal_bearish and ending_diagonal_bearish.confidence > 60:
            bullish_score += 30  # Ending diagonal bearish = trend exhaustion, expect reversal up
            reasons.append(f"Ending Diagonal exhaustion (bearish trend ending, {ending_diagonal_bearish.confidence:.0f}% confidence)")

        # Correction patterns (MEDIUM PRIORITY - 10-15 points) - Helps identify pullbacks
        if zigzag_correction and zigzag_correction.confidence > 50:
            # Zig-zag suggests sharp correction, look for continuation after
            if zigzag_correction.direction == 'bullish':
                bullish_score += 12
                reasons.append(f"Zig-Zag correction (bullish, Wave {chr(65 + zigzag_correction.current_wave)})")
            else:
                bearish_score += 12
                reasons.append(f"Zig-Zag correction (bearish, Wave {chr(65 + zigzag_correction.current_wave)})")

        if flat_correction and flat_correction.confidence > 50:
            # Flat suggests sideways consolidation
            score_add = 15 if flat_correction.subtype == 'expanded_flat' else 10
            if flat_correction.direction == 'bullish':
                bullish_score += score_add
                reasons.append(f"Flat correction ({flat_correction.subtype}, Wave {chr(65 + flat_correction.current_wave)})")
            else:
                bearish_score += score_add
                reasons.append(f"Flat correction ({flat_correction.subtype}, Wave {chr(65 + flat_correction.current_wave)})")

        if triangle_pattern and triangle_pattern.confidence > 50:
            # Triangle suggests continuation after Wave E completes
            score_add = 15 if triangle_pattern.current_wave >= 4 else 10
            if triangle_pattern.direction == 'bullish':
                bullish_score += score_add
                reasons.append(f"Triangle pattern ({triangle_pattern.subtype}, Wave {chr(65 + triangle_pattern.current_wave)})")
            else:
                bearish_score += score_add
                reasons.append(f"Triangle pattern ({triangle_pattern.subtype}, Wave {chr(65 + triangle_pattern.current_wave)})")

        # RSI Divergence signals (VERY HIGH PRIORITY - 20-30 points)
        if divergences:
            latest_div = divergences[0]  # Most recent divergence
            if latest_div.is_bullish:
                score_add = 30 if latest_div.confirmed else 20
                bullish_score += score_add
                reasons.append(f"{latest_div.divergence_type.value} ({'confirmed' if latest_div.confirmed else 'unconfirmed'})")
            else:
                score_add = 30 if latest_div.confirmed else 20
                bearish_score += score_add
                reasons.append(f"{latest_div.divergence_type.value} ({'confirmed' if latest_div.confirmed else 'unconfirmed'})")

        # Smart Money Concepts - Break of Structure (HIGH PRIORITY - 15 points)
        if structure_breaks:
            latest_bos = structure_breaks[-1]  # Most recent
            if latest_bos.is_bullish:
                score_add = 20 if latest_bos.volume_confirmation else 15
                bullish_score += score_add
                reasons.append(f"{latest_bos.structure_type.value} ({latest_bos.strength:.1f}% break)")
            else:
                score_add = 20 if latest_bos.volume_confirmation else 15
                bearish_score += score_add
                reasons.append(f"{latest_bos.structure_type.value} ({latest_bos.strength:.1f}% break)")

        # Fair Value Gaps (MEDIUM PRIORITY - 10 points)
        unfilled_fvgs = [fvg for fvg in fvgs if not fvg.filled]
        if unfilled_fvgs:
            latest_fvg = unfilled_fvgs[-1]
            if latest_fvg.direction == 'bullish':
                bullish_score += 10
                reasons.append(f"Bullish FVG unfilled (${latest_fvg.gap_low:.2f}-${latest_fvg.gap_high:.2f})")
            else:
                bearish_score += 10
                reasons.append(f"Bearish FVG unfilled (${latest_fvg.gap_low:.2f}-${latest_fvg.gap_high:.2f})")

        # Supply/Demand Zones (MEDIUM PRIORITY - 10 points)
        active_zones = [zone for zone in supply_demand_zones if zone.active and zone.touches >= 2]
        if active_zones:
            # Check if current price is near any strong zone
            current_price = df['close'].iloc[-1]
            for zone in active_zones:
                if zone.zone_low <= current_price <= zone.zone_high:
                    if zone.is_supply:
                        bearish_score += 15
                        reasons.append(f"At Supply Zone (${zone.zone_low:.2f}-${zone.zone_high:.2f}, {zone.touches} touches)")
                    else:
                        bullish_score += 15
                        reasons.append(f"At Demand Zone (${zone.zone_low:.2f}-${zone.zone_high:.2f}, {zone.touches} touches)")

        # Order Blocks (HIGH PRIORITY - 15-20 points) - Institutional entry zones
        if order_blocks:
            current_price = df['close'].iloc[-1]
            for ob in order_blocks:
                # Check if price is at or near order block (within zone)
                if ob.zone_low <= current_price <= ob.zone_high:
                    score_add = 20 if ob.strength > 0.7 else 15
                    if not ob.is_supply:  # Bullish order block (demand)
                        bullish_score += score_add
                        reasons.append(f"At Bullish Order Block (${ob.zone_low:.2f}-${ob.zone_high:.2f}, {ob.strength:.0%} strength)")
                    else:  # Bearish order block (supply)
                        bearish_score += score_add
                        reasons.append(f"At Bearish Order Block (${ob.zone_low:.2f}-${ob.zone_high:.2f}, {ob.strength:.0%} strength)")

        # Liquidity Sweeps (VERY HIGH PRIORITY - 20-25 points) - Stop hunts before reversal
        if liquidity_sweeps:
            latest_sweep = liquidity_sweeps[-1]  # Most recent sweep
            # Check if sweep is recent (within last 5 candles)
            current_idx = len(df) - 1
            if current_idx - latest_sweep['idx'] <= 5:
                if latest_sweep['type'] == 'bullish_sweep':
                    bullish_score += 25
                    reasons.append(f"Recent Bullish Liquidity Sweep above ${latest_sweep['sweep_level']:.2f}")
                else:  # bearish_sweep
                    bearish_score += 25
                    reasons.append(f"Recent Bearish Liquidity Sweep below ${latest_sweep['sweep_level']:.2f}")

        # Equal Highs/Lows (CRITICAL - 30-40 points) - Major liquidity pools
        if equal_highs_lows:
            current_price = df['close'].iloc[-1]
            for eq in equal_highs_lows:
                # High value if price is at level or if level was recently swept
                tolerance_range = eq.level * 0.005  # 0.5% range
                at_level = abs(current_price - eq.level) <= tolerance_range

                if eq.swept and eq.sweep_idx is not None:
                    # Check if sweep is recent
                    if len(df) - int(eq.sweep_idx) <= 5:
                        score_add = 40  # Very high confidence on sweep
                        if eq.is_equal_highs:
                            bullish_score += score_add
                            reasons.append(f"Equal Highs ${eq.level:.2f} swept (bearish reversal signal)")
                        else:  # equal_lows
                            bearish_score += score_add
                            reasons.append(f"Equal Lows ${eq.level:.2f} swept (bullish reversal signal)")
                elif at_level:
                    # Price approaching un-swept EQH/EQL
                    score_add = 30
                    if eq.is_equal_highs:
                        bearish_score += score_add  # EQH acts as resistance
                        reasons.append(f"At Equal Highs ${eq.level:.2f} ({eq.count} touches)")
                    else:
                        bullish_score += score_add  # EQL acts as support
                        reasons.append(f"At Equal Lows ${eq.level:.2f} ({eq.count} touches)")

        # Order Flow (HIGH PRIORITY - 15-20 points) - General institutional zones
        if order_flow:
            current_price = df['close'].iloc[-1]
            for of in order_flow:
                if of.active and of.zone_low <= current_price <= of.zone_high:
                    score_add = 20 if of.strength > 10 else 15  # Based on subsequent move strength
                    if of.is_bullish:
                        bullish_score += score_add
                        reasons.append(f"At Bullish Order Flow zone (${of.zone_low:.2f}-${of.zone_high:.2f})")
                    else:
                        bearish_score += score_add
                        reasons.append(f"At Bearish Order Flow zone (${of.zone_low:.2f}-${of.zone_high:.2f})")

        # Institutional Funding Candles (VERY HIGH - 25-30 points) - Reversal candles
        if institutional_funding_candles:
            current_idx = len(df) - 1
            for ifc in institutional_funding_candles:
                # IFC is very high value if recent
                if current_idx - ifc.candle_idx <= 3:
                    score_add = 30 if ifc.reversal_confirmed else 25
                    if ifc.is_bullish:
                        bullish_score += score_add
                        reasons.append(f"Bullish IFC: Swept ${ifc.swept_level:.2f}, reversal confirmed")
                    else:
                        bearish_score += score_add
                        reasons.append(f"Bearish IFC: Swept ${ifc.swept_level:.2f}, reversal confirmed")

        # False Break of Structure (HIGH - 25 points) - False signal filter / reversal
        if false_bos:
            current_idx = len(df) - 1
            for fbos in false_bos:
                # FBOS is high value if recent
                if current_idx - fbos['invalidation_idx'] <= 5:
                    if fbos['trap_signal'] == 'bullish':
                        bullish_score += 25
                        reasons.append(f"False Bearish BOS invalidated (bullish trap reversal)")
                    else:  # bearish
                        bearish_score += 25
                        reasons.append(f"False Bullish BOS invalidated (bearish trap reversal)")

        # Session Liquidity (HIGH - 25 points for intraday) - Asia/London/NY levels
        if session_liquidity:
            current_price = df['close'].iloc[-1]
            # Check most recent session liquidity
            for session in session_liquidity[-3:]:  # Last 3 sessions
                tolerance = session.session_high * 0.002  # 0.2% tolerance

                # High swept (bearish signal)
                if session.high_swept and session.high_sweep_idx:
                    sweep_recent = len(df) - int(session.high_sweep_idx) <= 5
                    if sweep_recent:
                        bullish_score += 25
                        reasons.append(f"{session.session_name.title()} session high ${session.session_high:.2f} swept")

                # Low swept (bullish signal)
                if session.low_swept and session.low_sweep_idx:
                    sweep_recent = len(df) - int(session.low_sweep_idx) <= 5
                    if sweep_recent:
                        bearish_score += 25
                        reasons.append(f"{session.session_name.title()} session low ${session.session_low:.2f} swept")

                # At session levels (not swept)
                if not session.high_swept and abs(current_price - session.session_high) <= tolerance:
                    bearish_score += 20
                    reasons.append(f"At {session.session_name.title()} session high ${session.session_high:.2f}")

                if not session.low_swept and abs(current_price - session.session_low) <= tolerance:
                    bullish_score += 20
                    reasons.append(f"At {session.session_name.title()} session low ${session.session_low:.2f}")

        # Daily Liquidity (HIGH - 20-30 points for swing) - PDH/PDL, PWH/PWL
        if daily_liquidity:
            current_price = df['close'].iloc[-1]
            tolerance = current_price * 0.003  # 0.3% tolerance

            # PDH (Previous Day High) - resistance
            if 'pdh' in daily_liquidity:
                pdh = daily_liquidity['pdh']
                if abs(current_price - pdh) <= tolerance:
                    bearish_score += 20
                    reasons.append(f"At Previous Day High ${pdh:.2f}")

            # PDL (Previous Day Low) - support
            if 'pdl' in daily_liquidity:
                pdl = daily_liquidity['pdl']
                if abs(current_price - pdl) <= tolerance:
                    bullish_score += 20
                    reasons.append(f"At Previous Day Low ${pdl:.2f}")

            # PWH (Previous Week High) - stronger resistance
            if 'pwh' in daily_liquidity:
                pwh = daily_liquidity['pwh']
                if abs(current_price - pwh) <= tolerance:
                    bearish_score += 30
                    reasons.append(f"At Previous Week High ${pwh:.2f}")

            # PWL (Previous Week Low) - stronger support
            if 'pwl' in daily_liquidity:
                pwl = daily_liquidity['pwl']
                if abs(current_price - pwl) <= tolerance:
                    bullish_score += 30
                    reasons.append(f"At Previous Week Low ${pwl:.2f}")

        # Smart Money Trap (HIGH - 20-25 points) - First pullback traps
        if smart_money_traps:
            current_idx = len(df) - 1
            for smt in smart_money_traps:
                # SMT is valuable if recent
                if current_idx - smt['pullback_idx'] <= 5:
                    if smt['signal'] == 'bullish':
                        bullish_score += 25
                        reasons.append(f"Bullish SMT: Bearish BOS trapped at ${smt['trap_level']:.2f}")
                    else:
                        bearish_score += 25
                        reasons.append(f"Bearish SMT: Bullish BOS trapped at ${smt['trap_level']:.2f}")

        # Inducement (MEDIUM-HIGH - 15-20 points) - Retail traps
        if inducements:
            current_idx = len(df) - 1
            for idm in inducements:
                # Inducement valuable if recent
                if current_idx - idm['reversal_idx'] <= 5:
                    if idm['signal'] == 'bullish':
                        bullish_score += 20
                        reasons.append(f"Bullish Inducement: Small bearish move trapped traders")
                    else:
                        bearish_score += 20
                        reasons.append(f"Bearish Inducement: Small bullish move trapped traders")

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
