"""Fundamental analyzer with explicit lag acknowledgment."""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from ..models.reasoning import (
    FundamentalData,
    FundamentalAlignment,
    BiasType,
)

logger = logging.getLogger(__name__)


class FundamentalAnalyzer:
    """
    Analyzes fundamental data with EXPLICIT lag acknowledgment.

    CRITICAL UNDERSTANDING:
    - Fundamentals are LAGGING indicators
    - They reflect past performance, not future price action
    - Technical analysis leads, fundamentals confirm
    - Use fundamentals for CONTEXT, not primary signals

    Proper interpretation:
    - Tech Bearish + Fund Bullish = Short-term correction in bull market
    - Tech Bullish + Fund Bearish = Relief rally in bear market
    - Tech Bullish + Fund Bullish = Strong uptrend with fundamental support
    - Tech Bearish + Fund Bearish = Strong downtrend with fundamental weakness
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize fundamental analyzer.

        Args:
            api_key: API key for fundamental data provider (optional)
        """
        self.api_key = api_key
        logger.info("Fundamental analyzer initialized (with lag acknowledgment)")

    async def fetch_fundamental_data(
        self,
        symbol: str,
    ) -> Optional[FundamentalData]:
        """
        Fetch fundamental data for symbol.

        In production, this would call:
        - Alpha Vantage API
        - Yahoo Finance API
        - Financial Modeling Prep API
        - IEX Cloud API

        For now, returns mock data structure.

        Args:
            symbol: Stock/crypto symbol

        Returns:
            FundamentalData if available, None otherwise
        """
        logger.info(f"Fetching fundamental data for {symbol}...")

        # TODO: Implement actual API calls
        # For now, return None (no fundamental data available)
        # This allows the system to work with technical-only analysis

        logger.warning(f"Fundamental data not available for {symbol} (API integration pending)")
        return None

        # Example structure for when we implement:
        # return FundamentalData(
        #     symbol=symbol,
        #     asset_type="stock",
        #     earnings_per_share=5.23,
        #     pe_ratio=18.5,
        #     revenue_growth=0.15,
        #     profit_margin=0.22,
        #     analyst_rating="BUY",
        #     analyst_target=185.00,
        #     institutional_ownership=0.78,
        #     fundamental_score=0.0,  # Calculated below
        #     bias=BiasType.NEUTRAL,  # Calculated below
        #     data_timestamp=datetime.utcnow(),
        # )

    def analyze_fundamental_data(
        self,
        fundamental_data: FundamentalData,
    ) -> FundamentalData:
        """
        Analyze fundamental data and assign score/bias.

        Args:
            fundamental_data: Raw fundamental data

        Returns:
            FundamentalData with score and bias calculated
        """
        score = 0.0

        # Earnings score
        if fundamental_data.earnings_per_share:
            if fundamental_data.earnings_per_share > 0:
                score += 15
            else:
                score -= 15

        # Valuation score (P/E ratio)
        if fundamental_data.pe_ratio:
            if fundamental_data.pe_ratio < 15:
                score += 10
            elif fundamental_data.pe_ratio > 30:
                score -= 10

        # Growth score
        if fundamental_data.revenue_growth:
            if fundamental_data.revenue_growth > 0.15:
                score += 12
            elif fundamental_data.revenue_growth < 0:
                score -= 12

        # Profitability score
        if fundamental_data.profit_margin:
            if fundamental_data.profit_margin > 0.20:
                score += 10
            elif fundamental_data.profit_margin < 0:
                score -= 10

        # Analyst opinion (lower weight)
        if fundamental_data.analyst_rating:
            rating = fundamental_data.analyst_rating.upper()
            if rating in ["STRONG BUY", "BUY"]:
                score += 8
            elif rating in ["SELL", "STRONG SELL"]:
                score -= 8

        # Institutional ownership
        if fundamental_data.institutional_ownership:
            if fundamental_data.institutional_ownership > 0.70:
                score += 8

        # Macro factors
        if fundamental_data.gdp_growth:
            if fundamental_data.gdp_growth > 0.03:
                score += 10
            elif fundamental_data.gdp_growth < 0:
                score -= 10

        # Determine bias
        if score > 30:
            bias = BiasType.BULLISH
        elif score < -30:
            bias = BiasType.BEARISH
        else:
            bias = BiasType.NEUTRAL

        fundamental_data.fundamental_score = score
        fundamental_data.bias = bias

        logger.info(f"Fundamental analysis: {bias.value} (score: {score:.0f})")
        return fundamental_data

    def align_with_technical(
        self,
        technical_bias: BiasType,
        technical_confidence: float,
        fundamental_data: Optional[FundamentalData],
    ) -> FundamentalAlignment:
        """
        Analyze alignment between technical and fundamental analysis.

        CRITICAL: This method explicitly acknowledges fundamental lag.

        Args:
            technical_bias: Bias from technical analysis
            technical_confidence: Confidence from technical analysis
            fundamental_data: Fundamental data (if available)

        Returns:
            FundamentalAlignment with interpretation
        """
        if not fundamental_data or fundamental_data.bias == BiasType.NEUTRAL:
            return FundamentalAlignment(
                direction=technical_bias,
                strength="WEAK",
                lag_assessment=self._build_no_fundamental_lag_assessment(),
                data={},
                interpretation="""
                No fundamental data available.

                INTERPRETATION:
                - Proceed with technical analysis only
                - Technical signals are primary decision factors
                - Fundamentals would provide context but are not required

                ACTION: Trade based on technical confluence
                """.strip(),
            )

        fund_bias = fundamental_data.bias
        fund_score = fundamental_data.fundamental_score

        # Check alignment
        if technical_bias == fund_bias and technical_bias != BiasType.NEUTRAL:
            # ALIGNED - Tech and fundamentals agree
            strength = "STRONG" if technical_confidence > 0.7 else "MODERATE"

            interpretation = f"""
            STRONG ALIGNMENT: Technical and Fundamental both {technical_bias.value}

            Technical: {technical_bias.value} ({technical_confidence:.1%} confidence)
            Fundamental: {fund_bias.value} ({fund_score:.0f} points)

            LAG ASSESSMENT:
            Fundamentals are LAGGING but supportive. This suggests:
            - The technical move is backed by underlying business strength
            - Institutional investors likely positioned based on fundamentals
            - Lower risk of fundamental surprise reversing technical trend

            INTERPRETATION:
            - High conviction trade setup
            - Fundamentals provide context for "why" price is moving
            - Technical analysis still leads entry/exit timing
            - Consider larger position size due to alignment

            ACTION: Follow technical signals with confidence
            """.strip()

        elif technical_bias != fund_bias and technical_bias != BiasType.NEUTRAL and fund_bias != BiasType.NEUTRAL:
            # DIVERGENT - Tech and fundamentals disagree
            strength = "WEAK"

            if technical_bias == BiasType.BULLISH and fund_bias == BiasType.BEARISH:
                lag_explanation = """
                Technical shows BULLISH but fundamentals are BEARISH.

                LAG ASSESSMENT:
                This is a CRITICAL divergence. Fundamentals are lagging, but here's the nuance:

                Scenario 1: Relief Rally (Most Likely)
                - Fundamentals are bearish (business is weak)
                - Technical shows short-term bullish setup
                - This is likely a TEMPORARY bounce in a bear market
                - Smart money may be using rally to exit positions

                Scenario 2: Early Reversal (Less Likely)
                - Technical is leading a reversal
                - Fundamentals haven't caught up yet
                - Next earnings could surprise positively
                - Price is pricing in future improvement

                RISK:
                - If fundamentals are correct, this bullish move is temporary
                - Be prepared for bearish continuation after bounce
                - Use TIGHT stops and smaller position size
                """

            else:  # Technical Bearish, Fundamental Bullish
                lag_explanation = """
                Technical shows BEARISH but fundamentals are BULLISH.

                LAG ASSESSMENT:
                This is an important divergence. Here's how to interpret:

                Scenario 1: Short-Term Correction (Most Likely)
                - Fundamentals are bullish (business is strong)
                - Technical shows short-term bearish setup
                - This is likely a HEALTHY pullback in a bull market
                - Smart money may be using dip to add positions

                Scenario 2: Early Bear Market (Less Likely)
                - Technical is leading a reversal lower
                - Fundamentals haven't deteriorated yet
                - Next earnings could surprise negatively
                - Price is pricing in future weakness

                OPPORTUNITY:
                - If fundamentals are correct, this dip is a buying opportunity
                - Look for technical reversal signals at support
                - Higher timeframe may still be bullish
                - This could be entry point for longer-term holders
                """

            interpretation = f"""
            DIVERGENCE: Technical {technical_bias.value} vs Fundamental {fund_bias.value}

            Technical: {technical_bias.value} ({technical_confidence:.1%} confidence)
            Fundamental: {fund_bias.value} ({fund_score:.0f} points)

            {lag_explanation}

            TRADING IMPLICATION:
            - Lower confidence setup due to conflict
            - Reduce position size (50% of normal)
            - Watch for resolution (either technical confirms fund, or fund data updates)
            - Multiple timeframe analysis is CRITICAL here

            ACTION: Trade cautiously, follow technical but be ready to exit quickly
            """.strip()

        else:
            # One is NEUTRAL
            strength = "MODERATE"
            interpretation = f"""
            PARTIAL ALIGNMENT: Technical {technical_bias.value}, Fundamental {fund_bias.value}

            Technical: {technical_bias.value} ({technical_confidence:.1%} confidence)
            Fundamental: {fund_bias.value} ({fund_score:.0f} points)

            LAG ASSESSMENT:
            Fundamentals are neutral/mixed, providing little directional insight.

            INTERPRETATION:
            - Fundamentals neither support nor contradict technical
            - Proceed primarily on technical analysis
            - Normal position sizing acceptable
            - Monitor for fundamental updates that could provide clarity

            ACTION: Follow technical signals
            """.strip()

        # Build data dictionary
        data = {
            "technical_bias": technical_bias.value,
            "technical_confidence": technical_confidence,
            "fundamental_bias": fund_bias.value,
            "fundamental_score": fund_score,
            "aligned": technical_bias == fund_bias,
        }

        if fundamental_data.earnings_per_share:
            data["eps"] = fundamental_data.earnings_per_share
        if fundamental_data.pe_ratio:
            data["pe_ratio"] = fundamental_data.pe_ratio
        if fundamental_data.revenue_growth:
            data["revenue_growth"] = fundamental_data.revenue_growth

        return FundamentalAlignment(
            direction=technical_bias if technical_confidence > 0.6 else BiasType.NEUTRAL,
            strength=strength,
            lag_assessment=self._build_lag_assessment(technical_bias, fund_bias),
            data=data,
            interpretation=interpretation,
        )

    def _build_lag_assessment(
        self,
        technical_bias: BiasType,
        fundamental_bias: BiasType,
    ) -> str:
        """Build detailed lag assessment."""
        if technical_bias == fundamental_bias:
            return """
            FUNDAMENTAL LAG: Supportive

            Fundamentals are LAGGING indicators but currently aligned with technical.
            This suggests the technical move is backed by underlying business/economic strength.
            However, remember that price LEADS fundamentals, not the other way around.

            What this means:
            - Fundamentals explain "why" the technical move is happening
            - Don't expect fundamentals to predict the next move
            - Technical analysis still determines entry/exit timing
            """.strip()
        else:
            return """
            FUNDAMENTAL LAG: Divergent

            Fundamentals are LAGGING indicators and currently divergent from technical.
            This is NORMAL and happens frequently. Price discounts future expectations.

            What this means:
            - Price may be pricing in future that fundamentals haven't shown yet
            - OR price is experiencing short-term technical move (correction/bounce)
            - Technical analysis takes priority for trading decisions
            - Watch for fundamental data updates that could resolve divergence
            """.strip()

    def _build_no_fundamental_lag_assessment(self) -> str:
        """Build lag assessment when no fundamental data available."""
        return """
        FUNDAMENTAL LAG: Not Applicable

        No fundamental data available for this symbol.

        What this means:
        - Trade purely on technical analysis
        - This is common for crypto, forex, and some stocks
        - Technical confluence is sufficient for high-confidence trades
        - Fundamentals would provide context but are not required
        """.strip()

    def estimate_fundamental_lag(
        self,
        fundamental_data: Optional[FundamentalData],
    ) -> Dict[str, Any]:
        """
        Estimate how old the fundamental data is.

        Args:
            fundamental_data: Fundamental data

        Returns:
            Dictionary with lag information
        """
        if not fundamental_data or not fundamental_data.data_timestamp:
            return {
                "lag_days": None,
                "lag_description": "No fundamental data available",
                "freshness": "UNKNOWN",
            }

        now = datetime.utcnow()
        lag = now - fundamental_data.data_timestamp
        lag_days = lag.days

        if lag_days < 1:
            freshness = "FRESH"
            description = "Less than 1 day old"
        elif lag_days < 7:
            freshness = "RECENT"
            description = f"{lag_days} days old"
        elif lag_days < 30:
            freshness = "MODERATE"
            description = f"{lag_days} days old (may be outdated)"
        elif lag_days < 90:
            freshness = "STALE"
            description = f"{lag_days} days old (likely outdated)"
        else:
            freshness = "VERY_STALE"
            description = f"{lag_days} days old (definitely outdated)"

        return {
            "lag_days": lag_days,
            "lag_description": description,
            "freshness": freshness,
            "data_timestamp": fundamental_data.data_timestamp,
        }
