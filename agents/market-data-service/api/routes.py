"""Market Data Service API routes."""

import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import (
    SubscribeRequest,
    UnsubscribeRequest,
    HistoricalBarsRequest,
    BarResponse,
    QuoteResponse,
    TradeResponse,
    StatusResponse,
    SubscriptionResponse,
    HealthResponse,
)
from ..services.market_data_service import MarketDataService
from ..repositories import OHLCVRepository, QuoteRepository, TradeRepository

# Import database session from shared
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from shared.database.connection import get_db_session


logger = logging.getLogger(__name__)

router = APIRouter()


# Dependency to get market data service (will be set in main.py)
_market_data_service: MarketDataService = None


def set_market_data_service(service: MarketDataService):
    """Set the global market data service instance."""
    global _market_data_service
    _market_data_service = service


def get_market_data_service() -> MarketDataService:
    """Get market data service dependency."""
    if _market_data_service is None:
        raise HTTPException(status_code=500, detail="Market data service not initialized")
    return _market_data_service


# ========== Health & Status Endpoints ==========

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0",
    )


@router.get("/status", response_model=StatusResponse)
async def get_status(service: MarketDataService = Depends(get_market_data_service)):
    """Get service status and active subscriptions."""
    return service.get_status()


# ========== Subscription Management ==========

@router.post("/subscribe", response_model=SubscriptionResponse)
async def subscribe_symbols(
    request: SubscribeRequest,
    service: MarketDataService = Depends(get_market_data_service),
):
    """
    Subscribe to real-time market data for symbols.

    Args:
        request: Subscription request with broker and symbols.

    Returns:
        Subscription confirmation.
    """
    try:
        await service.subscribe_symbols(request.broker, request.symbols)

        return SubscriptionResponse(
            broker=request.broker,
            symbols=request.symbols,
            success=True,
            message=f"Successfully subscribed to {len(request.symbols)} symbols",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Subscription error: {e}")
        raise HTTPException(status_code=500, detail="Failed to subscribe")


@router.post("/unsubscribe", response_model=SubscriptionResponse)
async def unsubscribe_symbols(
    request: UnsubscribeRequest,
    service: MarketDataService = Depends(get_market_data_service),
):
    """Unsubscribe from market data for symbols."""
    try:
        await service.unsubscribe_symbols(request.broker, request.symbols)

        return SubscriptionResponse(
            broker=request.broker,
            symbols=request.symbols,
            success=True,
            message=f"Successfully unsubscribed from {len(request.symbols)} symbols",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unsubscription error: {e}")
        raise HTTPException(status_code=500, detail="Failed to unsubscribe")


# ========== Historical Data Endpoints ==========

@router.post("/historical/bars", response_model=List[BarResponse])
async def get_historical_bars(
    request: HistoricalBarsRequest,
    service: MarketDataService = Depends(get_market_data_service),
):
    """
    Fetch historical OHLCV bars from broker and store in database.

    Args:
        request: Historical bars request.

    Returns:
        List of OHLCV bars.
    """
    try:
        bars = await service.get_historical_bars(
            broker=request.broker,
            symbol=request.symbol,
            timeframe=request.timeframe,
            start=request.start,
            end=request.end,
            limit=request.limit,
        )

        return [
            BarResponse(
                symbol=bar.symbol,
                timeframe=bar.timeframe,
                timestamp=bar.timestamp,
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
                volume=bar.volume,
                trade_count=bar.trade_count,
                vwap=bar.vwap,
            )
            for bar in bars
        ]

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Historical bars error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch historical bars")


@router.get("/bars/{symbol}", response_model=List[BarResponse])
async def get_bars(
    symbol: str,
    timeframe: str,
    start: datetime,
    end: datetime,
    limit: int = 1000,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get OHLCV bars from database.

    Args:
        symbol: Trading symbol.
        timeframe: Bar timeframe.
        start: Start datetime.
        end: End datetime.
        limit: Max bars to return.

    Returns:
        List of OHLCV bars.
    """
    repo = OHLCVRepository(session)

    try:
        bars = await repo.get_range(symbol, timeframe, start, end, limit)

        return [
            BarResponse(
                symbol=bar.symbol,
                timeframe=bar.timeframe,
                timestamp=bar.timestamp,
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
                volume=bar.volume,
                trade_count=bar.num_trades,
            )
            for bar in bars
        ]

    except Exception as e:
        logger.error(f"Get bars error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve bars")


@router.get("/quotes/{symbol}", response_model=List[QuoteResponse])
async def get_quotes(
    symbol: str,
    start: datetime,
    end: datetime,
    limit: int = 1000,
    session: AsyncSession = Depends(get_db_session),
):
    """Get quotes from database."""
    repo = QuoteRepository(session)

    try:
        quotes = await repo.get_range(symbol, start, end, limit=limit)

        return [
            QuoteResponse(
                symbol=quote.symbol,
                timestamp=quote.timestamp,
                bid_price=quote.bid_price,
                bid_size=quote.bid_size,
                ask_price=quote.ask_price,
                ask_size=quote.ask_size,
                spread=quote.calculate_spread(),
                mid_price=quote.calculate_mid_price(),
            )
            for quote in quotes
        ]

    except Exception as e:
        logger.error(f"Get quotes error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve quotes")


@router.get("/trades/{symbol}", response_model=List[TradeResponse])
async def get_trades(
    symbol: str,
    start: datetime,
    end: datetime,
    limit: int = 1000,
    session: AsyncSession = Depends(get_db_session),
):
    """Get trades from database."""
    repo = TradeRepository(session)

    try:
        trades = await repo.get_range(symbol, start, end, limit=limit)

        return [
            TradeResponse(
                symbol=trade.symbol,
                timestamp=trade.timestamp,
                price=trade.price,
                size=trade.size,
                notional=trade.calculate_notional(),
                side=trade.side,
                exchange=trade.exchange,
            )
            for trade in trades
        ]

    except Exception as e:
        logger.error(f"Get trades error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve trades")


@router.get("/latest/{symbol}", response_model=BarResponse)
async def get_latest_bar(
    symbol: str,
    timeframe: str = "1m",
    session: AsyncSession = Depends(get_db_session),
):
    """Get latest bar for symbol."""
    repo = OHLCVRepository(session)

    try:
        bar = await repo.get_latest(symbol, timeframe)

        if not bar:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

        return BarResponse(
            symbol=bar.symbol,
            timeframe=bar.timeframe,
            timestamp=bar.timestamp,
            open=bar.open,
            high=bar.high,
            low=bar.low,
            close=bar.close,
            volume=bar.volume,
            trade_count=bar.num_trades,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get latest bar error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve latest bar")


# ========== WebSocket Endpoint ==========

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    service: MarketDataService = Depends(get_market_data_service),
):
    """
    WebSocket endpoint for real-time market data streaming.

    Clients connect and receive real-time trade, quote, and bar updates.
    """
    await websocket.accept()
    service.add_websocket_client(websocket)

    try:
        # Keep connection alive and handle client messages
        while True:
            data = await websocket.receive_text()
            # You can implement client commands here (subscribe/unsubscribe)
            logger.debug(f"Received WebSocket message: {data}")

    except WebSocketDisconnect:
        service.remove_websocket_client(websocket)
        logger.info("WebSocket client disconnected")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        service.remove_websocket_client(websocket)
