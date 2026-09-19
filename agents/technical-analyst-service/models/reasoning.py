"""Data models for intelligent reasoning system."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum


class BiasType(str, Enum):
    """Trading bias types."""
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"
    MIXED = "MIXED"


class ActionType(str, Enum):
    """Trading action types."""
    BUY = "BUY"
    SELL = "SELL"
    WAIT = "WAIT"
    CLOSE = "CLOSE"


class AlignmentType(str, Enum):
    """Alignment between different analysis types."""
    ALIGNED = "ALIGNED"
    DIVERGENT = "DIVERGENT"
    NEUTRAL = "NEUTRAL"


class ConfidenceLevel(str, Enum):
    """Confidence levels."""
    VERY_LOW = "VERY_LOW"      # 0-20%
    LOW = "LOW"                # 20-40%
    MODERATE = "MODERATE"      # 40-60%
    HIGH = "HIGH"              # 60-80%
    VERY_HIGH = "VERY_HIGH"    # 80-100%


@dataclass
class Evidence:
    """Single piece of evidence supporting an argument."""

    source: str  # e.g., "4H Timeframe", "Earnings Report"
    type: str    # e.g., "SMC Pattern", "Fundamental Data"
    description: str
    score: float
    confidence: float
    timestamp: Optional[datetime] = None


@dataclass
class Argument:
    """
    Logical argument with claim, evidence, and reasoning.

    Follows structure:
    - Claim: What we're arguing
    - Evidence: Supporting data
    - Reasoning: Why evidence supports claim
    - Confidence: How strong is this argument
    """

    claim: str
    evidence: List[Evidence]
    reasoning: str
    confidence: float  # 0.0 to 1.0
    timeframe: Optional[str] = None

    @property
    def evidence_count(self) -> int:
        """Number of evidence pieces."""
        return len(self.evidence)

    @property
    def total_evidence_score(self) -> float:
        """Sum of all evidence scores."""
        return sum(e.score for e in self.evidence)

    @property
    def confidence_level(self) -> ConfidenceLevel:
        """Categorize confidence level."""
        if self.confidence < 0.2:
            return ConfidenceLevel.VERY_LOW
        elif self.confidence < 0.4:
            return ConfidenceLevel.LOW
        elif self.confidence < 0.6:
            return ConfidenceLevel.MODERATE
        elif self.confidence < 0.8:
            return ConfidenceLevel.HIGH
        else:
            return ConfidenceLevel.VERY_HIGH


@dataclass
class PatternEvidence:
    """Evidence from pattern detection."""

    pattern_type: str  # e.g., "EQH", "IFC", "Impulse Wave"
    pattern_name: str
    description: str
    score: float
    strength: float
    index: int
    price_level: float
    is_bullish: bool
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TimeframeAnalysis:
    """Analysis for a single timeframe."""

    timeframe: str
    bias: BiasType
    bullish_score: float
    bearish_score: float
    confidence: float

    # Pattern detections
    smc_patterns: List[PatternEvidence]
    elliott_patterns: List[PatternEvidence]
    indicators: Dict[str, float]
    divergences: List[PatternEvidence]

    # Key levels identified
    key_support_levels: List[float]
    key_resistance_levels: List[float]

    # Arguments for this timeframe
    primary_argument: Optional[Argument] = None

    @property
    def net_score(self) -> float:
        """Net score (bullish - bearish)."""
        return self.bullish_score - self.bearish_score

    @property
    def total_patterns(self) -> int:
        """Total patterns detected."""
        return (len(self.smc_patterns) +
                len(self.elliott_patterns) +
                len(self.divergences))


@dataclass
class MultiTimeframeAnalysis:
    """Analysis across all timeframes."""

    symbol: str
    timeframe_analyses: Dict[str, TimeframeAnalysis]
    overall_bias: BiasType
    overall_confidence: float

    # Confluence analysis
    timeframe_agreement: float  # % of timeframes that agree
    strongest_timeframe: str
    weakest_timeframe: str

    # Cross-timeframe patterns
    aligned_patterns: List[str]  # Patterns appearing on multiple TFs
    conflicting_signals: List[str]

    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def bullish_timeframes(self) -> int:
        """Count of bullish timeframes."""
        return sum(1 for ta in self.timeframe_analyses.values()
                  if ta.bias == BiasType.BULLISH)

    @property
    def bearish_timeframes(self) -> int:
        """Count of bearish timeframes."""
        return sum(1 for ta in self.timeframe_analyses.values()
                  if ta.bias == BiasType.BEARISH)


@dataclass
class FundamentalData:
    """Fundamental analysis data."""

    symbol: str
    asset_type: str  # 'stock', 'crypto', 'forex'

    # Stock-specific
    earnings_per_share: Optional[float] = None
    pe_ratio: Optional[float] = None
    revenue_growth: Optional[float] = None
    profit_margin: Optional[float] = None

    # Sentiment
    analyst_rating: Optional[str] = None
    analyst_target: Optional[float] = None
    institutional_ownership: Optional[float] = None

    # Macro (for forex/indices)
    interest_rate: Optional[float] = None
    gdp_growth: Optional[float] = None
    inflation_rate: Optional[float] = None

    # Custom data
    custom_data: Dict[str, Any] = field(default_factory=dict)

    # Scoring
    fundamental_score: float = 0.0
    bias: BiasType = BiasType.NEUTRAL

    data_timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class FundamentalAlignment:
    """Alignment between technical and fundamental analysis."""

    direction: BiasType
    strength: str  # "WEAK", "MODERATE", "STRONG"
    lag_assessment: str  # Detailed explanation of fundamental lag
    data: Dict[str, Any]

    interpretation: str  # How to interpret the alignment/divergence


@dataclass
class RiskAssessment:
    """Risk assessment for trading decision."""

    primary_risks: List[str]
    risk_level: str  # "LOW", "MODERATE", "HIGH"
    mitigation: str
    max_drawdown_estimate: Optional[float] = None
    probability_of_loss: Optional[float] = None

    # Event risks
    upcoming_events: List[str] = field(default_factory=list)
    event_impact: str = "UNKNOWN"


@dataclass
class Target:
    """Price target with reasoning."""

    price: float
    reasoning: str
    percent_exit: int  # % of position to exit at this target
    probability: Optional[float] = None
    timeframe_estimate: Optional[str] = None


@dataclass
class EntryPlan:
    """Complete entry plan with reasoning."""

    entry_price: float
    entry_reasoning: str

    stop_loss: float
    stop_reasoning: str

    targets: List[Target]

    risk_reward: float
    position_size_recommendation: Optional[float] = None

    # Timing
    entry_trigger: str  # What should trigger entry
    invalidation: str   # What invalidates the setup


@dataclass
class TradingDecision:
    """
    Final trading decision with complete justification.

    This is the output of the intelligent reasoning system.
    """

    symbol: str
    action: ActionType
    confidence: float  # 0.0 to 1.0

    # Arguments
    primary_arguments: List[Argument]
    counter_arguments: List[Argument]

    # Alignment
    fundamental_alignment: Optional[FundamentalAlignment] = None

    # Risk
    risk_assessment: RiskAssessment = None

    # Execution plan
    entry_plan: Optional[EntryPlan] = None

    # Supporting data
    timeframe_summary: Dict[str, TimeframeAnalysis] = field(default_factory=dict)

    # Confidence breakdown
    confidence_breakdown: Dict[str, float] = field(default_factory=dict)

    # Reasoning narrative
    executive_summary: str = ""
    detailed_reasoning: str = ""

    # Metadata
    generated_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    @property
    def confidence_level(self) -> ConfidenceLevel:
        """Categorize confidence level."""
        if self.confidence < 0.2:
            return ConfidenceLevel.VERY_LOW
        elif self.confidence < 0.4:
            return ConfidenceLevel.LOW
        elif self.confidence < 0.6:
            return ConfidenceLevel.MODERATE
        elif self.confidence < 0.8:
            return ConfidenceLevel.HIGH
        else:
            return ConfidenceLevel.VERY_HIGH

    @property
    def should_trade(self) -> bool:
        """Whether confidence is high enough to trade."""
        return self.confidence >= 0.6 and self.action in [ActionType.BUY, ActionType.SELL]


@dataclass
class Conflict:
    """Conflict between different analyses."""

    conflict_type: str
    description: str
    timeframe_1: str
    bias_1: BiasType
    timeframe_2: str
    bias_2: BiasType
    resolution: str
    recommended_action: str


@dataclass
class ConfluenceAnalysis:
    """Analysis of confluence across multiple sources."""

    total_sources: int
    agreeing_sources: int
    disagreeing_sources: int
    confluence_percentage: float

    strongest_confluence: List[str]
    weakest_confluence: List[str]

    interpretation: str
