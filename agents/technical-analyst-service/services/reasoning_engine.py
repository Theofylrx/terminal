"""Reasoning engine for evidence-based trading decisions."""

import logging
from typing import List, Dict, Optional
from datetime import datetime

from ..models.reasoning import (
    Argument,
    Evidence,
    Conflict,
    ConfluenceAnalysis,
    TimeframeAnalysis,
    MultiTimeframeAnalysis,
    BiasType,
    PatternEvidence,
)

logger = logging.getLogger(__name__)


class ReasoningEngine:
    """
    Provides intelligent reasoning and argumentation.

    Doesn't just score - explains WHY and provides EVIDENCE.
    Builds logical arguments (claim → evidence → reasoning → confidence).
    """

    def build_multi_timeframe_argument(
        self,
        mtf_analysis: MultiTimeframeAnalysis,
    ) -> Argument:
        """
        Build primary argument across all timeframes.

        Returns:
            Argument with claim, evidence, reasoning, and confidence
        """
        logger.info("Building multi-timeframe argument...")

        bias = mtf_analysis.overall_bias
        analyses = mtf_analysis.timeframe_analyses

        # Count timeframe agreement
        bullish_tfs = [tf for tf, a in analyses.items() if a.bias == BiasType.BULLISH]
        bearish_tfs = [tf for tf, a in analyses.items() if a.bias == BiasType.BEARISH]

        # Gather evidence from agreeing timeframes
        evidence = []

        if bias == BiasType.BULLISH:
            claim = f"Strong bullish bias across {len(bullish_tfs)}/{len(analyses)} timeframes"

            for tf in bullish_tfs:
                analysis = analyses[tf]
                evidence.append(Evidence(
                    source=f"{tf} Timeframe",
                    type="Multi-Timeframe Analysis",
                    description=f"{tf}: Bullish ({analysis.bullish_score:.0f} pts)",
                    score=analysis.bullish_score,
                    confidence=analysis.confidence,
                ))

        elif bias == BiasType.BEARISH:
            claim = f"Strong bearish bias across {len(bearish_tfs)}/{len(analyses)} timeframes"

            for tf in bearish_tfs:
                analysis = analyses[tf]
                evidence.append(Evidence(
                    source=f"{tf} Timeframe",
                    type="Multi-Timeframe Analysis",
                    description=f"{tf}: Bearish ({analysis.bearish_score:.0f} pts)",
                    score=analysis.bearish_score,
                    confidence=analysis.confidence,
                ))

        else:
            claim = "Mixed signals across timeframes - no clear bias"
            evidence = [
                Evidence(
                    source="Multi-Timeframe Analysis",
                    type="Conflicting Signals",
                    description=f"{len(bullish_tfs)} bullish vs {len(bearish_tfs)} bearish",
                    score=0,
                    confidence=0.5,
                )
            ]

        # Build detailed reasoning
        reasoning = self._build_multi_timeframe_reasoning(
            mtf_analysis, bias, bullish_tfs, bearish_tfs
        )

        # Calculate confidence
        confidence = mtf_analysis.overall_confidence

        logger.info(f"Multi-timeframe argument: {claim} ({confidence:.1%} confidence)")

        return Argument(
            claim=claim,
            evidence=evidence,
            reasoning=reasoning,
            confidence=confidence,
        )

    def _build_multi_timeframe_reasoning(
        self,
        mtf_analysis: MultiTimeframeAnalysis,
        bias: BiasType,
        bullish_tfs: List[str],
        bearish_tfs: List[str],
    ) -> str:
        """Build detailed reasoning for multi-timeframe bias."""
        analyses = mtf_analysis.timeframe_analyses

        reasoning = f"""
{bias.value.capitalize()} bias is supported by cross-timeframe analysis:

TIMEFRAME BREAKDOWN:
"""

        # Add each timeframe's contribution
        for tf in sorted(analyses.keys(), key=lambda x: self._timeframe_priority(x)):
            analysis = analyses[tf]

            # Get top 3 patterns
            top_patterns = sorted(
                analysis.smc_patterns + analysis.elliott_patterns,
                key=lambda x: x.score,
                reverse=True
            )[:3]

            reasoning += f"\n{tf} ({analysis.bias.value}):\n"
            for pattern in top_patterns:
                reasoning += f"  - {pattern.pattern_name}: {pattern.description} ({pattern.score:.0f} pts)\n"

        # Add confluence analysis
        reasoning += f"""

CROSS-TIMEFRAME CONFLUENCE:
- {len(bullish_tfs)} timeframes bullish
- {len(bearish_tfs)} timeframes bearish
- Agreement: {mtf_analysis.timeframe_agreement:.0%}

"""

        # Add aligned patterns
        if mtf_analysis.aligned_patterns:
            reasoning += "ALIGNED PATTERNS (appearing on multiple timeframes):\n"
            for pattern in mtf_analysis.aligned_patterns[:5]:
                reasoning += f"  - {pattern}\n"

        # Add interpretation
        if bias == BiasType.BULLISH:
            reasoning += "\nINTERPRETATION:\n"
            reasoning += "Multiple timeframes show bullish structure, indicating institutional buying.\n"
            reasoning += "Higher timeframe support provides confidence for bullish positions.\n"

        elif bias == BiasType.BEARISH:
            reasoning += "\nINTERPRETATION:\n"
            reasoning += "Multiple timeframes show bearish structure, indicating institutional selling.\n"
            reasoning += "Higher timeframe resistance provides confidence for bearish positions.\n"

        else:
            reasoning += "\nINTERPRETATION:\n"
            reasoning += "Conflicting signals suggest we're in a transition period or ranging market.\n"
            reasoning += "Wait for clearer alignment before taking directional positions.\n"

        return reasoning.strip()

    def identify_counter_arguments(
        self,
        mtf_analysis: MultiTimeframeAnalysis,
    ) -> List[Argument]:
        """
        Identify arguments AGAINST the primary bias.

        This is critical for risk assessment and nuanced decision-making.
        """
        logger.info("Identifying counter-arguments...")

        counter_args = []
        bias = mtf_analysis.overall_bias
        analyses = mtf_analysis.timeframe_analyses

        # Find timeframes that disagree
        disagreeing_tfs = [
            (tf, analysis) for tf, analysis in analyses.items()
            if analysis.bias != bias and analysis.bias != BiasType.NEUTRAL
        ]

        for tf, analysis in disagreeing_tfs:
            # Build counter-argument
            evidence = []

            # Get top patterns from disagreeing timeframe
            top_patterns = sorted(
                analysis.smc_patterns + analysis.elliott_patterns,
                key=lambda x: x.score,
                reverse=True
            )[:3]

            for pattern in top_patterns:
                evidence.append(Evidence(
                    source=f"{tf} Timeframe",
                    type="Contradicting Pattern",
                    description=f"{pattern.pattern_name}: {pattern.description}",
                    score=pattern.score,
                    confidence=pattern.strength,
                ))

            # Build reasoning
            if analysis.bias == BiasType.BULLISH:
                claim = f"{tf} shows bullish signals contradicting primary bias"
                interpretation = f"""
                {tf} timeframe shows bullish structure with {analysis.bullish_score:.0f} points.
                This could indicate:
                1. Short-term correction/bounce in overall bearish trend
                2. Early reversal signal (lower timeframe leads)
                3. Ranging market on this timeframe

                Risk: If this is early reversal, primary bearish thesis may be invalidating.
                """
            else:
                claim = f"{tf} shows bearish signals contradicting primary bias"
                interpretation = f"""
                {tf} timeframe shows bearish structure with {analysis.bearish_score:.0f} points.
                This could indicate:
                1. Short-term pullback in overall bullish trend
                2. Early reversal signal (lower timeframe leads)
                3. Ranging market on this timeframe

                Risk: If this is early reversal, primary bullish thesis may be invalidating.
                """

            counter_args.append(Argument(
                claim=claim,
                evidence=evidence,
                reasoning=interpretation.strip(),
                confidence=analysis.confidence,
                timeframe=tf,
            ))

        logger.info(f"Found {len(counter_args)} counter-arguments")

        return counter_args

    def evaluate_confluence(
        self,
        mtf_analysis: MultiTimeframeAnalysis,
    ) -> ConfluenceAnalysis:
        """
        Evaluate confluence ACROSS timeframes.

        Returns:
            ConfluenceAnalysis with agreement metrics and interpretation
        """
        analyses = mtf_analysis.timeframe_analyses
        bias = mtf_analysis.overall_bias

        total = len(analyses)
        agreeing = sum(1 for a in analyses.values() if a.bias == bias)
        disagreeing = total - agreeing

        confluence_pct = agreeing / total if total > 0 else 0

        # Find strongest confluence areas
        strongest = []
        if mtf_analysis.aligned_patterns:
            strongest = mtf_analysis.aligned_patterns[:5]

        # Find weakest confluence areas
        weakest = mtf_analysis.conflicting_signals[:5] if mtf_analysis.conflicting_signals else []

        # Build interpretation
        if confluence_pct >= 0.8:
            interpretation = f"""
            VERY HIGH CONFLUENCE ({confluence_pct:.0%})

            {agreeing}/{total} timeframes agree with {bias.value} bias.
            This represents strong institutional positioning across multiple timeframes.

            Trading Implication:
            - High confidence in {bias.value.lower()} direction
            - Multiple timeframe alignment reduces risk
            - Good candidate for larger position size

            Patterns appearing on multiple timeframes:
            {chr(10).join(f"- {p}" for p in strongest) if strongest else "None"}
            """

        elif confluence_pct >= 0.6:
            interpretation = f"""
            MODERATE CONFLUENCE ({confluence_pct:.0%})

            {agreeing}/{total} timeframes agree with {bias.value} bias.
            Majority support but some divergence exists.

            Trading Implication:
            - Moderate confidence in {bias.value.lower()} direction
            - Watch for timeframe alignment to improve or deteriorate
            - Consider smaller position size due to mixed signals

            Conflicting signals:
            {chr(10).join(f"- {c}" for c in weakest) if weakest else "None"}
            """

        else:
            interpretation = f"""
            LOW CONFLUENCE ({confluence_pct:.0%})

            Only {agreeing}/{total} timeframes agree with {bias.value} bias.
            Significant divergence across timeframes.

            Trading Implication:
            - Low confidence - likely ranging or transitional market
            - High risk of whipsaw
            - Recommend WAIT for clearer alignment
            - If trading, use very small position sizes

            Major conflicts:
            {chr(10).join(f"- {c}" for c in weakest) if weakest else "None"}
            """

        return ConfluenceAnalysis(
            total_sources=total,
            agreeing_sources=agreeing,
            disagreeing_sources=disagreeing,
            confluence_percentage=confluence_pct,
            strongest_confluence=strongest,
            weakest_confluence=weakest,
            interpretation=interpretation.strip(),
        )

    def identify_conflicts(
        self,
        mtf_analysis: MultiTimeframeAnalysis,
    ) -> List[Conflict]:
        """
        Identify and analyze conflicts between timeframes.

        Returns list of conflicts with resolutions.
        """
        conflicts = []
        analyses = mtf_analysis.timeframe_analyses
        timeframes = sorted(analyses.keys(), key=self._timeframe_priority)

        # Check each timeframe pair
        for i, tf1 in enumerate(timeframes):
            for tf2 in timeframes[i+1:]:
                a1 = analyses[tf1]
                a2 = analyses[tf2]

                # Skip if both neutral or same bias
                if a1.bias == a2.bias or a1.bias == BiasType.NEUTRAL or a2.bias == BiasType.NEUTRAL:
                    continue

                # We have a conflict
                description = f"{tf1} shows {a1.bias.value} while {tf2} shows {a2.bias.value}"

                # Resolve based on timeframe hierarchy
                tf1_priority = self._timeframe_priority(tf1)
                tf2_priority = self._timeframe_priority(tf2)

                if tf1_priority < tf2_priority:  # tf1 is higher timeframe
                    resolution = f"""
                    {tf1} (higher timeframe) takes precedence.

                    {tf2} (lower timeframe) showing opposite direction likely indicates:
                    - Short-term correction within {tf1} trend
                    - Entry opportunity to join {tf1} trend
                    - Temporary counter-trend move

                    Resolution: Follow {tf1} {a1.bias.value} bias, use {tf2} for entry timing.
                    """

                    recommended_action = f"Trade {a1.bias.value.lower()}, use {tf2} for entry"

                else:  # tf2 is higher timeframe
                    resolution = f"""
                    {tf2} (higher timeframe) takes precedence.

                    {tf1} (lower timeframe) showing opposite direction likely indicates:
                    - Short-term correction within {tf2} trend
                    - Entry opportunity to join {tf2} trend
                    - Temporary counter-trend move

                    Resolution: Follow {tf2} {a2.bias.value} bias, use {tf1} for entry timing.
                    """

                    recommended_action = f"Trade {a2.bias.value.lower()}, use {tf1} for entry"

                conflicts.append(Conflict(
                    conflict_type="Timeframe Divergence",
                    description=description,
                    timeframe_1=tf1,
                    bias_1=a1.bias,
                    timeframe_2=tf2,
                    bias_2=a2.bias,
                    resolution=resolution.strip(),
                    recommended_action=recommended_action,
                ))

        return conflicts

    def _timeframe_priority(self, timeframe: str) -> int:
        """
        Get timeframe priority (lower number = higher priority/longer timeframe).

        1MO > 1W > 1D > 4H > 1H > 15M
        """
        priority = {
            "1MO": 1,
            "1W": 2,
            "1D": 3,
            "4H": 4,
            "1H": 5,
            "15M": 6,
            "5M": 7,
            "1M": 8,
        }
        return priority.get(timeframe, 99)

    def build_executive_summary(
        self,
        mtf_analysis: MultiTimeframeAnalysis,
        primary_argument: Argument,
        counter_arguments: List[Argument],
        confluence: ConfluenceAnalysis,
    ) -> str:
        """
        Build executive summary for trading decision.

        This is the "TLDR" that traders can read quickly.
        """
        bias = mtf_analysis.overall_bias
        symbol = mtf_analysis.symbol

        summary = f"""
═══════════════════════════════════════════════════════
EXECUTIVE SUMMARY - {symbol}
═══════════════════════════════════════════════════════

OVERALL BIAS: {bias.value}
CONFIDENCE: {mtf_analysis.overall_confidence:.1%}
CONFLUENCE: {confluence.confluence_percentage:.0%} timeframe agreement

PRIMARY THESIS:
{primary_argument.claim}

SUPPORTING EVIDENCE:
{chr(10).join(f"- {e.description}" for e in primary_argument.evidence[:5])}

COUNTER-ARGUMENTS:
{chr(10).join(f"- {ca.claim}" for ca in counter_arguments[:3]) if counter_arguments else "None identified"}

RECOMMENDATION:
{self._build_quick_recommendation(bias, mtf_analysis.overall_confidence, confluence.confluence_percentage)}

═══════════════════════════════════════════════════════
"""
        return summary.strip()

    def _build_quick_recommendation(
        self,
        bias: BiasType,
        confidence: float,
        confluence: float,
    ) -> str:
        """Build quick trading recommendation."""
        if confidence >= 0.8 and confluence >= 0.8:
            if bias == BiasType.BULLISH:
                return "STRONG BUY - High confidence, high confluence"
            elif bias == BiasType.BEARISH:
                return "STRONG SELL - High confidence, high confluence"
            else:
                return "WAIT - Mixed signals despite high confluence"

        elif confidence >= 0.6 and confluence >= 0.6:
            if bias == BiasType.BULLISH:
                return "BUY - Moderate confidence, consider smaller position"
            elif bias == BiasType.BEARISH:
                return "SELL - Moderate confidence, consider smaller position"
            else:
                return "WAIT - Insufficient directional clarity"

        else:
            return "WAIT - Low confidence or low confluence, high risk of whipsaw"
