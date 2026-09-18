"""Technical indicator calculator."""

import logging
from typing import List, Optional
import pandas as pd
import numpy as np

from .models import (
    IndicatorResult,
    IndicatorType,
    MACDResult,
    BollingerBandsResult,
    StochasticResult,
)


logger = logging.getLogger(__name__)


class IndicatorCalculator:
    """
    Technical indicator calculator.

    Calculates various technical indicators from OHLCV data.
    """

    @staticmethod
    def calculate_sma(prices: pd.Series, period: int) -> pd.Series:
        """
        Calculate Simple Moving Average.

        Args:
            prices: Price series (usually close prices).
            period: SMA period.

        Returns:
            SMA values.
        """
        return prices.rolling(window=period).mean()

    @staticmethod
    def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
        """
        Calculate Exponential Moving Average.

        Args:
            prices: Price series.
            period: EMA period.

        Returns:
            EMA values.
        """
        return prices.ewm(span=period, adjust=False).mean()

    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index.

        Args:
            prices: Price series.
            period: RSI period (default 14).

        Returns:
            RSI values (0-100).
        """
        # Calculate price changes
        delta = prices.diff()

        # Separate gains and losses
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)

        # Calculate average gains and losses
        avg_gains = gains.rolling(window=period).mean()
        avg_losses = losses.rolling(window=period).mean()

        # Calculate RS and RSI
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))

        return rsi

    @staticmethod
    def calculate_macd(
        prices: pd.Series,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> pd.DataFrame:
        """
        Calculate MACD (Moving Average Convergence Divergence).

        Args:
            prices: Price series.
            fast_period: Fast EMA period.
            slow_period: Slow EMA period.
            signal_period: Signal line period.

        Returns:
            DataFrame with macd_line, signal_line, and histogram.
        """
        # Calculate EMAs
        ema_fast = prices.ewm(span=fast_period, adjust=False).mean()
        ema_slow = prices.ewm(span=slow_period, adjust=False).mean()

        # MACD line
        macd_line = ema_fast - ema_slow

        # Signal line
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()

        # Histogram
        histogram = macd_line - signal_line

        return pd.DataFrame({
            'macd_line': macd_line,
            'signal_line': signal_line,
            'histogram': histogram,
        })

    @staticmethod
    def calculate_bollinger_bands(
        prices: pd.Series,
        period: int = 20,
        std_dev: float = 2.0,
    ) -> pd.DataFrame:
        """
        Calculate Bollinger Bands.

        Args:
            prices: Price series.
            period: Moving average period.
            std_dev: Standard deviation multiplier.

        Returns:
            DataFrame with upper, middle, lower bands, bandwidth, and %B.
        """
        # Middle band (SMA)
        middle_band = prices.rolling(window=period).mean()

        # Standard deviation
        std = prices.rolling(window=period).std()

        # Upper and lower bands
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)

        # Bandwidth (volatility measure)
        bandwidth = (upper_band - lower_band) / middle_band

        # %B (position within bands)
        percent_b = (prices - lower_band) / (upper_band - lower_band)

        return pd.DataFrame({
            'upper_band': upper_band,
            'middle_band': middle_band,
            'lower_band': lower_band,
            'bandwidth': bandwidth,
            'percent_b': percent_b,
        })

    @staticmethod
    def calculate_atr(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14,
    ) -> pd.Series:
        """
        Calculate Average True Range.

        Args:
            high: High prices.
            low: Low prices.
            close: Close prices.
            period: ATR period.

        Returns:
            ATR values.
        """
        # True Range components
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        # True Range (maximum of the three)
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # ATR (smoothed average of TR)
        atr = true_range.rolling(window=period).mean()

        return atr

    @staticmethod
    def calculate_stochastic(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        k_period: int = 14,
        d_period: int = 3,
    ) -> pd.DataFrame:
        """
        Calculate Stochastic Oscillator.

        Args:
            high: High prices.
            low: Low prices.
            close: Close prices.
            k_period: %K period.
            d_period: %D period.

        Returns:
            DataFrame with %K and %D lines.
        """
        # Lowest low and highest high over period
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()

        # %K line
        k_line = 100 * ((close - lowest_low) / (highest_high - lowest_low))

        # %D line (SMA of %K)
        d_line = k_line.rolling(window=d_period).mean()

        return pd.DataFrame({
            'k_line': k_line,
            'd_line': d_line,
        })

    @staticmethod
    def calculate_adx(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14,
    ) -> pd.Series:
        """
        Calculate Average Directional Index.

        Args:
            high: High prices.
            low: Low prices.
            close: Close prices.
            period: ADX period.

        Returns:
            ADX values.
        """
        # Calculate +DM and -DM
        plus_dm = high.diff()
        minus_dm = -low.diff()

        # Set negative values to 0
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0

        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Smooth the values
        atr = true_range.rolling(window=period).mean()
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)

        # Calculate DX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)

        # ADX is smoothed DX
        adx = dx.rolling(window=period).mean()

        return adx

    @staticmethod
    def calculate_cci(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 20,
    ) -> pd.Series:
        """
        Calculate Commodity Channel Index.

        Args:
            high: High prices.
            low: Low prices.
            close: Close prices.
            period: CCI period.

        Returns:
            CCI values.
        """
        # Typical Price
        tp = (high + low + close) / 3

        # SMA of Typical Price
        sma_tp = tp.rolling(window=period).mean()

        # Mean Deviation
        mad = tp.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())

        # CCI
        cci = (tp - sma_tp) / (0.015 * mad)

        return cci

    @staticmethod
    def calculate_williams_r(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14,
    ) -> pd.Series:
        """
        Calculate Williams %R.

        Args:
            high: High prices.
            low: Low prices.
            close: Close prices.
            period: Williams %R period.

        Returns:
            Williams %R values (-100 to 0).
        """
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()

        williams_r = -100 * ((highest_high - close) / (highest_high - lowest_low))

        return williams_r

    @staticmethod
    def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        Calculate On-Balance Volume.

        Args:
            close: Close prices.
            volume: Volume.

        Returns:
            OBV values.
        """
        obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
        return obv

    @staticmethod
    def calculate_vwap(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume: pd.Series,
    ) -> pd.Series:
        """
        Calculate Volume Weighted Average Price.

        Args:
            high: High prices.
            low: Low prices.
            close: Close prices.
            volume: Volume.

        Returns:
            VWAP values.
        """
        typical_price = (high + low + close) / 3
        vwap = (typical_price * volume).cumsum() / volume.cumsum()
        return vwap

    @staticmethod
    def calculate_mfi(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume: pd.Series,
        period: int = 14,
    ) -> pd.Series:
        """
        Calculate Money Flow Index.

        Args:
            high: High prices.
            low: Low prices.
            close: Close prices.
            volume: Volume.
            period: MFI period.

        Returns:
            MFI values (0-100).
        """
        # Typical Price
        tp = (high + low + close) / 3

        # Money Flow
        mf = tp * volume

        # Positive and Negative Money Flow
        positive_mf = mf.where(tp > tp.shift(), 0).rolling(window=period).sum()
        negative_mf = mf.where(tp < tp.shift(), 0).rolling(window=period).sum()

        # Money Flow Ratio
        mfr = positive_mf / negative_mf

        # MFI
        mfi = 100 - (100 / (1 + mfr))

        return mfi

    @staticmethod
    def calculate_roc(prices: pd.Series, period: int = 12) -> pd.Series:
        """
        Calculate Rate of Change.

        Args:
            prices: Price series.
            period: ROC period.

        Returns:
            ROC values (percentage).
        """
        roc = 100 * (prices - prices.shift(period)) / prices.shift(period)
        return roc
