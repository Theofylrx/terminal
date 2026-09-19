"""Trading Decision Model - Complete Storage for Intelligent Analysis."""

from sqlalchemy import Column, String, Float, DateTime, Text, JSON, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.orm import relationship
from enum import Enum
from datetime import datetime
from typing import Dict, Any

from .base_model import BaseModel


class ActionType(str, Enum):
    """Trading action types."""
    BUY = "BUY"
    SELL = "SELL"
    WAIT = "WAIT"
    CLOSE = "CLOSE"


class ConfidenceLevel(str, Enum):
    """Confidence levels."""
    VERY_LOW = "VERY_LOW"      # 0-20%
    LOW = "LOW"                # 20-40%
    MODERATE = "MODERATE"      # 40-60%
    HIGH = "HIGH"              # 60-80%
    VERY_HIGH = "VERY_HIGH"    # 80-100%


class TradingDecision(BaseModel):
    """
    Complete trading decision with full justification.

    Stores EVERYTHING from the intelligent reasoning system:
    - Multi-timeframe analysis
    - Evidence and arguments
    - Risk assessment
    - Entry plans
    - Complete reasoning narrative

    This provides full audit trail and historical analysis.
    """

    __tablename__ = "trading_decisions"

    # User ownership - CRITICAL for multi-user isolation
    user_id = Column(String(36), nullable=False, index=True)

    # Basic information
    symbol = Column(String(20), nullable=False, index=True)
    action = Column(SQLEnum(ActionType), nullable=False)
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0
    confidence_level = Column(SQLEnum(ConfidenceLevel), nullable=False)

    # Decision metadata
    generated_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, nullable=True)
    should_trade = Column(String(10), nullable=False)  # "true" or "false"

    # Arguments (stored as JSON)
    # Structure: [{"claim": "...", "evidence": [...], "reasoning": "...", "confidence": 0.85}]
    primary_arguments = Column(JSON, nullable=False)
    counter_arguments = Column(JSON, nullable=False)

    # Fundamental alignment (stored as JSON)
    # Structure: {"direction": "BULLISH", "strength": "STRONG", "interpretation": "..."}
    fundamental_alignment = Column(JSON, nullable=True)

    # Risk assessment (stored as JSON)
    # Structure: {"risk_level": "LOW", "primary_risks": [...], "mitigation": "...", ...}
    risk_assessment = Column(JSON, nullable=False)

    # Entry plan (stored as JSON)
    # Structure: {"entry_price": 81250, "stop_loss": 81650, "targets": [...], "risk_reward": 7.0}
    entry_plan = Column(JSON, nullable=True)

    # Timeframe summary (stored as JSON)
    # Structure: {"15M": {"bias": "BEARISH", "confidence": 0.87, ...}, "1H": {...}, ...}
    timeframe_summary = Column(JSON, nullable=False)

    # Confidence breakdown (stored as JSON)
    # Structure: {"technical_confidence": 0.82, "confluence_score": 0.88, ...}
    confidence_breakdown = Column(JSON, nullable=False)

    # Reasoning narratives (stored as Text - can be large)
    executive_summary = Column(Text, nullable=False)  # TLDR version
    detailed_reasoning = Column(Text, nullable=False)  # Complete analysis

    # Performance tracking (updated after trade completes)
    actual_entry_price = Column(Float, nullable=True)
    actual_exit_price = Column(Float, nullable=True)
    actual_pnl = Column(Float, nullable=True)
    actual_pnl_percent = Column(Float, nullable=True)
    trade_outcome = Column(String(20), nullable=True)  # "WIN", "LOSS", "BREAKEVEN"

    # Relationships
    signals = relationship("Signal", back_populates="trading_decision", cascade="all, delete-orphan")
    evidence_items = relationship("Evidence", back_populates="trading_decision", cascade="all, delete-orphan")
    analysis_reports = relationship("AnalysisReport", back_populates="trading_decision", cascade="all, delete-orphan")

    # Indexes for querying - IMPORTANT: user_id must be first for query performance
    __table_args__ = (
        Index('idx_trading_decision_user_id', 'user_id'),
        Index('idx_trading_decision_user_symbol', 'user_id', 'symbol'),
        Index('idx_trading_decision_symbol', 'symbol'),
        Index('idx_trading_decision_action', 'action'),
        Index('idx_trading_decision_confidence', 'confidence'),
        Index('idx_trading_decision_generated_at', 'generated_at'),
        Index('idx_trading_decision_should_trade', 'should_trade'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "symbol": self.symbol,
            "action": self.action.value if self.action else None,
            "confidence": self.confidence,
            "confidence_level": self.confidence_level.value if self.confidence_level else None,
            "primary_arguments": self.primary_arguments,
            "counter_arguments": self.counter_arguments,
            "fundamental_alignment": self.fundamental_alignment,
            "risk_assessment": self.risk_assessment,
            "entry_plan": self.entry_plan,
            "timeframe_summary": self.timeframe_summary,
            "confidence_breakdown": self.confidence_breakdown,
            "executive_summary": self.executive_summary,
            "detailed_reasoning": self.detailed_reasoning,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "should_trade": self.should_trade == "true",
            "actual_entry_price": self.actual_entry_price,
            "actual_exit_price": self.actual_exit_price,
            "actual_pnl": self.actual_pnl,
            "actual_pnl_percent": self.actual_pnl_percent,
            "trade_outcome": self.trade_outcome,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<TradingDecision(symbol={self.symbol}, action={self.action}, "
            f"confidence={self.confidence:.2f}, should_trade={self.should_trade})>"
        )


class Evidence(BaseModel):
    """
    Evidence storage for audit trail.

    Stores individual pieces of evidence that support trading decisions.
    This allows querying which patterns/indicators led to decisions.
    """

    __tablename__ = "evidence"

    # User ownership - CRITICAL for multi-user isolation
    user_id = Column(String(36), nullable=False, index=True)

    # Link to trading decision
    trading_decision_id = Column(String(36), ForeignKey('trading_decisions.id'), nullable=False, index=True)

    # Evidence details
    source = Column(String(100), nullable=False)  # "4H Timeframe", "Fundamental Analysis"
    type = Column(String(100), nullable=False)    # "SMC Pattern", "Elliott Wave", "Indicator"
    description = Column(Text, nullable=False)
    score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=True)

    # Evidence metadata (stored as JSON for flexibility)
    metadata = Column(JSON, nullable=True)

    # Relationship
    trading_decision = relationship("TradingDecision", back_populates="evidence_items")

    # Indexes - IMPORTANT: user_id must be first for query performance
    __table_args__ = (
        Index('idx_evidence_user_id', 'user_id'),
        Index('idx_evidence_user_decision', 'user_id', 'trading_decision_id'),
        Index('idx_evidence_decision_id', 'trading_decision_id'),
        Index('idx_evidence_source', 'source'),
        Index('idx_evidence_type', 'type'),
        Index('idx_evidence_score', 'score'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "trading_decision_id": str(self.trading_decision_id),
            "source": self.source,
            "type": self.type,
            "description": self.description,
            "score": self.score,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "metadata": self.metadata,
        }


class AnalysisReport(BaseModel):
    """
    Complete analysis report storage.

    Stores the full multi-timeframe analysis report for archival and review.
    Useful for backtesting, system improvement, and compliance.
    """

    __tablename__ = "analysis_reports"

    # User ownership - CRITICAL for multi-user isolation
    user_id = Column(String(36), nullable=False, index=True)

    # Link to trading decision
    trading_decision_id = Column(String(36), ForeignKey('trading_decisions.id'), nullable=False, index=True)

    # Report metadata
    symbol = Column(String(20), nullable=False, index=True)
    report_type = Column(String(50), nullable=False)  # "MULTI_TIMEFRAME", "SINGLE_TIMEFRAME"
    timeframes_analyzed = Column(JSON, nullable=False)  # ["15M", "1H", "4H", "Daily"]

    # Complete analysis data (stored as JSON)
    # This includes ALL patterns detected, scores, levels, etc.
    analysis_data = Column(JSON, nullable=False)

    # Report file path (if saved to disk)
    report_file_path = Column(String(500), nullable=True)

    # Generated timestamp
    generated_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Relationship
    trading_decision = relationship("TradingDecision", back_populates="analysis_reports")

    # Indexes - IMPORTANT: user_id must be first for query performance
    __table_args__ = (
        Index('idx_analysis_report_user_id', 'user_id'),
        Index('idx_analysis_report_user_symbol', 'user_id', 'symbol'),
        Index('idx_analysis_report_decision_id', 'trading_decision_id'),
        Index('idx_analysis_report_symbol', 'symbol'),
        Index('idx_analysis_report_generated_at', 'generated_at'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "trading_decision_id": str(self.trading_decision_id),
            "symbol": self.symbol,
            "report_type": self.report_type,
            "timeframes_analyzed": self.timeframes_analyzed,
            "analysis_data": self.analysis_data,
            "report_file_path": self.report_file_path,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
        }


# Update Signal model to link to TradingDecision
# (This would be added to the existing Signal model)
"""
Add to Signal model:

    # Link to trading decision
    trading_decision_id = Column(String(36), ForeignKey('trading_decisions.id'), nullable=True)

    # Relationship
    trading_decision = relationship("TradingDecision", back_populates="signals")
"""
