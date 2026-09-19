"""Decision framework for intelligent trading decisions."""

import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta

from ..models.reasoning import (
    TradingDecision,
    ActionType,
    BiasType,
    Argument,
    Evidence,
    FundamentalAlignment,
    RiskAssessment,
    EntryPlan,
    Target,
    MultiTimeframeAnalysis,
    FundamentalData,
    ConfluenceAnalysis,
)

logger = logging.getLogger(__name__)


class DecisionFramework:
    """
    Makes final trading decisions with complete justification.

    Decision Process:
    1. Analyze multi-timeframe technical confluence
    2. Build primary arguments with evidence
    3. Identify counter-arguments (critical for risk)
    4. Evaluate fundamental alignment (with lag acknowledgment)
    5. Assess risks comprehensively
    6. Build entry plan with reasoning
    7. Calculate final confidence
    8. Make decision with full justification

    Output: TradingDecision with complete reasoning narrative
    """

    def make_decision(
        self,
        mtf_analysis: MultiTimeframeAnalysis,
        primary_argument: Argument,
        counter_arguments: List[Argument],
        confluence_analysis: ConfluenceAnalysis,
        fundamental_alignment: Optional[FundamentalAlignment],
        current_price: float,
    ) -> TradingDecision:
        """
        Make final trading decision with complete justification.

        Args:
            mtf_analysis: Multi-timeframe analysis
            primary_argument: Primary argument for the trade
            counter_arguments: Arguments against the trade
            confluence_analysis: Confluence analysis
            fundamental_alignment: Fundamental alignment (if available)
            current_price: Current market price

        Returns:
            TradingDecision with full justification
        """
        logger.info(f"Making trading decision for {mtf_analysis.symbol}...")

        symbol = mtf_analysis.symbol
        bias = mtf_analysis.overall_bias
        confidence = mtf_analysis.overall_confidence

        # Determine action
        action = self._determine_action(
            bias,
            confidence,
            confluence_analysis.confluence_percentage,
            fundamental_alignment,
        )

        # Assess risks
        risk_assessment = self._assess_risks(
            mtf_analysis,
            counter_arguments,
            confluence_analysis,
        )

        # Build entry plan (if action is BUY/SELL)
        entry_plan = None
        if action in [ActionType.BUY, ActionType.SELL]:
            entry_plan = self._build_entry_plan(
                symbol,
                action,
                current_price,
                mtf_analysis,
                confidence,
            )

        # Calculate confidence breakdown
        confidence_breakdown = self._calculate_confidence_breakdown(
            mtf_analysis,
            confluence_analysis,
            fundamental_alignment,
            len(counter_arguments),
        )

        # Build executive summary
        executive_summary = self._build_executive_summary(
            symbol,
            action,
            bias,
            confidence,
            confluence_analysis,
            primary_argument,
            counter_arguments,
        )

        # Build detailed reasoning
        detailed_reasoning = self._build_detailed_reasoning(
            mtf_analysis,
            primary_argument,
            counter_arguments,
            confluence_analysis,
            fundamental_alignment,
            risk_assessment,
            entry_plan,
        )

        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(hours=4)  # Analysis valid for 4 hours

        decision = TradingDecision(
            symbol=symbol,
            action=action,
            confidence=confidence,
            primary_arguments=[primary_argument],
            counter_arguments=counter_arguments,
            fundamental_alignment=fundamental_alignment,
            risk_assessment=risk_assessment,
            entry_plan=entry_plan,
            timeframe_summary={
                tf: analysis for tf, analysis in mtf_analysis.timeframe_analyses.items()
            },
            confidence_breakdown=confidence_breakdown,
            executive_summary=executive_summary,
            detailed_reasoning=detailed_reasoning,
            generated_at=datetime.utcnow(),
            expires_at=expires_at,
        )

        logger.info(f"Decision: {action.value} {symbol} with {confidence:.1%} confidence")
        return decision

    def _determine_action(
        self,
        bias: BiasType,
        confidence: float,
        confluence: float,
        fundamental_alignment: Optional[FundamentalAlignment],
    ) -> ActionType:
        """
        Determine trading action.

        Decision criteria:
        - High confidence (>80%) + High confluence (>80%) = Strong action
        - Moderate confidence (>60%) + Moderate confluence (>60%) = Action
        - Low confidence or confluence = WAIT
        - Fundamental divergence = Reduce conviction
        """
        # Adjust confidence based on fundamental alignment
        adjusted_confidence = confidence

        if fundamental_alignment:
            if fundamental_alignment.strength == "WEAK":
                # Fundamental divergence reduces confidence
                adjusted_confidence *= 0.85
            elif fundamental_alignment.strength == "STRONG":
                # Fundamental alignment increases confidence slightly
                adjusted_confidence *= 1.05
                adjusted_confidence = min(adjusted_confidence, 1.0)

        # Make decision
        if adjusted_confidence >= 0.75 and confluence >= 0.75:
            if bias == BiasType.BULLISH:
                return ActionType.BUY
            elif bias == BiasType.BEARISH:
                return ActionType.SELL
            else:
                return ActionType.WAIT

        elif adjusted_confidence >= 0.60 and confluence >= 0.60:
            if bias == BiasType.BULLISH:
                return ActionType.BUY
            elif bias == BiasType.BEARISH:
                return ActionType.SELL
            else:
                return ActionType.WAIT

        else:
            return ActionType.WAIT

    def _assess_risks(
        self,
        mtf_analysis: MultiTimeframeAnalysis,
        counter_arguments: List[Argument],
        confluence_analysis: ConfluenceAnalysis,
    ) -> RiskAssessment:
        """
        Comprehensive risk assessment.

        Args:
            mtf_analysis: Multi-timeframe analysis
            counter_arguments: Counter-arguments
            confluence_analysis: Confluence analysis

        Returns:
            RiskAssessment
        """
        primary_risks = []

        # Risk 1: Counter-arguments
        if len(counter_arguments) > 0:
            primary_risks.append(
                f"{len(counter_arguments)} timeframe(s) show contradicting signals - "
                f"potential for reversal or ranging market"
            )

        # Risk 2: Low confluence
        if confluence_analysis.confluence_percentage < 0.7:
            primary_risks.append(
                f"Low timeframe agreement ({confluence_analysis.confluence_percentage:.0%}) - "
                f"risk of whipsaw and false signals"
            )

        # Risk 3: Conflicting patterns
        if mtf_analysis.conflicting_signals:
            primary_risks.append(
                f"{len(mtf_analysis.conflicting_signals)} conflicting signals detected - "
                f"market may be transitioning"
            )

        # Risk 4: Weak primary timeframe
        strongest_tf = mtf_analysis.strongest_timeframe
        weakest_tf = mtf_analysis.weakest_timeframe

        if weakest_tf == strongest_tf:
            primary_risks.append(
                f"Weakest timeframe ({weakest_tf}) is also the strongest - "
                f"low overall signal strength"
            )

        # Determine risk level
        if len(primary_risks) >= 3:
            risk_level = "HIGH"
        elif len(primary_risks) >= 2:
            risk_level = "MODERATE"
        elif len(primary_risks) >= 1:
            risk_level = "LOW"
        else:
            risk_level = "VERY_LOW"

        # Build mitigation strategy
        mitigation = self._build_risk_mitigation(
            risk_level,
            confluence_analysis.confluence_percentage,
            len(counter_arguments),
        )

        # Estimate probabilities
        max_drawdown_estimate = self._estimate_max_drawdown(
            risk_level,
            confluence_analysis.confluence_percentage,
        )

        probability_of_loss = self._estimate_loss_probability(
            mtf_analysis.overall_confidence,
            confluence_analysis.confluence_percentage,
        )

        return RiskAssessment(
            primary_risks=primary_risks if primary_risks else ["No major risks identified"],
            risk_level=risk_level,
            mitigation=mitigation,
            max_drawdown_estimate=max_drawdown_estimate,
            probability_of_loss=probability_of_loss,
            upcoming_events=[],  # TODO: Integrate calendar data
            event_impact="UNKNOWN",
        )

    def _build_risk_mitigation(
        self,
        risk_level: str,
        confluence: float,
        counter_arg_count: int,
    ) -> str:
        """Build risk mitigation strategy."""
        if risk_level == "VERY_LOW":
            return """
            Risk Level: VERY LOW

            Mitigation Strategy:
            - Use standard position sizing (1-2% risk per trade)
            - Normal stop loss placement (below key support/above key resistance)
            - Can hold through minor volatility
            - Take partial profits at first target (30%)
            - Move stop to breakeven after first target hit
            """.strip()

        elif risk_level == "LOW":
            return """
            Risk Level: LOW

            Mitigation Strategy:
            - Use standard position sizing (1-2% risk per trade)
            - Tight stop loss placement (below recent swing/above recent swing)
            - Monitor for early reversal signs
            - Take partial profits early (50% at first target)
            - Move stop to breakeven quickly
            - Be ready to exit if confluence deteriorates
            """.strip()

        elif risk_level == "MODERATE":
            return """
            Risk Level: MODERATE

            Mitigation Strategy:
            - REDUCE position size (0.5-1% risk per trade)
            - Very tight stop loss (just below/above recent candle)
            - Take quick profits (70% at first target)
            - Don't hold through volatility - exit and re-enter
            - Watch for timeframe alignment to improve or deteriorate
            - If counter-arguments strengthen, exit immediately
            """.strip()

        else:  # HIGH
            return """
            Risk Level: HIGH

            Mitigation Strategy:
            - STRONGLY CONSIDER NOT TRADING
            - If trading, use micro position size (0.25% risk or less)
            - Extremely tight stop loss
            - Take profits at 100% at first target (full exit)
            - This is a scalp, not a swing trade
            - Watch every candle - be ready to exit at any sign of reversal
            - Alternatively: WAIT for better setup with higher confluence
            """.strip()

    def _estimate_max_drawdown(
        self,
        risk_level: str,
        confluence: float,
    ) -> float:
        """Estimate maximum expected drawdown."""
        base_drawdown = 0.02  # 2% base

        if risk_level == "HIGH":
            return base_drawdown * 3.0  # 6%
        elif risk_level == "MODERATE":
            return base_drawdown * 2.0  # 4%
        elif risk_level == "LOW":
            return base_drawdown * 1.5  # 3%
        else:
            return base_drawdown  # 2%

    def _estimate_loss_probability(
        self,
        confidence: float,
        confluence: float,
    ) -> float:
        """Estimate probability of loss."""
        # Higher confidence and confluence = lower probability of loss
        combined = (confidence + confluence) / 2
        return 1.0 - combined

    def _build_entry_plan(
        self,
        symbol: str,
        action: ActionType,
        current_price: float,
        mtf_analysis: MultiTimeframeAnalysis,
        confidence: float,
    ) -> EntryPlan:
        """
        Build entry plan with targets and stops.

        Args:
            symbol: Trading symbol
            action: BUY or SELL
            current_price: Current market price
            mtf_analysis: Multi-timeframe analysis
            confidence: Overall confidence

        Returns:
            EntryPlan with entry, stop, and targets
        """
        # Get key levels from strongest timeframe
        strongest_tf_analysis = mtf_analysis.timeframe_analyses[mtf_analysis.strongest_timeframe]

        support_levels = strongest_tf_analysis.key_support_levels
        resistance_levels = strongest_tf_analysis.key_resistance_levels

        if action == ActionType.BUY:
            # Entry: Current price or pullback to support
            entry_price = current_price
            entry_reasoning = f"""
            Entry at current price: ${current_price:.2f}

            Reasoning:
            - Strong bullish bias across {mtf_analysis.bullish_timeframes}/{len(mtf_analysis.timeframe_analyses)} timeframes
            - Confidence: {confidence:.1%}
            - Entry on confirmation of bullish structure

            Alternative: Wait for pullback to nearest support at ${support_levels[0]:.2f if support_levels else current_price * 0.98}
            """.strip()

            # Stop: Below nearest support
            if support_levels:
                stop_loss = support_levels[0] * 0.995  # 0.5% below support
                stop_reasoning = f"Stop below key support at ${support_levels[0]:.2f}"
            else:
                stop_loss = current_price * 0.97  # 3% stop
                stop_reasoning = "Stop 3% below entry (no clear support identified)"

            # Targets: Resistance levels
            targets = []
            if resistance_levels:
                # Target 1: First resistance (30% exit)
                targets.append(Target(
                    price=resistance_levels[0],
                    reasoning=f"First resistance level from {mtf_analysis.strongest_timeframe} analysis",
                    percent_exit=30,
                    probability=0.75,
                    timeframe_estimate=f"{mtf_analysis.strongest_timeframe} timeframe",
                ))

                # Target 2: Second resistance (40% exit)
                if len(resistance_levels) > 1:
                    targets.append(Target(
                        price=resistance_levels[1],
                        reasoning=f"Second resistance level",
                        percent_exit=40,
                        probability=0.50,
                        timeframe_estimate=f"Extended {mtf_analysis.strongest_timeframe} move",
                    ))

                # Target 3: Third resistance (30% exit)
                if len(resistance_levels) > 2:
                    targets.append(Target(
                        price=resistance_levels[2],
                        reasoning=f"Major resistance level",
                        percent_exit=30,
                        probability=0.30,
                        timeframe_estimate="Multiple timeframe resistance",
                    ))
            else:
                # Default targets based on % moves
                targets = [
                    Target(
                        price=current_price * 1.02,
                        reasoning="2% move target (conservative)",
                        percent_exit=50,
                        probability=0.70,
                    ),
                    Target(
                        price=current_price * 1.05,
                        reasoning="5% move target (moderate)",
                        percent_exit=30,
                        probability=0.50,
                    ),
                    Target(
                        price=current_price * 1.10,
                        reasoning="10% move target (aggressive)",
                        percent_exit=20,
                        probability=0.30,
                    ),
                ]

        else:  # SELL
            # Entry: Current price or bounce to resistance
            entry_price = current_price
            entry_reasoning = f"""
            Entry at current price: ${current_price:.2f}

            Reasoning:
            - Strong bearish bias across {mtf_analysis.bearish_timeframes}/{len(mtf_analysis.timeframe_analyses)} timeframes
            - Confidence: {confidence:.1%}
            - Entry on confirmation of bearish structure

            Alternative: Wait for bounce to nearest resistance at ${resistance_levels[0]:.2f if resistance_levels else current_price * 1.02}
            """.strip()

            # Stop: Above nearest resistance
            if resistance_levels:
                stop_loss = resistance_levels[0] * 1.005  # 0.5% above resistance
                stop_reasoning = f"Stop above key resistance at ${resistance_levels[0]:.2f}"
            else:
                stop_loss = current_price * 1.03  # 3% stop
                stop_reasoning = "Stop 3% above entry (no clear resistance identified)"

            # Targets: Support levels
            targets = []
            if support_levels:
                # Target 1: First support (30% exit)
                targets.append(Target(
                    price=support_levels[0],
                    reasoning=f"First support level from {mtf_analysis.strongest_timeframe} analysis",
                    percent_exit=30,
                    probability=0.75,
                    timeframe_estimate=f"{mtf_analysis.strongest_timeframe} timeframe",
                ))

                # Target 2: Second support (40% exit)
                if len(support_levels) > 1:
                    targets.append(Target(
                        price=support_levels[1],
                        reasoning=f"Second support level",
                        percent_exit=40,
                        probability=0.50,
                        timeframe_estimate=f"Extended {mtf_analysis.strongest_timeframe} move",
                    ))

                # Target 3: Third support (30% exit)
                if len(support_levels) > 2:
                    targets.append(Target(
                        price=support_levels[2],
                        reasoning=f"Major support level",
                        percent_exit=30,
                        probability=0.30,
                        timeframe_estimate="Multiple timeframe support",
                    ))
            else:
                # Default targets based on % moves
                targets = [
                    Target(
                        price=current_price * 0.98,
                        reasoning="2% move target (conservative)",
                        percent_exit=50,
                        probability=0.70,
                    ),
                    Target(
                        price=current_price * 0.95,
                        reasoning="5% move target (moderate)",
                        percent_exit=30,
                        probability=0.50,
                    ),
                    Target(
                        price=current_price * 0.90,
                        reasoning="10% move target (aggressive)",
                        percent_exit=20,
                        probability=0.30,
                    ),
                ]

        # Calculate risk/reward
        if action == ActionType.BUY:
            risk = entry_price - stop_loss
            reward = targets[0].price - entry_price if targets else entry_price * 0.02
        else:
            risk = stop_loss - entry_price
            reward = entry_price - targets[0].price if targets else entry_price * 0.02

        risk_reward = reward / risk if risk > 0 else 0

        # Entry trigger
        entry_trigger = f"""
        Enter when:
        - Price confirms {action.value} with candle close
        - Volume confirms move (above average)
        - No major news events pending
        """.strip()

        # Invalidation
        if action == ActionType.BUY:
            invalidation = f"Setup invalidated if price closes below ${stop_loss:.2f}"
        else:
            invalidation = f"Setup invalidated if price closes above ${stop_loss:.2f}"

        # Position size recommendation
        if confidence >= 0.8:
            position_size = 1.5  # 1.5% risk
        elif confidence >= 0.6:
            position_size = 1.0  # 1% risk
        else:
            position_size = 0.5  # 0.5% risk

        return EntryPlan(
            entry_price=entry_price,
            entry_reasoning=entry_reasoning,
            stop_loss=stop_loss,
            stop_reasoning=stop_reasoning,
            targets=targets,
            risk_reward=risk_reward,
            position_size_recommendation=position_size,
            entry_trigger=entry_trigger,
            invalidation=invalidation,
        )

    def _calculate_confidence_breakdown(
        self,
        mtf_analysis: MultiTimeframeAnalysis,
        confluence_analysis: ConfluenceAnalysis,
        fundamental_alignment: Optional[FundamentalAlignment],
        counter_arg_count: int,
    ) -> Dict[str, float]:
        """Calculate detailed confidence breakdown."""
        breakdown = {
            "technical_confidence": mtf_analysis.overall_confidence,
            "timeframe_agreement": mtf_analysis.timeframe_agreement,
            "confluence_score": confluence_analysis.confluence_percentage,
        }

        if fundamental_alignment:
            if fundamental_alignment.strength == "STRONG":
                breakdown["fundamental_boost"] = 0.05
            elif fundamental_alignment.strength == "WEAK":
                breakdown["fundamental_penalty"] = -0.10

        if counter_arg_count > 0:
            breakdown["counter_argument_penalty"] = -0.05 * counter_arg_count

        return breakdown

    def _build_executive_summary(
        self,
        symbol: str,
        action: ActionType,
        bias: BiasType,
        confidence: float,
        confluence_analysis: ConfluenceAnalysis,
        primary_argument: Argument,
        counter_arguments: List[Argument],
    ) -> str:
        """Build executive summary."""
        return f"""
═══════════════════════════════════════════════════════
TRADING DECISION - {symbol}
═══════════════════════════════════════════════════════

ACTION: {action.value}
BIAS: {bias.value}
CONFIDENCE: {confidence:.1%}
CONFLUENCE: {confluence_analysis.confluence_percentage:.0%}

PRIMARY THESIS:
{primary_argument.claim}

KEY EVIDENCE:
{chr(10).join(f"• {e.description}" for e in primary_argument.evidence[:5])}

COUNTER-ARGUMENTS:
{chr(10).join(f"• {ca.claim}" for ca in counter_arguments[:3]) if counter_arguments else "• None identified"}

BOTTOM LINE:
{self._build_bottom_line(action, confidence, confluence_analysis.confluence_percentage)}

═══════════════════════════════════════════════════════
        """.strip()

    def _build_bottom_line(
        self,
        action: ActionType,
        confidence: float,
        confluence: float,
    ) -> str:
        """Build bottom line recommendation."""
        if action == ActionType.WAIT:
            return "WAIT for better setup - insufficient confidence or confluence"

        if confidence >= 0.80 and confluence >= 0.80:
            return f"{action.value} with HIGH conviction - multiple timeframes aligned"
        elif confidence >= 0.60:
            return f"{action.value} with MODERATE conviction - use reduced position size"
        else:
            return f"Marginal {action.value} signal - consider waiting for higher confidence"

    def _build_detailed_reasoning(
        self,
        mtf_analysis: MultiTimeframeAnalysis,
        primary_argument: Argument,
        counter_arguments: List[Argument],
        confluence_analysis: ConfluenceAnalysis,
        fundamental_alignment: Optional[FundamentalAlignment],
        risk_assessment: RiskAssessment,
        entry_plan: Optional[EntryPlan],
    ) -> str:
        """Build complete detailed reasoning."""
        sections = []

        # Section 1: Multi-Timeframe Analysis
        sections.append("=== MULTI-TIMEFRAME ANALYSIS ===\n")
        sections.append(primary_argument.reasoning)

        # Section 2: Confluence Analysis
        sections.append("\n\n=== CONFLUENCE ANALYSIS ===\n")
        sections.append(confluence_analysis.interpretation)

        # Section 3: Counter-Arguments
        if counter_arguments:
            sections.append("\n\n=== COUNTER-ARGUMENTS ===\n")
            for ca in counter_arguments:
                sections.append(f"\n{ca.claim}:\n{ca.reasoning}")

        # Section 4: Fundamental Alignment
        if fundamental_alignment:
            sections.append("\n\n=== FUNDAMENTAL ALIGNMENT ===\n")
            sections.append(fundamental_alignment.interpretation)

        # Section 5: Risk Assessment
        sections.append("\n\n=== RISK ASSESSMENT ===\n")
        sections.append(f"Risk Level: {risk_assessment.risk_level}\n")
        sections.append(f"\nPrimary Risks:\n")
        for risk in risk_assessment.primary_risks:
            sections.append(f"• {risk}\n")
        sections.append(f"\n{risk_assessment.mitigation}")

        # Section 6: Entry Plan
        if entry_plan:
            sections.append("\n\n=== ENTRY PLAN ===\n")
            sections.append(f"{entry_plan.entry_reasoning}\n")
            sections.append(f"\nStop Loss: ${entry_plan.stop_loss:.2f}\n")
            sections.append(f"Reasoning: {entry_plan.stop_reasoning}\n")
            sections.append(f"\nTargets:\n")
            for i, target in enumerate(entry_plan.targets, 1):
                sections.append(
                    f"{i}. ${target.price:.2f} ({target.percent_exit}% exit) - "
                    f"{target.reasoning}\n"
                )
            sections.append(f"\nRisk/Reward: {entry_plan.risk_reward:.2f}")

        return "".join(sections)
