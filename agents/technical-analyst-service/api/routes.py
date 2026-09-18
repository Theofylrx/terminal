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
from shared.database.models import OHLCV, Signal
from shared.database.models.signal import SignalStatus

from .schemas import (
    GenerateSignalRequest,
    SignalResponse,
    HealthResponse,
    IndicatorResponse,
)
from ..services.signal_generator import SignalGenerator


logger = logging.getLogger(__name__)

router = APIRouter()

# Global signal generator instance
signal_generator = SignalGenerator()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
    )


@router.post("/signals/generate", response_model=SignalResponse)
async def generate_signal(
    request: GenerateSignalRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Generate trading signal for symbol.

    Analyzes recent price data and generates a trading signal
    based on technical indicators and patterns.
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


@router.get("/signals", response_model=List[SignalResponse])
async def get_signals(
    symbol: str = Query(None),
    status: str = Query(None),
    limit: int = Query(100, le=500),
    session: AsyncSession = Depends(get_db_session),
):
    """Get trading signals with optional filters."""
    try:
        query = select(Signal).order_by(Signal.generated_at.desc())

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


@router.get("/signals/{signal_id}", response_model=SignalResponse)
async def get_signal(
    signal_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """Get specific signal by ID."""
    try:
        query = select(Signal).where(Signal.id == signal_id)
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


@router.get("/indicators/{symbol}", response_model=IndicatorResponse)
async def get_indicators(
    symbol: str,
    timeframe: str = Query("1h"),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get current technical indicators for symbol.

    Returns calculated indicator values without generating a signal.
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
