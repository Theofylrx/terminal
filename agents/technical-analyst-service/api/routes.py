"""Technical Analyst Service API routes."""

import logging
from datetime import datetime, timedelta
from typing import List
import pandas as pd

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

# Add shared to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.database.connection import get_db_session
from shared.database.models import OHLCV, Signal, User, TradingDecision
from shared.database.models.signal import SignalStatus
from shared.utils.dependencies import get_current_user

from .schemas import (
    GenerateSignalRequest,
    SignalResponse,
    HealthResponse,
    IndicatorResponse,
    ElliottWaveResponse,
    WaveResponse,
    FibonacciLevelResponse,
    DivergencesResponse,
    DivergenceResponse,
    SmartMoneyResponse,
    BreakOfStructureResponse,
    FairValueGapResponse,
    SupplyDemandZoneResponse,
    LiquiditySweepResponse,
    EqualHighsLowsResponse,
    OrderFlowResponse,
    InstitutionalFundingCandleResponse,
    FalseBreakOfStructureResponse,
    SessionLiquidityResponse,
    DailyLiquidityResponse,
    SmartMoneyTrapResponse,
    InducementResponse,
    TradingDecisionResponse,
    ArgumentResponse,
    EvidenceResponse,
    ConfluenceAnalysisResponse,
    FundamentalAlignmentResponse,
    RiskAssessmentResponse,
    EntryPlanResponse,
    TargetResponse,
)
from ..services.signal_generator import SignalGenerator
from ..services.multi_timeframe_analyzer import MultiTimeframeAnalyzer
from ..services.reasoning_engine import ReasoningEngine
from ..services.evidence_collector import EvidenceCollector
from ..services.fundamental_analyzer import FundamentalAnalyzer
from ..services.decision_framework import DecisionFramework


logger = logging.getLogger(__name__)

router = APIRouter()

# Global service instances
signal_generator = SignalGenerator()
mtf_analyzer = MultiTimeframeAnalyzer()  # No arguments needed
reasoning_engine = ReasoningEngine()
evidence_collector = EvidenceCollector()
fundamental_analyzer = FundamentalAnalyzer()
decision_framework = DecisionFramework()


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["health"],
    summary="Health check",
    description="Check if the Technical Analyst Service is running and healthy"
)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
    )


@router.post(
    "/signals/generate",
    response_model=SignalResponse,
    tags=["signals"],
    summary="Generate trading signal",
    description="""
    Generate a high-confidence trading signal for the specified symbol and timeframe.

    Analyzes recent price data using:
    - 15 technical indicators (RSI, MACD, Bollinger Bands, EMAs, etc.)
    - 10+ candlestick and chart patterns
    - Elliott Wave patterns with Fibonacci levels
    - RSI divergences with Break of Structure confirmation
    - Smart Money Concepts (BOS, FVG, Supply/Demand zones)

    Returns a signal with entry price, target, stop loss, and detailed reasoning.
    """
)
async def generate_signal(
    request: GenerateSignalRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Generate trading signal for symbol.

    Analyzes recent price data and generates a trading signal
    based on technical indicators and patterns.

    **Authentication Required**: This endpoint requires a valid JWT token.
    """
    try:
        # Fetch recent OHLCV data
        lookback = datetime.utcnow() - timedelta(days=7)
        query = select(OHLCV).where(
            and_(
                OHLCV.symbol == request.symbol,
                OHLCV.timeframe == request.timeframe,
                OHLCV.timestamp >= lookback,
            )
        ).order_by(OHLCV.timestamp.asc())

        result = await session.execute(query)
        bars = result.scalars().all()

        if len(bars) < 50:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data for {request.symbol}. Need at least 50 bars."
            )

        # Convert to DataFrame
        df = pd.DataFrame([
            {
                'open': bar.open,
                'high': bar.high,
                'low': bar.low,
                'close': bar.close,
                'volume': bar.volume,
                'timestamp': bar.timestamp,
            }
            for bar in bars
        ])

        # Generate signal
        signal = await signal_generator.generate_signal(
            request.symbol,
            request.timeframe,
            df,
        )

        if not signal:
            raise HTTPException(
                status_code=404,
                detail=f"No signal generated for {request.symbol}. Conditions not met."
            )

        # Set user_id for multi-tenant isolation
        signal.user_id = str(current_user.id)

        # Save signal to database
        session.add(signal)
        await session.commit()
        await session.refresh(signal)

        return SignalResponse(**signal.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating signal: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate signal")


@router.get(
    "/signals",
    response_model=List[SignalResponse],
    tags=["signals"],
    summary="Get trading signals",
    description="Retrieve trading signals with optional filtering by symbol, status, and limit"
)
async def get_signals(
    symbol: str = Query(None, description="Filter by trading symbol (e.g., AAPL, BTCUSD)"),
    status: str = Query(None, description="Filter by signal status (ACTIVE, TRIGGERED, EXPIRED, CANCELLED)"),
    limit: int = Query(100, le=500, description="Maximum number of signals to return (max 500)"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get trading signals with optional filters.

    **Authentication Required**: Returns only signals belonging to the authenticated user.
    """
    try:
        # CRITICAL: Filter by user_id for multi-tenant isolation
        query = select(Signal).where(
            Signal.user_id == str(current_user.id)
        ).order_by(Signal.generated_at.desc())

        if symbol:
            query = query.where(Signal.symbol == symbol)

        if status:
            query = query.where(Signal.status == status)

        query = query.limit(limit)

        result = await session.execute(query)
        signals = result.scalars().all()

        return [SignalResponse(**sig.to_dict()) for sig in signals]

    except Exception as e:
        logger.error(f"Error fetching signals: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch signals")


@router.get(
    "/signals/{signal_id}",
    response_model=SignalResponse,
    tags=["signals"],
    summary="Get signal by ID",
    description="Retrieve a specific trading signal by its unique ID"
)
async def get_signal(
    signal_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get specific signal by ID.

    **Authentication Required**: Only returns signal if it belongs to the authenticated user.
    """
    try:
        # CRITICAL: Filter by both signal_id AND user_id for security
        query = select(Signal).where(
            Signal.id == signal_id,
            Signal.user_id == str(current_user.id)
        )
        result = await session.execute(query)
        signal = result.scalar_one_or_none()

        if not signal:
            raise HTTPException(status_code=404, detail="Signal not found")

        return SignalResponse(**signal.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching signal: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch signal")


@router.get(
    "/indicators/{symbol}",
    response_model=IndicatorResponse,
    tags=["indicators"],
    summary="Get technical indicators",
    description="""
    Calculate and return current technical indicator values for the specified symbol.

    Returns all 15 indicators including:
    - RSI (Relative Strength Index)
    - MACD (Moving Average Convergence Divergence)
    - Bollinger Bands (upper, middle, lower, %B)
    - Moving Averages (EMA 9, EMA 21, SMA 50)
    - ATR (Average True Range)

    Does not generate a trading signal.
    """
)
async def get_indicators(
    symbol: str,
    timeframe: str = Query("1h", description="Timeframe for analysis (1m, 5m, 15m, 1h, 4h, 1D)"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get current technical indicators for symbol.

    Returns calculated indicator values without generating a signal.

    **Authentication Required**: This endpoint requires a valid JWT token.
    """
    try:
        # Fetch recent data
        lookback = datetime.utcnow() - timedelta(days=7)
        query = select(OHLCV).where(
            and_(
                OHLCV.symbol == symbol,
                OHLCV.timeframe == timeframe,
                OHLCV.timestamp >= lookback,
            )
        ).order_by(OHLCV.timestamp.asc())

        result = await session.execute(query)
        bars = result.scalars().all()

        if len(bars) < 50:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data for {symbol}"
            )

        # Convert to DataFrame
        df = pd.DataFrame([
            {
                'open': bar.open,
                'high': bar.high,
                'low': bar.low,
                'close': bar.close,
                'volume': bar.volume,
                'timestamp': bar.timestamp,
            }
            for bar in bars
        ])

        # Calculate indicators
        indicators = signal_generator._calculate_indicators(df)

        # Convert NaN to None for JSON serialization
        indicators_clean = {
            k: (None if pd.isna(v) else float(v))
            for k, v in indicators.items()
        }

        return IndicatorResponse(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=df['timestamp'].iloc[-1],
            indicators=indicators_clean,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating indicators: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate indicators")


@router.get(
    "/elliott-wave/{symbol}",
    response_model=ElliottWaveResponse,
    tags=["elliott-wave"],
    summary="Detect Elliott Wave patterns",
    description="""
    Detect Elliott Wave 5-wave impulse patterns with Fibonacci retracements and extensions.

    **Elliott Wave Theory**:
    - 5-wave impulse patterns (waves 1, 2, 3, 4, 5)
    - Wave 2 retracements: 38.2%, 50%, 61.8%, 78.6%
    - Wave 3 extensions: 161.8%, 261.8% of Wave 1
    - Wave 4 retracements: 23.6%, 38.2%
    - Wave 5 targets: 100%, 161.8% of Wave 1

    **Validation Rules**:
    - Wave 2 never retraces more than 100% of Wave 1
    - Wave 3 is never the shortest impulse wave
    - Wave 4 never overlaps Wave 1 price territory

    Returns pattern with wave details, Fibonacci levels, and confidence score.
    """
)
async def get_elliott_wave(
    symbol: str,
    timeframe: str = Query("1h", description="Timeframe for analysis (1m, 5m, 15m, 1h, 4h, 1D)"),
    direction: str = Query("bullish", regex="^(bullish|bearish)$", description="Pattern direction (bullish or bearish)"),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Detect Elliott Wave patterns for symbol.

    Returns 5-wave impulse pattern with Fibonacci levels.
    """
    try:
        # Fetch recent data
        lookback = datetime.utcnow() - timedelta(days=7)
        query = select(OHLCV).where(
            and_(
                OHLCV.symbol == symbol,
                OHLCV.timeframe == timeframe,
                OHLCV.timestamp >= lookback,
            )
        ).order_by(OHLCV.timestamp.asc())

        result = await session.execute(query)
        bars = result.scalars().all()

        if len(bars) < 50:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data for {symbol}. Need at least 50 bars."
            )

        # Convert to DataFrame
        df = pd.DataFrame([
            {
                'open': bar.open,
                'high': bar.high,
                'low': bar.low,
                'close': bar.close,
                'volume': bar.volume,
                'timestamp': bar.timestamp,
            }
            for bar in bars
        ])

        # Detect Elliott Wave
        is_bullish = direction == "bullish"
        pattern = signal_generator.elliott_wave_detector.detect_impulse_wave(df, is_bullish)

        if not pattern:
            raise HTTPException(
                status_code=404,
                detail=f"No Elliott Wave {direction} pattern detected for {symbol}"
            )

        # Convert to response
        waves_response = [
            WaveResponse(
                wave_number=w.wave_number,
                start_idx=w.start_idx,
                end_idx=w.end_idx,
                start_price=w.start_price,
                end_price=w.end_price,
                magnitude=w.magnitude,
                is_up=w.is_up,
            )
            for w in pattern.waves
        ]

        fib_levels_response = [
            FibonacciLevelResponse(
                level=f.level,
                price=f.price,
                level_type=f.level_type,
            )
            for f in pattern.fib_levels
        ]

        return ElliottWaveResponse(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=df['timestamp'].iloc[-1],
            pattern_type=pattern.pattern_type,
            direction=pattern.direction,
            current_wave=pattern.current_wave,
            confidence=pattern.confidence,
            waves=waves_response,
            fibonacci_levels=fib_levels_response,
            is_complete=pattern.is_complete,
            subtype=pattern.subtype,
            is_truncated=pattern.is_truncated,
            extended_wave=pattern.extended_wave,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting Elliott Wave: {e}")
        raise HTTPException(status_code=500, detail="Failed to detect Elliott Wave pattern")


@router.get(
    "/elliott-wave/diagonal/{symbol}",
    response_model=ElliottWaveResponse,
    tags=["elliott-wave"],
    summary="Detect Diagonal patterns (Leading/Ending)",
    description="""
    Detect Elliott Wave Diagonal patterns (Leading or Ending).

    **Leading Diagonal** (Wave 1 or Wave A):
    - Occurs at the start of a trend
    - 5-wave structure with wave overlap (Wave 4 overlaps Wave 1)
    - Wedge shape with converging trendlines
    - Wave 1 typically longest, Wave 5 shortest

    **Ending Diagonal** (Wave 5 or Wave C):
    - Occurs at end of trend (exhaustion pattern)
    - 5-wave structure with wave overlap
    - Contracting wedge shape
    - Often accompanied by RSI/MACD divergence
    - HIGH-VALUE reversal signal

    Returns diagonal pattern with wave details and confidence score.
    """
)
async def get_diagonal_pattern(
    symbol: str,
    timeframe: str = Query("1h", description="Timeframe for analysis"),
    direction: str = Query("bullish", regex="^(bullish|bearish)$", description="Pattern direction"),
    diagonal_type: str = Query("ending", regex="^(leading|ending)$", description="Diagonal type (leading or ending)"),
    session: AsyncSession = Depends(get_db_session),
):
    """Detect Leading or Ending Diagonal patterns."""
    try:
        # Fetch recent data
        lookback = datetime.utcnow() - timedelta(days=7)
        query = select(OHLCV).where(
            and_(
                OHLCV.symbol == symbol,
                OHLCV.timeframe == timeframe,
                OHLCV.timestamp >= lookback,
            )
        ).order_by(OHLCV.timestamp.asc())

        result = await session.execute(query)
        bars = result.scalars().all()

        if len(bars) < 50:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data for {symbol}. Need at least 50 bars."
            )

        # Convert to DataFrame
        df = pd.DataFrame([
            {
                'open': bar.open,
                'high': bar.high,
                'low': bar.low,
                'close': bar.close,
                'volume': bar.volume,
                'timestamp': bar.timestamp,
            }
            for bar in bars
        ])

        # Detect diagonal pattern
        is_bullish = direction == "bullish"

        if diagonal_type == "leading":
            pattern = signal_generator.elliott_wave_detector.detect_leading_diagonal(df, is_bullish)
        else:
            pattern = signal_generator.elliott_wave_detector.detect_ending_diagonal(df, is_bullish)

        if not pattern:
            raise HTTPException(
                status_code=404,
                detail=f"No {diagonal_type} diagonal {direction} pattern detected for {symbol}"
            )

        # Convert to response
        waves_response = [
            WaveResponse(
                wave_number=w.wave_number,
                start_idx=w.start_idx,
                end_idx=w.end_idx,
                start_price=w.start_price,
                end_price=w.end_price,
                magnitude=w.magnitude,
                is_up=w.is_up,
            )
            for w in pattern.waves
        ]

        fib_levels_response = [
            FibonacciLevelResponse(
                level=f.level,
                price=f.price,
                level_type=f.level_type,
            )
            for f in pattern.fib_levels
        ]

        return ElliottWaveResponse(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=df['timestamp'].iloc[-1],
            pattern_type=pattern.pattern_type,
            direction=pattern.direction,
            current_wave=pattern.current_wave,
            confidence=pattern.confidence,
            waves=waves_response,
            fibonacci_levels=fib_levels_response,
            is_complete=pattern.is_complete,
            subtype=pattern.subtype,
            is_truncated=pattern.is_truncated,
            extended_wave=pattern.extended_wave,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting diagonal pattern: {e}")
        raise HTTPException(status_code=500, detail="Failed to detect diagonal pattern")


@router.get(
    "/elliott-wave/correction/{symbol}",
    response_model=ElliottWaveResponse,
    tags=["elliott-wave"],
    summary="Detect Correction patterns (Zig-Zag, Flat, Triangle)",
    description="""
    Detect Elliott Wave correction patterns (A-B-C or A-B-C-D-E).

    **Zig-Zag Correction** (5-3-5 structure):
    - Sharp correction against major trend
    - Wave B < Wave A
    - Wave C = 100%-161.8% of Wave A
    - Most common corrective pattern

    **Flat Correction** (3-3-5 structure):
    - Sideways correction
    - Wave B retraces most/all of Wave A
    - Types: Regular, Expanded, Running

    **Triangle Pattern** (3-3-3-3-3 structure):
    - 5 overlapping corrective waves (A-B-C-D-E)
    - Converging or diverging trendlines
    - Balance between buyers and sellers
    - Continuation pattern (occurs before final push)

    Returns correction pattern with wave details and type classification.
    """
)
async def get_correction_pattern(
    symbol: str,
    timeframe: str = Query("1h", description="Timeframe for analysis"),
    correction_type: str = Query("zigzag", regex="^(zigzag|flat|triangle)$", description="Correction type"),
    session: AsyncSession = Depends(get_db_session),
):
    """Detect correction patterns (Zig-Zag, Flat, or Triangle)."""
    try:
        # Fetch recent data
        lookback = datetime.utcnow() - timedelta(days=7)
        query = select(OHLCV).where(
            and_(
                OHLCV.symbol == symbol,
                OHLCV.timeframe == timeframe,
                OHLCV.timestamp >= lookback,
            )
        ).order_by(OHLCV.timestamp.asc())

        result = await session.execute(query)
        bars = result.scalars().all()

        if len(bars) < 50:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data for {symbol}. Need at least 50 bars."
            )

        # Convert to DataFrame
        df = pd.DataFrame([
            {
                'open': bar.open,
                'high': bar.high,
                'low': bar.low,
                'close': bar.close,
                'volume': bar.volume,
                'timestamp': bar.timestamp,
            }
            for bar in bars
        ])

        # Detect correction pattern
        if correction_type == "zigzag":
            pattern = signal_generator.elliott_wave_detector.detect_zigzag_correction(df, is_bullish=False)
        elif correction_type == "flat":
            pattern = signal_generator.elliott_wave_detector.detect_flat_correction(df, is_bullish=False)
        else:  # triangle
            pattern = signal_generator.elliott_wave_detector.detect_triangle_pattern(df, is_bullish=False)

        if not pattern:
            raise HTTPException(
                status_code=404,
                detail=f"No {correction_type} correction pattern detected for {symbol}"
            )

        # Convert to response
        waves_response = [
            WaveResponse(
                wave_number=w.wave_number,
                start_idx=w.start_idx,
                end_idx=w.end_idx,
                start_price=w.start_price,
                end_price=w.end_price,
                magnitude=w.magnitude,
                is_up=w.is_up,
            )
            for w in pattern.waves
        ]

        fib_levels_response = [
            FibonacciLevelResponse(
                level=f.level,
                price=f.price,
                level_type=f.level_type,
            )
            for f in pattern.fib_levels
        ]

        return ElliottWaveResponse(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=df['timestamp'].iloc[-1],
            pattern_type=pattern.pattern_type,
            direction=pattern.direction,
            current_wave=pattern.current_wave,
            confidence=pattern.confidence,
            waves=waves_response,
            fibonacci_levels=fib_levels_response,
            is_complete=pattern.is_complete,
            subtype=pattern.subtype,
            is_truncated=pattern.is_truncated,
            extended_wave=pattern.extended_wave,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting correction pattern: {e}")
        raise HTTPException(status_code=500, detail="Failed to detect correction pattern")


@router.get(
    "/divergences/{symbol}",
    response_model=DivergencesResponse,
    tags=["divergences"],
    summary="Detect RSI divergences",
    description="""
    Detect RSI divergence patterns with Break of Structure (BOS) confirmation.

    **Regular Divergences** (Reversal signals):
    - **Regular Bullish**: Price makes lower low (LL), RSI makes higher low (HL) → Reversal UP
    - **Regular Bearish**: Price makes higher high (HH), RSI makes lower high (LH) → Reversal DOWN

    **Hidden Divergences** (Continuation signals):
    - **Hidden Bullish**: Price makes higher low (HL), RSI makes lower low (LL) → Continuation UP
    - **Hidden Bearish**: Price makes lower high (LH), RSI makes higher high (HH) → Continuation DOWN

    **Break of Structure Confirmation**:
    - Confirmed divergences require price to break previous high/low
    - Unconfirmed divergences show potential but await confirmation
    - Confidence scores range from 50-100 based on divergence strength and confirmation

    Returns all detected divergences sorted by recency.
    """
)
async def get_divergences(
    symbol: str,
    timeframe: str = Query("1h", description="Timeframe for analysis (1m, 5m, 15m, 1h, 4h, 1D)"),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Detect RSI divergences for symbol.

    Returns regular and hidden divergences with Break of Structure confirmation.
    """
    try:
        # Fetch recent data
        lookback = datetime.utcnow() - timedelta(days=7)
        query = select(OHLCV).where(
            and_(
                OHLCV.symbol == symbol,
                OHLCV.timeframe == timeframe,
                OHLCV.timestamp >= lookback,
            )
        ).order_by(OHLCV.timestamp.asc())

        result = await session.execute(query)
        bars = result.scalars().all()

        if len(bars) < 50:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data for {symbol}. Need at least 50 bars."
            )

        # Convert to DataFrame
        df = pd.DataFrame([
            {
                'open': bar.open,
                'high': bar.high,
                'low': bar.low,
                'close': bar.close,
                'volume': bar.volume,
                'timestamp': bar.timestamp,
            }
            for bar in bars
        ])

        # Calculate RSI
        from ..core.config import settings
        rsi = signal_generator.indicator_calc.calculate_rsi(df['close'], settings.RSI_PERIOD)

        # Detect all divergences
        divergences = signal_generator.divergence_detector.detect_all_divergences(df, rsi)

        # Convert to response
        divergences_response = [
            DivergenceResponse(
                divergence_type=d.divergence_type.value,
                start_idx=d.start_idx,
                end_idx=d.end_idx,
                price_start=d.price_start,
                price_end=d.price_end,
                rsi_start=d.rsi_start,
                rsi_end=d.rsi_end,
                confirmed=d.confirmed,
                confidence=d.confidence,
                description=d.description,
                is_bullish=d.is_bullish,
                is_reversal=d.is_reversal,
            )
            for d in divergences
        ]

        return DivergencesResponse(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=df['timestamp'].iloc[-1],
            divergences=divergences_response,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting divergences: {e}")
        raise HTTPException(status_code=500, detail="Failed to detect divergences")


@router.get(
    "/smart-money/{symbol}",
    response_model=SmartMoneyResponse,
    tags=["smart-money"],
    summary="Detect Smart Money Concepts",
    description="""
    Detect institutional trading patterns (Smart Money Concepts) for the specified symbol.

    **Break of Structure (BOS)**:
    - Price breaking previous swing high/low in trend direction
    - Volume confirmation for stronger signals
    - Strength measured as percentage of break

    **Change of Character (CHoCH)**:
    - Price breaking structure against trend (potential reversal)
    - Signals shift in market sentiment

    **Fair Value Gaps (FVG)**:
    - Price imbalances between candles
    - Bullish FVG: Candle 1 high < Candle 3 low (gap between)
    - Bearish FVG: Candle 1 low > Candle 3 high (gap between)
    - Tracks if gaps have been filled

    **Supply/Demand Zones**:
    - Areas where price reversed significantly
    - Supply zones: Resistance areas (selling pressure)
    - Demand zones: Support areas (buying pressure)
    - Strength based on number of touches and reactions
    - Active zones haven't been violated

    **Order Blocks**:
    - Last opposing candle before strong directional move
    - Bullish Order Block: Last bearish candle before strong bullish move
    - Bearish Order Block: Last bullish candle before strong bearish move
    - Represents institutional entry zones
    - High probability support/resistance on retest

    **Liquidity Sweeps**:
    - Stop hunts/raids before institutional entry
    - Price briefly breaks swing high/low then reverses
    - Triggers retail stops, provides liquidity for institutions
    - Often precedes strong move in opposite direction

    Returns all detected institutional patterns with strength scores and activity status.
    """
)
async def get_smart_money_concepts(
    symbol: str,
    timeframe: str = Query("1h", description="Timeframe for analysis (1m, 5m, 15m, 1h, 4h, 1D)"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Detect Smart Money Concepts for symbol.

    Returns Break of Structure, Fair Value Gaps, Supply/Demand zones, Order Blocks, and Liquidity Sweeps.

    **Authentication Required**: This endpoint requires a valid JWT token.
    """
    try:
        # Fetch recent data
        lookback = datetime.utcnow() - timedelta(days=7)
        query = select(OHLCV).where(
            and_(
                OHLCV.symbol == symbol,
                OHLCV.timeframe == timeframe,
                OHLCV.timestamp >= lookback,
            )
        ).order_by(OHLCV.timestamp.asc())

        result = await session.execute(query)
        bars = result.scalars().all()

        if len(bars) < 50:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data for {symbol}. Need at least 50 bars."
            )

        # Convert to DataFrame
        df = pd.DataFrame([
            {
                'open': bar.open,
                'high': bar.high,
                'low': bar.low,
                'close': bar.close,
                'volume': bar.volume,
                'timestamp': bar.timestamp,
            }
            for bar in bars
        ])

        # Set datetime index for session/daily liquidity detection
        df = df.set_index('timestamp')

        # Detect Smart Money Concepts (All 14 Patterns)

        # Core 6 patterns
        structure_breaks = signal_generator.smc_detector.detect_break_of_structure(df)
        fvgs = signal_generator.smc_detector.detect_fair_value_gaps(df)
        zones = signal_generator.smc_detector.detect_supply_demand_zones(df)
        order_blocks = signal_generator.smc_detector.detect_order_blocks(df)
        liquidity_sweeps = signal_generator.smc_detector.detect_liquidity_sweeps(df)

        # New 8 patterns
        equal_highs_lows = signal_generator.smc_detector.detect_equal_highs_lows(df)
        order_flow = signal_generator.smc_detector.detect_order_flow(df)
        institutional_funding_candles = signal_generator.smc_detector.detect_institutional_funding_candles(df)
        false_bos = signal_generator.smc_detector.detect_false_break_of_structure(df)
        session_liquidity = signal_generator.smc_detector.detect_session_liquidity(df)
        daily_liquidity = signal_generator.smc_detector.detect_daily_liquidity(df)
        smart_money_traps = signal_generator.smc_detector.detect_smart_money_trap(df)
        inducements = signal_generator.smc_detector.detect_inducement(df)

        # Convert to response
        bos_response = [
            BreakOfStructureResponse(
                structure_type=bos.structure_type.value,
                break_idx=bos.break_idx,
                break_price=bos.break_price,
                previous_level=bos.previous_level,
                strength=bos.strength,
                volume_confirmation=bos.volume_confirmation,
                description=bos.description,
                is_bullish=bos.is_bullish,
            )
            for bos in structure_breaks
        ]

        fvg_response = [
            FairValueGapResponse(
                direction=fvg.direction,
                start_idx=fvg.start_idx,
                end_idx=fvg.end_idx,
                gap_high=fvg.gap_high,
                gap_low=fvg.gap_low,
                gap_size=fvg.gap_size,
                midpoint=fvg.midpoint,
                filled=fvg.filled,
                strength=fvg.strength,
            )
            for fvg in fvgs
        ]

        zone_response = [
            SupplyDemandZoneResponse(
                zone_type=zone.zone_type.value,
                start_idx=zone.start_idx,
                end_idx=zone.end_idx,
                zone_high=zone.zone_high,
                zone_low=zone.zone_low,
                zone_size=zone.zone_size,
                midpoint=zone.midpoint,
                strength=zone.strength,
                active=zone.active,
                touches=zone.touches,
                is_supply=zone.is_supply,
            )
            for zone in zones
        ]

        # Order blocks use same structure as zones
        order_block_response = [
            SupplyDemandZoneResponse(
                zone_type=ob.zone_type.value,
                start_idx=ob.start_idx,
                end_idx=ob.end_idx,
                zone_high=ob.zone_high,
                zone_low=ob.zone_low,
                zone_size=ob.zone_size,
                midpoint=ob.midpoint,
                strength=ob.strength,
                active=ob.active,
                touches=ob.touches,
                is_supply=ob.is_supply,
            )
            for ob in order_blocks
        ]

        # Liquidity sweeps
        sweep_response = [
            LiquiditySweepResponse(
                sweep_type=sweep['type'],
                sweep_idx=sweep['idx'],
                sweep_level=sweep['sweep_level'],
                description=sweep['description'],
                is_bullish=sweep['type'] == 'bullish_sweep',
            )
            for sweep in liquidity_sweeps
        ]

        # Equal Highs/Lows
        eq_response = [
            EqualHighsLowsResponse(
                eq_type=eq.eq_type,
                level=eq.level,
                count=eq.count,
                indices=eq.indices,
                swept=eq.swept,
                sweep_idx=eq.sweep_idx,
                strength=eq.strength,
                is_resistance=eq.is_equal_highs,
            )
            for eq in equal_highs_lows
        ]

        # Order Flow
        of_response = [
            OrderFlowResponse(
                of_type=of.of_type,
                candle_idx=of.candle_idx,
                zone_high=of.zone_high,
                zone_low=of.zone_low,
                strength=of.strength,
                active=of.active,
                description=of.description,
                is_bullish=of.is_bullish,
            )
            for of in order_flow
        ]

        # Institutional Funding Candles
        ifc_response = [
            InstitutionalFundingCandleResponse(
                ifc_type=ifc.ifc_type,
                candle_idx=ifc.candle_idx,
                swept_level=ifc.swept_level,
                wick_extreme=ifc.wick_extreme,
                close_price=ifc.close_price,
                strength=ifc.strength,
                reversal_confirmed=ifc.reversal_confirmed,
                description=ifc.description,
                is_bullish=ifc.is_bullish,
            )
            for ifc in institutional_funding_candles
        ]

        # False Break of Structure
        fbos_response = [
            FalseBreakOfStructureResponse(
                fbos_type=fbos['fbos_type'],
                bos_idx=fbos['bos_idx'],
                invalidation_idx=fbos['invalidation_idx'],
                break_level=fbos['break_level'],
                previous_level=fbos['previous_level'],
                description=fbos['description'],
                trap_signal=fbos['trap_signal'],
            )
            for fbos in false_bos
        ]

        # Session Liquidity
        session_response = [
            SessionLiquidityResponse(
                session_name=session.session_name,
                session_date=session.session_date,
                session_high=session.session_high,
                session_low=session.session_low,
                high_swept=session.high_swept,
                low_swept=session.low_swept,
                range_size=session.range_size,
            )
            for session in session_liquidity
        ]

        # Daily Liquidity
        daily_liq_response = DailyLiquidityResponse(
            pdh=daily_liquidity.get('pdh'),
            pdl=daily_liquidity.get('pdl'),
            pwh=daily_liquidity.get('pwh'),
            pwl=daily_liquidity.get('pwl'),
        )

        # Smart Money Traps
        smt_response = [
            SmartMoneyTrapResponse(
                smt_type=smt['smt_type'],
                bos_idx=smt['bos_idx'],
                pullback_idx=smt['pullback_idx'],
                trap_level=smt['trap_level'],
                description=smt['description'],
                signal=smt['signal'],
            )
            for smt in smart_money_traps
        ]

        # Inducements
        idm_response = [
            InducementResponse(
                idm_type=idm['idm_type'],
                inducement_idx=idm['inducement_idx'],
                reversal_idx=idm['reversal_idx'],
                inducement_price=idm['inducement_price'],
                move_percentage=idm['move_percentage'],
                description=idm['description'],
                signal=idm['signal'],
            )
            for idm in inducements
        ]

        return SmartMoneyResponse(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=df.index[-1],
            structure_breaks=bos_response,
            fair_value_gaps=fvg_response,
            supply_demand_zones=zone_response,
            order_blocks=order_block_response,
            liquidity_sweeps=sweep_response,
            equal_highs_lows=eq_response,
            order_flow=of_response,
            institutional_funding_candles=ifc_response,
            false_break_of_structure=fbos_response,
            session_liquidity=session_response,
            daily_liquidity=daily_liq_response,
            smart_money_traps=smt_response,
            inducements=idm_response,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting Smart Money Concepts: {e}")
        raise HTTPException(status_code=500, detail="Failed to detect Smart Money Concepts")


@router.post(
    "/signals/comprehensive-analysis",
    response_model=TradingDecisionResponse,
    tags=["signals"],
    summary="Comprehensive Multi-Timeframe Analysis with Reasoning",
    description="""
    **INTELLIGENT ANALYSIS WITH REASONING AND EVIDENCE**

    This endpoint provides a complete trading decision with full justification using:

    **Multi-Timeframe Analysis**:
    - Analyzes 6 timeframes (1MO, 1W, 1D, 4H, 1H, 15M)
    - Detects all 14 Smart Money Concepts on each timeframe
    - Detects Elliott Wave patterns on each timeframe
    - Calculates all indicators on each timeframe
    - Identifies divergences on each timeframe

    **Evidence-Based Reasoning**:
    - Builds arguments with claims, evidence, and reasoning
    - Identifies counter-arguments (critical for risk assessment)
    - Evaluates confluence across timeframes
    - Provides detailed interpretation of each piece of evidence

    **Fundamental Integration**:
    - Fetches fundamental data (when available)
    - Acknowledges fundamental lag explicitly
    - Interprets technical-fundamental alignment/divergence
    - Provides nuanced interpretation of conflicts

    **Risk Assessment**:
    - Multi-dimensional risk evaluation
    - Identifies specific risks with mitigation strategies
    - Estimates max drawdown and probability of loss
    - Provides position sizing recommendations

    **Entry Plan**:
    - Entry price with reasoning
    - Stop loss with reasoning
    - Multiple targets with probabilities
    - Risk/reward calculation
    - Entry triggers and invalidation levels

    **Final Decision**:
    - BUY, SELL, or WAIT with confidence level
    - Executive summary for quick reading
    - Detailed reasoning with all analysis
    - Confidence breakdown showing contributing factors

    This is the "brain" of the system - it reasons, argues, and justifies every decision.
    """
)
async def comprehensive_analysis(
    request: GenerateSignalRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Generate comprehensive trading decision with full reasoning.

    This endpoint performs the complete intelligent analysis:
    1. Multi-timeframe technical analysis (6 timeframes)
    2. Evidence collection from all sources
    3. Argument building with reasoning
    4. Fundamental alignment (if available)
    5. Risk assessment
    6. Entry plan construction
    7. Final decision with complete justification

    **Authentication Required**: This endpoint requires a valid JWT token.
    The trading decision will be saved with your user_id for isolation.
    """
    try:
        logger.info(f"Starting comprehensive analysis for {request.symbol}...")

        # Step 1: Multi-Timeframe Analysis
        logger.info("Step 1: Analyzing all timeframes...")
        mtf_analysis = await mtf_analyzer.analyze_symbol(
            request.symbol,
            session,
        )

        # Step 2: Build Primary Argument
        logger.info("Step 2: Building primary argument...")
        primary_argument = reasoning_engine.build_multi_timeframe_argument(mtf_analysis)

        # Step 3: Identify Counter-Arguments
        logger.info("Step 3: Identifying counter-arguments...")
        counter_arguments = reasoning_engine.identify_counter_arguments(mtf_analysis)

        # Step 4: Evaluate Confluence
        logger.info("Step 4: Evaluating confluence...")
        confluence_analysis = reasoning_engine.evaluate_confluence(mtf_analysis)

        # Step 5: Fetch and Analyze Fundamentals
        logger.info("Step 5: Fetching fundamental data...")
        fundamental_data = await fundamental_analyzer.fetch_fundamental_data(request.symbol)

        if fundamental_data:
            fundamental_data = fundamental_analyzer.analyze_fundamental_data(fundamental_data)

        fundamental_alignment = fundamental_analyzer.align_with_technical(
            mtf_analysis.overall_bias,
            mtf_analysis.overall_confidence,
            fundamental_data,
        )

        # Step 6: Get Current Price (from strongest timeframe)
        strongest_tf = mtf_analysis.strongest_timeframe
        strongest_analysis = mtf_analysis.timeframe_analyses[strongest_tf]

        # Fetch latest bar for current price
        latest_query = select(OHLCV).where(
            and_(
                OHLCV.symbol == request.symbol,
                OHLCV.timeframe == strongest_tf,
            )
        ).order_by(OHLCV.timestamp.desc()).limit(1)

        result = await session.execute(latest_query)
        latest_bar = result.scalar_one_or_none()

        if not latest_bar:
            raise HTTPException(
                status_code=400,
                detail=f"No price data available for {request.symbol}"
            )

        current_price = latest_bar.close

        # Step 7: Make Final Decision
        logger.info("Step 7: Making final decision...")
        decision = decision_framework.make_decision(
            mtf_analysis,
            primary_argument,
            counter_arguments,
            confluence_analysis,
            fundamental_alignment,
            current_price,
        )

        # Step 8: Convert to Response
        logger.info("Step 8: Converting to response...")

        # Convert arguments
        primary_args_response = [
            ArgumentResponse(
                claim=arg.claim,
                evidence=[
                    EvidenceResponse(
                        source=e.source,
                        type=e.type,
                        description=e.description,
                        score=e.score,
                        confidence=e.confidence,
                        timestamp=e.timestamp,
                    )
                    for e in arg.evidence
                ],
                reasoning=arg.reasoning,
                confidence=arg.confidence,
                timeframe=arg.timeframe,
                evidence_count=arg.evidence_count,
                total_evidence_score=arg.total_evidence_score,
            )
            for arg in decision.primary_arguments
        ]

        counter_args_response = [
            ArgumentResponse(
                claim=arg.claim,
                evidence=[
                    EvidenceResponse(
                        source=e.source,
                        type=e.type,
                        description=e.description,
                        score=e.score,
                        confidence=e.confidence,
                        timestamp=e.timestamp,
                    )
                    for e in arg.evidence
                ],
                reasoning=arg.reasoning,
                confidence=arg.confidence,
                timeframe=arg.timeframe,
                evidence_count=arg.evidence_count,
                total_evidence_score=arg.total_evidence_score,
            )
            for arg in decision.counter_arguments
        ]

        # Convert fundamental alignment
        fundamental_alignment_response = None
        if decision.fundamental_alignment:
            fundamental_alignment_response = FundamentalAlignmentResponse(
                direction=decision.fundamental_alignment.direction.value,
                strength=decision.fundamental_alignment.strength,
                lag_assessment=decision.fundamental_alignment.lag_assessment,
                data=decision.fundamental_alignment.data,
                interpretation=decision.fundamental_alignment.interpretation,
            )

        # Convert risk assessment
        risk_assessment_response = RiskAssessmentResponse(
            primary_risks=decision.risk_assessment.primary_risks,
            risk_level=decision.risk_assessment.risk_level,
            mitigation=decision.risk_assessment.mitigation,
            max_drawdown_estimate=decision.risk_assessment.max_drawdown_estimate,
            probability_of_loss=decision.risk_assessment.probability_of_loss,
            upcoming_events=decision.risk_assessment.upcoming_events,
            event_impact=decision.risk_assessment.event_impact,
        )

        # Convert entry plan
        entry_plan_response = None
        if decision.entry_plan:
            entry_plan_response = EntryPlanResponse(
                entry_price=decision.entry_plan.entry_price,
                entry_reasoning=decision.entry_plan.entry_reasoning,
                stop_loss=decision.entry_plan.stop_loss,
                stop_reasoning=decision.entry_plan.stop_reasoning,
                targets=[
                    TargetResponse(
                        price=target.price,
                        reasoning=target.reasoning,
                        percent_exit=target.percent_exit,
                        probability=target.probability,
                        timeframe_estimate=target.timeframe_estimate,
                    )
                    for target in decision.entry_plan.targets
                ],
                risk_reward=decision.entry_plan.risk_reward,
                position_size_recommendation=decision.entry_plan.position_size_recommendation,
                entry_trigger=decision.entry_plan.entry_trigger,
                invalidation=decision.entry_plan.invalidation,
            )

        logger.info(f"Comprehensive analysis complete: {decision.action.value} {decision.symbol} ({decision.confidence:.1%})")

        # Step 9: Save trading decision to database with user_id
        logger.info("Step 9: Saving trading decision to database...")

        # Create TradingDecision model instance
        trading_decision_model = TradingDecision(
            user_id=str(current_user.id),  # CRITICAL: User isolation
            symbol=decision.symbol,
            action=decision.action,
            confidence=decision.confidence,
            confidence_level=decision.confidence_level,
            generated_at=decision.generated_at,
            expires_at=decision.expires_at,
            should_trade="true" if decision.should_trade else "false",

            # Arguments (JSON)
            primary_arguments=[
                {
                    "claim": arg.claim,
                    "evidence": [
                        {
                            "source": e.source,
                            "type": e.type,
                            "description": e.description,
                            "score": e.score,
                            "confidence": e.confidence,
                            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                        }
                        for e in arg.evidence
                    ],
                    "reasoning": arg.reasoning,
                    "confidence": arg.confidence,
                    "timeframe": arg.timeframe,
                    "evidence_count": arg.evidence_count,
                    "total_evidence_score": arg.total_evidence_score,
                }
                for arg in decision.primary_arguments
            ],
            counter_arguments=[
                {
                    "claim": arg.claim,
                    "evidence": [
                        {
                            "source": e.source,
                            "type": e.type,
                            "description": e.description,
                            "score": e.score,
                            "confidence": e.confidence,
                            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                        }
                        for e in arg.evidence
                    ],
                    "reasoning": arg.reasoning,
                    "confidence": arg.confidence,
                    "timeframe": arg.timeframe,
                    "evidence_count": arg.evidence_count,
                    "total_evidence_score": arg.total_evidence_score,
                }
                for arg in decision.counter_arguments
            ],

            # Fundamental alignment (JSON)
            fundamental_alignment={
                "direction": decision.fundamental_alignment.direction.value if decision.fundamental_alignment else None,
                "strength": decision.fundamental_alignment.strength if decision.fundamental_alignment else None,
                "lag_assessment": decision.fundamental_alignment.lag_assessment if decision.fundamental_alignment else None,
                "data": decision.fundamental_alignment.data if decision.fundamental_alignment else None,
                "interpretation": decision.fundamental_alignment.interpretation if decision.fundamental_alignment else None,
            } if decision.fundamental_alignment else None,

            # Risk assessment (JSON)
            risk_assessment={
                "primary_risks": decision.risk_assessment.primary_risks,
                "risk_level": decision.risk_assessment.risk_level,
                "mitigation": decision.risk_assessment.mitigation,
                "max_drawdown_estimate": decision.risk_assessment.max_drawdown_estimate,
                "probability_of_loss": decision.risk_assessment.probability_of_loss,
                "upcoming_events": decision.risk_assessment.upcoming_events,
                "event_impact": decision.risk_assessment.event_impact,
            },

            # Entry plan (JSON)
            entry_plan={
                "entry_price": decision.entry_plan.entry_price,
                "entry_reasoning": decision.entry_plan.entry_reasoning,
                "stop_loss": decision.entry_plan.stop_loss,
                "stop_reasoning": decision.entry_plan.stop_reasoning,
                "targets": [
                    {
                        "price": target.price,
                        "reasoning": target.reasoning,
                        "percent_exit": target.percent_exit,
                        "probability": target.probability,
                        "timeframe_estimate": target.timeframe_estimate,
                    }
                    for target in decision.entry_plan.targets
                ],
                "risk_reward": decision.entry_plan.risk_reward,
                "position_size_recommendation": decision.entry_plan.position_size_recommendation,
                "entry_trigger": decision.entry_plan.entry_trigger,
                "invalidation": decision.entry_plan.invalidation,
            } if decision.entry_plan else None,

            # Timeframe summary (JSON) - TODO: Add this to decision_framework if not present
            timeframe_summary={tf: {"bias": mtf_analysis.timeframe_analyses[tf].bias.value, "confidence": mtf_analysis.timeframe_analyses[tf].confidence} for tf in mtf_analysis.timeframe_analyses.keys()},

            # Confidence breakdown (JSON)
            confidence_breakdown=decision.confidence_breakdown,

            # Reasoning narratives (TEXT)
            executive_summary=decision.executive_summary,
            detailed_reasoning=decision.detailed_reasoning,
        )

        session.add(trading_decision_model)
        await session.commit()
        await session.refresh(trading_decision_model)

        logger.info(f"Trading decision saved to database with ID: {trading_decision_model.id}")

        return TradingDecisionResponse(
            symbol=decision.symbol,
            action=decision.action.value,
            confidence=decision.confidence,
            confidence_level=decision.confidence_level.value,
            primary_arguments=primary_args_response,
            counter_arguments=counter_args_response,
            fundamental_alignment=fundamental_alignment_response,
            risk_assessment=risk_assessment_response,
            entry_plan=entry_plan_response,
            confidence_breakdown=decision.confidence_breakdown,
            executive_summary=decision.executive_summary,
            detailed_reasoning=decision.detailed_reasoning,
            generated_at=decision.generated_at,
            expires_at=decision.expires_at,
            should_trade=decision.should_trade,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in comprehensive analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to complete comprehensive analysis: {str(e)}")
