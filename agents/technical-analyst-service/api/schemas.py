"""API request and response schemas."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class SignalResponse(BaseModel):
    """Signal response schema."""

    id: str
    symbol: str
    timeframe: str
    signal_type: str
    status: str
    entry_price: float
    current_price: Optional[float]
    target_price: Optional[float]
    stop_loss: Optional[float]
    confidence: float
    strategy: Optional[str]
    description: Optional[str]
    generated_at: datetime
    expires_at: Optional[datetime]


class GenerateSignalRequest(BaseModel):
    """Request to generate signal for symbol."""

    symbol: str = Field(..., description="Trading symbol")
    timeframe: str = Field(default="1h", description="Timeframe for analysis")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    timestamp: datetime
    version: str = "1.0.0"


class IndicatorResponse(BaseModel):
    """Indicator values response."""

    symbol: str
    timeframe: str
    timestamp: datetime
    indicators: dict


class WaveResponse(BaseModel):
    """Elliott Wave response."""

    wave_number: int
    start_idx: int
    end_idx: int
    start_price: float
    end_price: float
    magnitude: float
    is_up: bool


class FibonacciLevelResponse(BaseModel):
    """Fibonacci level response."""

    level: float
    price: float
    level_type: str  # 'retracement' or 'extension'


class ElliottWaveResponse(BaseModel):
    """Elliott Wave pattern response."""

    symbol: str
    timeframe: str
    timestamp: datetime
    pattern_type: str  # 'impulse', 'leading_diagonal', 'ending_diagonal', 'zigzag', 'flat', 'triangle'
    direction: str  # 'bullish' or 'bearish'
    current_wave: int
    confidence: float
    waves: List[WaveResponse]
    fibonacci_levels: List[FibonacciLevelResponse]
    is_complete: bool
    subtype: Optional[str] = None  # 'expanded_flat', 'running_flat', 'contracting_triangle', etc.
    is_truncated: bool = False  # True if Wave 5 is truncated
    extended_wave: Optional[int] = None  # Which wave is extended (1, 3, or 5)


class DivergenceResponse(BaseModel):
    """RSI Divergence response."""

    divergence_type: str
    start_idx: int
    end_idx: int
    price_start: float
    price_end: float
    rsi_start: float
    rsi_end: float
    confirmed: bool
    confidence: float
    description: str
    is_bullish: bool
    is_reversal: bool


class DivergencesResponse(BaseModel):
    """All divergences response."""

    symbol: str
    timeframe: str
    timestamp: datetime
    divergences: List[DivergenceResponse]


class BreakOfStructureResponse(BaseModel):
    """Break of Structure response."""

    structure_type: str
    break_idx: int
    break_price: float
    previous_level: float
    strength: float
    volume_confirmation: bool
    description: str
    is_bullish: bool


class FairValueGapResponse(BaseModel):
    """Fair Value Gap response."""

    direction: str
    start_idx: int
    end_idx: int
    gap_high: float
    gap_low: float
    gap_size: float
    midpoint: float
    filled: bool
    strength: float


class SupplyDemandZoneResponse(BaseModel):
    """Supply/Demand zone response."""

    zone_type: str
    start_idx: int
    end_idx: int
    zone_high: float
    zone_low: float
    zone_size: float
    midpoint: float
    strength: float
    active: bool
    touches: int
    is_supply: bool


class LiquiditySweepResponse(BaseModel):
    """Liquidity Sweep response."""

    sweep_type: str
    sweep_idx: int
    sweep_level: float
    description: str
    is_bullish: bool


class EqualHighsLowsResponse(BaseModel):
    """Equal Highs/Lows (EQH/EQL) response."""

    eq_type: str  # 'equal_highs' or 'equal_lows'
    level: float
    count: int
    indices: List[int]
    swept: bool
    sweep_idx: Optional[int]
    strength: float
    is_resistance: bool  # True for EQH, False for EQL


class OrderFlowResponse(BaseModel):
    """Order Flow (OF) response."""

    of_type: str  # 'bullish_of' or 'bearish_of'
    candle_idx: int
    zone_high: float
    zone_low: float
    strength: float
    active: bool
    description: str
    is_bullish: bool


class InstitutionalFundingCandleResponse(BaseModel):
    """Institutional Funding Candle (IFC) response."""

    ifc_type: str  # 'bullish_ifc' or 'bearish_ifc'
    candle_idx: int
    swept_level: float
    wick_extreme: float
    close_price: float
    strength: float
    reversal_confirmed: bool
    description: str
    is_bullish: bool


class FalseBreakOfStructureResponse(BaseModel):
    """False Break of Structure (FBOS) response."""

    fbos_type: str
    bos_idx: int
    invalidation_idx: int
    break_level: float
    previous_level: float
    description: str
    trap_signal: str  # 'bullish' or 'bearish'


class SessionLiquidityResponse(BaseModel):
    """Session Liquidity response."""

    session_name: str  # 'asia', 'london', 'new_york'
    session_date: str
    session_high: float
    session_low: float
    high_swept: bool
    low_swept: bool
    range_size: float


class DailyLiquidityResponse(BaseModel):
    """Daily Liquidity (PDH/PDL, PWH/PWL) response."""

    pdh: Optional[float] = None  # Previous Day High
    pdl: Optional[float] = None  # Previous Day Low
    pwh: Optional[float] = None  # Previous Week High
    pwl: Optional[float] = None  # Previous Week Low


class SmartMoneyTrapResponse(BaseModel):
    """Smart Money Trap (SMT) response."""

    smt_type: str
    bos_idx: int
    pullback_idx: int
    trap_level: float
    description: str
    signal: str  # 'bullish' or 'bearish'


class InducementResponse(BaseModel):
    """Inducement (IDM) response."""

    idm_type: str
    inducement_idx: int
    reversal_idx: int
    inducement_price: float
    move_percentage: float
    description: str
    signal: str  # 'bullish' or 'bearish'


class SmartMoneyResponse(BaseModel):
    """Smart Money Concepts response - Complete 14-Pattern Implementation."""

    symbol: str
    timeframe: str
    timestamp: datetime

    # Core 6 patterns
    structure_breaks: List[BreakOfStructureResponse]
    fair_value_gaps: List[FairValueGapResponse]
    supply_demand_zones: List[SupplyDemandZoneResponse]
    order_blocks: List[SupplyDemandZoneResponse]
    liquidity_sweeps: List[LiquiditySweepResponse]

    # New 8 patterns
    equal_highs_lows: List[EqualHighsLowsResponse]
    order_flow: List[OrderFlowResponse]
    institutional_funding_candles: List[InstitutionalFundingCandleResponse]
    false_break_of_structure: List[FalseBreakOfStructureResponse]
    session_liquidity: List[SessionLiquidityResponse]
    daily_liquidity: DailyLiquidityResponse
    smart_money_traps: List[SmartMoneyTrapResponse]
    inducements: List[InducementResponse]


# === Intelligent Analysis Response Models ===


class EvidenceResponse(BaseModel):
    """Evidence supporting an argument."""

    source: str
    type: str
    description: str
    score: float
    confidence: float
    timestamp: Optional[datetime] = None


class ArgumentResponse(BaseModel):
    """Logical argument with claim, evidence, and reasoning."""

    claim: str
    evidence: List[EvidenceResponse]
    reasoning: str
    confidence: float
    timeframe: Optional[str] = None
    evidence_count: int
    total_evidence_score: float


class ConflictResponse(BaseModel):
    """Conflict between timeframes."""

    conflict_type: str
    description: str
    timeframe_1: str
    bias_1: str
    timeframe_2: str
    bias_2: str
    resolution: str
    recommended_action: str


class ConfluenceAnalysisResponse(BaseModel):
    """Confluence analysis across timeframes."""

    total_sources: int
    agreeing_sources: int
    disagreeing_sources: int
    confluence_percentage: float
    strongest_confluence: List[str]
    weakest_confluence: List[str]
    interpretation: str


class FundamentalAlignmentResponse(BaseModel):
    """Fundamental alignment with technical analysis."""

    direction: str
    strength: str
    lag_assessment: str
    data: Dict[str, Any]
    interpretation: str


class RiskAssessmentResponse(BaseModel):
    """Risk assessment for trading decision."""

    primary_risks: List[str]
    risk_level: str
    mitigation: str
    max_drawdown_estimate: Optional[float] = None
    probability_of_loss: Optional[float] = None
    upcoming_events: List[str] = []
    event_impact: str = "UNKNOWN"


class TargetResponse(BaseModel):
    """Price target with reasoning."""

    price: float
    reasoning: str
    percent_exit: int
    probability: Optional[float] = None
    timeframe_estimate: Optional[str] = None


class EntryPlanResponse(BaseModel):
    """Entry plan with targets and stops."""

    entry_price: float
    entry_reasoning: str
    stop_loss: float
    stop_reasoning: str
    targets: List[TargetResponse]
    risk_reward: float
    position_size_recommendation: Optional[float] = None
    entry_trigger: str
    invalidation: str


class TradingDecisionResponse(BaseModel):
    """Complete trading decision with full justification."""

    symbol: str
    action: str  # BUY, SELL, WAIT, CLOSE
    confidence: float
    confidence_level: str  # VERY_LOW, LOW, MODERATE, HIGH, VERY_HIGH

    # Arguments
    primary_arguments: List[ArgumentResponse]
    counter_arguments: List[ArgumentResponse]

    # Alignment
    fundamental_alignment: Optional[FundamentalAlignmentResponse] = None

    # Risk
    risk_assessment: RiskAssessmentResponse

    # Execution
    entry_plan: Optional[EntryPlanResponse] = None

    # Confidence breakdown
    confidence_breakdown: Dict[str, float]

    # Reasoning
    executive_summary: str
    detailed_reasoning: str

    # Metadata
    generated_at: datetime
    expires_at: Optional[datetime] = None
    should_trade: bool
