"""Evidence collector for comprehensive trading analysis."""

import logging
from typing import List, Dict, Optional
from datetime import datetime

from ..models.reasoning import (
    Evidence,
    PatternEvidence,
    TimeframeAnalysis,
    MultiTimeframeAnalysis,
    FundamentalData,
)

logger = logging.getLogger(__name__)


class EvidenceCollector:
    """
    Collects and organizes evidence from all sources.

    Technical Evidence:
    - SMC patterns (14 patterns)
    - Elliott Wave patterns
    - Technical indicators
    - Divergences

    Fundamental Evidence:
    - Earnings data
    - Financial metrics
    - Analyst ratings
    - Market sentiment
    """

    def collect_technical_evidence(
        self,
        timeframe_analysis: TimeframeAnalysis,
    ) -> List[Evidence]:
        """
        Collect all technical evidence from a single timeframe analysis.

        Args:
            timeframe_analysis: Analysis for single timeframe

        Returns:
            List of Evidence objects
        """
        evidence = []
        tf = timeframe_analysis.timeframe

        # Collect SMC pattern evidence
        for pattern in timeframe_analysis.smc_patterns:
            evidence.append(Evidence(
                source=f"{tf} Timeframe",
                type="SMC Pattern",
                description=f"{pattern.pattern_name}: {pattern.description}",
                score=pattern.score,
                confidence=pattern.strength,
                timestamp=datetime.utcnow(),
            ))

        # Collect Elliott Wave evidence
        for pattern in timeframe_analysis.elliott_patterns:
            evidence.append(Evidence(
                source=f"{tf} Timeframe",
                type="Elliott Wave Pattern",
                description=f"{pattern.pattern_name}: {pattern.description}",
                score=pattern.score,
                confidence=pattern.strength,
                timestamp=datetime.utcnow(),
            ))

        # Collect divergence evidence
        for divergence in timeframe_analysis.divergences:
            evidence.append(Evidence(
                source=f"{tf} Timeframe",
                type="Divergence",
                description=f"{divergence.pattern_name}: {divergence.description}",
                score=divergence.score,
                confidence=divergence.strength,
                timestamp=datetime.utcnow(),
            ))

        # Collect indicator evidence (only significant ones)
        if timeframe_analysis.indicators:
            # RSI extremes
            rsi = timeframe_analysis.indicators.get('rsi', 50)
            if rsi > 70:
                evidence.append(Evidence(
                    source=f"{tf} Timeframe",
                    type="Technical Indicator",
                    description=f"RSI Overbought: {rsi:.1f} (>70)",
                    score=-15,  # Bearish
                    confidence=0.7,
                    timestamp=datetime.utcnow(),
                ))
            elif rsi < 30:
                evidence.append(Evidence(
                    source=f"{tf} Timeframe",
                    type="Technical Indicator",
                    description=f"RSI Oversold: {rsi:.1f} (<30)",
                    score=15,  # Bullish
                    confidence=0.7,
                    timestamp=datetime.utcnow(),
                ))

            # MACD signal
            macd = timeframe_analysis.indicators.get('macd', 0)
            macd_signal = timeframe_analysis.indicators.get('macd_signal', 0)
            if macd > macd_signal and macd > 0:
                evidence.append(Evidence(
                    source=f"{tf} Timeframe",
                    type="Technical Indicator",
                    description=f"MACD Bullish: {macd:.4f} > Signal",
                    score=10,
                    confidence=0.6,
                    timestamp=datetime.utcnow(),
                ))
            elif macd < macd_signal and macd < 0:
                evidence.append(Evidence(
                    source=f"{tf} Timeframe",
                    type="Technical Indicator",
                    description=f"MACD Bearish: {macd:.4f} < Signal",
                    score=-10,
                    confidence=0.6,
                    timestamp=datetime.utcnow(),
                ))

            # Bollinger Bands
            bb_upper = timeframe_analysis.indicators.get('bb_upper')
            bb_lower = timeframe_analysis.indicators.get('bb_lower')
            close = timeframe_analysis.indicators.get('close')

            if bb_upper and bb_lower and close:
                if close > bb_upper:
                    evidence.append(Evidence(
                        source=f"{tf} Timeframe",
                        type="Technical Indicator",
                        description=f"Price above Upper Bollinger Band (overbought)",
                        score=-12,
                        confidence=0.65,
                        timestamp=datetime.utcnow(),
                    ))
                elif close < bb_lower:
                    evidence.append(Evidence(
                        source=f"{tf} Timeframe",
                        type="Technical Indicator",
                        description=f"Price below Lower Bollinger Band (oversold)",
                        score=12,
                        confidence=0.65,
                        timestamp=datetime.utcnow(),
                    ))

        logger.info(f"Collected {len(evidence)} pieces of technical evidence from {tf}")
        return evidence

    def collect_multi_timeframe_evidence(
        self,
        mtf_analysis: MultiTimeframeAnalysis,
    ) -> Dict[str, List[Evidence]]:
        """
        Collect evidence from all timeframes.

        Args:
            mtf_analysis: Multi-timeframe analysis

        Returns:
            Dictionary mapping timeframe to evidence list
        """
        all_evidence = {}

        for tf, analysis in mtf_analysis.timeframe_analyses.items():
            evidence = self.collect_technical_evidence(analysis)
            all_evidence[tf] = evidence

        logger.info(f"Collected evidence from {len(all_evidence)} timeframes")
        return all_evidence

    def collect_fundamental_evidence(
        self,
        fundamental_data: Optional[FundamentalData],
    ) -> List[Evidence]:
        """
        Collect fundamental evidence.

        Note: Fundamentals are LAGGING indicators but provide context.

        Args:
            fundamental_data: Fundamental data if available

        Returns:
            List of fundamental evidence
        """
        evidence = []

        if not fundamental_data:
            logger.info("No fundamental data available")
            return evidence

        symbol = fundamental_data.symbol

        # Earnings evidence
        if fundamental_data.earnings_per_share:
            eps = fundamental_data.earnings_per_share
            if eps > 0:
                evidence.append(Evidence(
                    source="Fundamental Analysis",
                    type="Earnings",
                    description=f"{symbol} EPS: ${eps:.2f} (Positive earnings)",
                    score=15,
                    confidence=0.5,  # Lower confidence due to lag
                    timestamp=fundamental_data.data_timestamp,
                ))
            else:
                evidence.append(Evidence(
                    source="Fundamental Analysis",
                    type="Earnings",
                    description=f"{symbol} EPS: ${eps:.2f} (Negative earnings)",
                    score=-15,
                    confidence=0.5,
                    timestamp=fundamental_data.data_timestamp,
                ))

        # P/E Ratio evidence
        if fundamental_data.pe_ratio:
            pe = fundamental_data.pe_ratio
            if pe < 15:
                evidence.append(Evidence(
                    source="Fundamental Analysis",
                    type="Valuation",
                    description=f"{symbol} P/E: {pe:.1f} (Undervalued)",
                    score=10,
                    confidence=0.5,
                    timestamp=fundamental_data.data_timestamp,
                ))
            elif pe > 30:
                evidence.append(Evidence(
                    source="Fundamental Analysis",
                    type="Valuation",
                    description=f"{symbol} P/E: {pe:.1f} (Overvalued)",
                    score=-10,
                    confidence=0.5,
                    timestamp=fundamental_data.data_timestamp,
                ))

        # Revenue growth evidence
        if fundamental_data.revenue_growth:
            growth = fundamental_data.revenue_growth
            if growth > 0.15:  # 15%+ growth
                evidence.append(Evidence(
                    source="Fundamental Analysis",
                    type="Growth",
                    description=f"{symbol} Revenue Growth: {growth:.1%} (Strong growth)",
                    score=12,
                    confidence=0.5,
                    timestamp=fundamental_data.data_timestamp,
                ))
            elif growth < 0:
                evidence.append(Evidence(
                    source="Fundamental Analysis",
                    type="Growth",
                    description=f"{symbol} Revenue Growth: {growth:.1%} (Declining)",
                    score=-12,
                    confidence=0.5,
                    timestamp=fundamental_data.data_timestamp,
                ))

        # Profit margin evidence
        if fundamental_data.profit_margin:
            margin = fundamental_data.profit_margin
            if margin > 0.20:  # 20%+ margin
                evidence.append(Evidence(
                    source="Fundamental Analysis",
                    type="Profitability",
                    description=f"{symbol} Profit Margin: {margin:.1%} (Healthy margins)",
                    score=10,
                    confidence=0.5,
                    timestamp=fundamental_data.data_timestamp,
                ))
            elif margin < 0:
                evidence.append(Evidence(
                    source="Fundamental Analysis",
                    type="Profitability",
                    description=f"{symbol} Profit Margin: {margin:.1%} (Unprofitable)",
                    score=-10,
                    confidence=0.5,
                    timestamp=fundamental_data.data_timestamp,
                ))

        # Analyst rating evidence
        if fundamental_data.analyst_rating:
            rating = fundamental_data.analyst_rating.upper()
            if rating in ["STRONG BUY", "BUY"]:
                evidence.append(Evidence(
                    source="Fundamental Analysis",
                    type="Analyst Opinion",
                    description=f"{symbol} Analyst Rating: {rating}",
                    score=8,
                    confidence=0.4,  # Analysts can be wrong
                    timestamp=fundamental_data.data_timestamp,
                ))
            elif rating in ["SELL", "STRONG SELL"]:
                evidence.append(Evidence(
                    source="Fundamental Analysis",
                    type="Analyst Opinion",
                    description=f"{symbol} Analyst Rating: {rating}",
                    score=-8,
                    confidence=0.4,
                    timestamp=fundamental_data.data_timestamp,
                ))

        # Institutional ownership evidence
        if fundamental_data.institutional_ownership:
            ownership = fundamental_data.institutional_ownership
            if ownership > 0.70:  # 70%+ institutional
                evidence.append(Evidence(
                    source="Fundamental Analysis",
                    type="Ownership",
                    description=f"{symbol} Institutional Ownership: {ownership:.1%} (High institutional interest)",
                    score=8,
                    confidence=0.5,
                    timestamp=fundamental_data.data_timestamp,
                ))
            elif ownership < 0.30:
                evidence.append(Evidence(
                    source="Fundamental Analysis",
                    type="Ownership",
                    description=f"{symbol} Institutional Ownership: {ownership:.1%} (Low institutional interest)",
                    score=-5,
                    confidence=0.5,
                    timestamp=fundamental_data.data_timestamp,
                ))

        # Macro factors (for forex/indices)
        if fundamental_data.interest_rate is not None:
            rate = fundamental_data.interest_rate
            evidence.append(Evidence(
                source="Fundamental Analysis",
                type="Macro",
                description=f"Interest Rate: {rate:.2%}",
                score=5 if rate > 0.02 else -5,  # Higher rates = currency strength
                confidence=0.6,
                timestamp=fundamental_data.data_timestamp,
            ))

        if fundamental_data.gdp_growth is not None:
            gdp = fundamental_data.gdp_growth
            if gdp > 0.03:  # 3%+ growth
                evidence.append(Evidence(
                    source="Fundamental Analysis",
                    type="Macro",
                    description=f"GDP Growth: {gdp:.1%} (Strong economy)",
                    score=10,
                    confidence=0.6,
                    timestamp=fundamental_data.data_timestamp,
                ))
            elif gdp < 0:
                evidence.append(Evidence(
                    source="Fundamental Analysis",
                    type="Macro",
                    description=f"GDP Growth: {gdp:.1%} (Recession)",
                    score=-10,
                    confidence=0.6,
                    timestamp=fundamental_data.data_timestamp,
                ))

        logger.info(f"Collected {len(evidence)} pieces of fundamental evidence")
        return evidence

    def prioritize_evidence(
        self,
        evidence: List[Evidence],
        min_score: float = 10.0,
        min_confidence: float = 0.5,
    ) -> List[Evidence]:
        """
        Filter and prioritize evidence.

        Args:
            evidence: List of all evidence
            min_score: Minimum absolute score to include
            min_confidence: Minimum confidence to include

        Returns:
            Filtered and sorted evidence (highest impact first)
        """
        # Filter by score and confidence
        filtered = [
            e for e in evidence
            if abs(e.score) >= min_score and e.confidence >= min_confidence
        ]

        # Sort by impact (score * confidence)
        filtered.sort(
            key=lambda e: abs(e.score) * e.confidence,
            reverse=True
        )

        logger.info(f"Prioritized {len(filtered)} high-impact evidence from {len(evidence)} total")
        return filtered

    def aggregate_evidence_scores(
        self,
        evidence: List[Evidence],
    ) -> Dict[str, float]:
        """
        Aggregate evidence into bullish/bearish scores.

        Args:
            evidence: List of evidence

        Returns:
            Dictionary with bullish_score, bearish_score, net_score, confidence
        """
        bullish_score = sum(e.score for e in evidence if e.score > 0)
        bearish_score = abs(sum(e.score for e in evidence if e.score < 0))
        net_score = bullish_score - bearish_score

        # Weighted confidence (higher scores get more weight)
        if evidence:
            total_weight = sum(abs(e.score) for e in evidence)
            weighted_confidence = sum(
                abs(e.score) * e.confidence for e in evidence
            ) / total_weight if total_weight > 0 else 0
        else:
            weighted_confidence = 0

        return {
            "bullish_score": bullish_score,
            "bearish_score": bearish_score,
            "net_score": net_score,
            "confidence": weighted_confidence,
            "evidence_count": len(evidence),
        }
