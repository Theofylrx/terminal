# Fundamental + Technical Analysis Confluence

**Feature:** Symbol Research Dashboard & Analysis Confluence
**Status:** Design Phase
**Priority:** High

---

## 🎯 Overview

**Principle:**
- **Technical Analysis** = Primary driver for trade timing (entry/exit signals)
- **Fundamental Analysis** = Optional context/filter for symbol selection
- **Confluence** = Combine both for higher-quality trading decisions

**User Need:**
Users should be able to:
1. **Research any symbol** - View fundamentals + technicals before enabling auto-trading
2. **See confluence** - Understand when both fundamental and technical align
3. **Make informed decisions** - Choose which symbols to auto-trade based on complete data

---

## 🏗️ Architecture Integration

### **Existing Agents:**

```
┌────────────────────────────────────────────────────────────────┐
│  ANALYSIS LAYER                                                │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────┐      ┌──────────────────────┐       │
│  │  Technical Analyst   │      │  Fundamental Analyst │       │
│  │  ──────────────────  │      │  ──────────────────  │       │
│  │  • 21 Patterns (SMC) │      │  • Financial Ratios  │       │
│  │  • Elliott Wave      │      │  • Earnings Data     │       │
│  │  • Divergence        │      │  • Company Metrics   │       │
│  │  • AI Reasoning      │      │  • News Sentiment    │       │
│  │  • Confidence Score  │      │  • Sector Analysis   │       │
│  │                      │      │  • Health Score      │       │
│  │  PRIMARY for timing  │      │  OPTIONAL for filter │       │
│  └──────────────────────┘      └──────────────────────┘       │
│           │                              │                     │
│           └──────────────┬───────────────┘                     │
│                          ↓                                     │
│              ┌──────────────────────┐                          │
│              │  Confluence Engine   │                          │
│              │  ──────────────────  │                          │
│              │  • Combines signals  │                          │
│              │  • Boosts confidence │                          │
│              │  • Filters symbols   │                          │
│              └──────────────────────┘                          │
│                          │                                     │
│                          ↓                                     │
│              ┌──────────────────────┐                          │
│              │  Auto-Trading Engine │                          │
│              │  (Decision Making)   │                          │
│              └──────────────────────┘                          │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## 📊 Fundamental Analysis - What We Track

### **Data Sources:**
- **Alpha Vantage** - Company fundamentals, financial statements
- **Financial Modeling Prep** - Ratios, metrics, earnings
- **News APIs** - Sentiment analysis
- **SEC EDGAR** - Official filings (optional)

### **Fundamental Metrics:**

```python
class FundamentalAnalysis:
    """Fundamental data for a symbol"""

    # Company Info
    company_name: str
    sector: str
    industry: str
    market_cap: float
    description: str

    # Financial Ratios
    pe_ratio: float          # Price-to-Earnings
    pb_ratio: float          # Price-to-Book
    ps_ratio: float          # Price-to-Sales
    peg_ratio: float         # PEG (growth-adjusted P/E)

    # Profitability
    profit_margin: float     # Net profit margin %
    operating_margin: float
    roe: float               # Return on Equity
    roa: float               # Return on Assets

    # Growth
    revenue_growth_yoy: float
    earnings_growth_yoy: float
    revenue_growth_qoq: float

    # Financial Health
    current_ratio: float
    quick_ratio: float
    debt_to_equity: float
    free_cash_flow: float

    # Earnings
    next_earnings_date: datetime
    estimated_eps: float
    actual_eps: float
    eps_surprise: float

    # Analyst Ratings
    analyst_rating: str      # Buy, Hold, Sell
    price_target: float
    num_analysts: int

    # News Sentiment
    sentiment_score: float   # -1 to +1
    news_volume: int
    recent_headlines: List[str]

    # Overall Health Score
    fundamental_score: float  # 0-100
    fundamental_rating: str   # STRONG, GOOD, NEUTRAL, WEAK, POOR
```

---

## 🔄 Confluence Logic - How Technical + Fundamental Work Together

### **Approach: 3-Tier System**

```
┌────────────────────────────────────────────────────────────────┐
│  TIER 1: FUNDAMENTAL FILTERING (Optional Symbol Screening)    │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Before enabling auto-trading on a symbol, check:              │
│                                                                 │
│  ✓ Fundamental Score > 50 (NEUTRAL or better)                  │
│  ✓ No upcoming earnings in next 3 days (avoid volatility)      │
│  ✓ Sentiment not extremely negative (< -0.7)                   │
│  ✓ Not in financial distress (debt/equity < 3.0)               │
│                                                                 │
│  → If passed: Symbol is ELIGIBLE for auto-trading              │
│  → If failed: Symbol is FLAGGED (user can override)            │
│                                                                 │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│  TIER 2: CONFIDENCE BOOSTING (Enhance Technical Signals)      │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  When technical signal is detected:                            │
│                                                                 │
│  Base Technical Confidence: 75%                                │
│                                                                 │
│  + Fundamental Boost:                                          │
│    • Fundamental Score 80+:        +5% confidence              │
│    • Analyst Rating "Buy":         +3% confidence              │
│    • Positive Sentiment (+0.5):    +2% confidence              │
│    • Strong Revenue Growth (>20%): +2% confidence              │
│                                                                 │
│  - Fundamental Warning:                                        │
│    • Earnings in 1-3 days:         -5% confidence              │
│    • Negative sentiment (<-0.3):   -3% confidence              │
│    • High debt/equity (>2.5):      -2% confidence              │
│                                                                 │
│  Final Confidence: 75% + 12% - 0% = 87%                        │
│                                                                 │
│  → If >= 70%: Execute trade                                    │
│  → If < 70%: Wait for better signal                            │
│                                                                 │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│  TIER 3: RISK ADJUSTMENT (Position Sizing Modifier)           │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Adjust position size based on fundamental strength:           │
│                                                                 │
│  Base Risk: 1% of capital                                      │
│                                                                 │
│  Fundamental Score 80+:  Risk = 1.2% (increase position)       │
│  Fundamental Score 60-80: Risk = 1.0% (standard)               │
│  Fundamental Score 40-60: Risk = 0.8% (reduce position)        │
│  Fundamental Score <40:   Risk = 0.5% (minimal position)       │
│                                                                 │
│  Example:                                                       │
│  - AAPL: Fundamental Score 85 → Trade with 1.2% risk           │
│  - TSLA: Fundamental Score 55 → Trade with 0.8% risk           │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## 🖥️ Symbol Research Dashboard UI

### **New Tab: "Symbol Research"**

```
┌──────────────────────────────────────────────────────────────────────┐
│  Symbol Research & Analysis                                          │
│  [Search: _____________] [Search]        Recently Viewed: AAPL TSLA │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  AAPL - Apple Inc.                              NASDAQ      │    │
│  │  Current Price: $152.50  |  Change: +$2.30 (+1.53%)        │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  CONFLUENCE SCORE                                             │   │
│  │  ──────────────────────────────────────────────────────────       │
│  │                                                               │   │
│  │  Overall Rating: ★★★★☆ STRONG BUY                           │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │                                                               │   │
│  │  ┌──────────────────┐        ┌──────────────────┐           │   │
│  │  │  TECHNICAL       │        │  FUNDAMENTAL     │           │   │
│  │  │  ──────────────  │        │  ──────────────  │           │   │
│  │  │  Signal: BULLISH │        │  Score: 85/100   │           │   │
│  │  │  Confidence: 82% │        │  Rating: STRONG  │           │   │
│  │  │  ████████░░ 82%  │        │  ████████░░ 85%  │           │   │
│  │  │                  │        │                  │           │   │
│  │  │  ✅ 5 Patterns   │        │  ✅ High Growth  │           │   │
│  │  │  ✅ Strong Trend │        │  ✅ Profitable   │           │   │
│  │  │  ⚠️  Overbought  │        │  ⚠️  High P/E    │           │   │
│  │  └──────────────────┘        └──────────────────┘           │   │
│  │                                                               │   │
│  │  CONFLUENCE: Both technical and fundamental align for LONG   │   │
│  │  Recommended Action: ✅ STRONG BUY (Auto-Trade Eligible)     │   │
│  │                                                               │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌─ TAB NAVIGATION ─────────────────────────────────────────────┐   │
│  │  [Overview] [Fundamental] [Technical] [News] [Chart]        │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

---

### **Sub-Tab: FUNDAMENTAL VIEW**

```
┌──────────────────────────────────────────────────────────────────────┐
│  Fundamental Analysis - AAPL                                         │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  COMPANY OVERVIEW                                            │    │
│  │  ──────────────────────────────────────────────────────────      │
│  │  Name: Apple Inc.                                            │    │
│  │  Sector: Technology                                          │    │
│  │  Industry: Consumer Electronics                              │    │
│  │  Market Cap: $2.4T                                           │    │
│  │  Employees: 164,000                                          │    │
│  │                                                               │    │
│  │  Description: Apple Inc. designs, manufactures, and markets  │    │
│  │  smartphones, personal computers, tablets, wearables, and    │    │
│  │  accessories worldwide...                                    │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  FUNDAMENTAL HEALTH SCORE: 85/100 - STRONG                  │    │
│  │  ──────────────────────────────────────────────────────────      │
│  │  [████████████████░░]  85%                                   │    │
│  │                                                               │    │
│  │  ✅ Profitability: Excellent (96/100)                        │    │
│  │  ✅ Growth: Strong (82/100)                                  │    │
│  │  ✅ Financial Health: Excellent (91/100)                     │    │
│  │  ⚠️  Valuation: High (65/100) - Expensive P/E               │    │
│  │  ✅ Momentum: Strong (88/100)                                │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  VALUATION       │  │  PROFITABILITY   │  │  GROWTH          │  │
│  │  ──────────────  │  │  ──────────────  │  │  ──────────────  │  │
│  │  P/E Ratio       │  │  Profit Margin   │  │  Revenue (YoY)   │  │
│  │  28.5x ⚠️        │  │  26.3% ✅        │  │  +8.1% ✅        │  │
│  │  (High)          │  │  (Excellent)     │  │  (Good)          │  │
│  │                  │  │                  │  │                  │  │
│  │  P/B Ratio       │  │  Operating Mrgn  │  │  Earnings (YoY)  │  │
│  │  42.8x ⚠️        │  │  30.7% ✅        │  │  +11.2% ✅       │  │
│  │  (High)          │  │  (Excellent)     │  │  (Strong)        │  │
│  │                  │  │                  │  │                  │  │
│  │  P/S Ratio       │  │  ROE             │  │  Revenue (QoQ)   │  │
│  │  7.3x ⚠️         │  │  147.2% ✅       │  │  +6.5% ✅        │  │
│  │  (High)          │  │  (Exceptional)   │  │  (Good)          │  │
│  │                  │  │                  │  │                  │  │
│  │  PEG Ratio       │  │  ROA             │  │  EPS Growth      │  │
│  │  2.54 ⚠️         │  │  28.4% ✅        │  │  +13.4% ✅       │  │
│  │  (Expensive)     │  │  (Excellent)     │  │  (Strong)        │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│                                                                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  FINANCIAL HEALTH│  │  EARNINGS        │  │  ANALYST RATINGS │  │
│  │  ──────────────  │  │  ──────────────  │  │  ──────────────  │  │
│  │  Current Ratio   │  │  Next Report     │  │  Consensus       │  │
│  │  0.98 ⚠️         │  │  Jan 30, 2024    │  │  STRONG BUY ✅   │  │
│  │  (Below 1.0)     │  │  (12 days)       │  │                  │  │
│  │                  │  │                  │  │  Buy:     28     │  │
│  │  Quick Ratio     │  │  Est. EPS        │  │  Hold:    8      │  │
│  │  0.93 ⚠️         │  │  $2.10           │  │  Sell:    2      │  │
│  │  (Below 1.0)     │  │                  │  │                  │  │
│  │                  │  │  Prev. EPS       │  │  Price Target    │  │
│  │  Debt/Equity     │  │  $1.89 (actual)  │  │  $195.00         │  │
│  │  1.73 ✅         │  │  $1.94 (est)     │  │  (+27.8%)        │  │
│  │  (Healthy)       │  │  Beat by 2.6%    │  │                  │  │
│  │                  │  │                  │  │  38 Analysts     │  │
│  │  Free Cash Flow  │  │  Surprise: ✅    │  │  Avg Rating: 8.4 │  │
│  │  $99.8B ✅       │  │                  │  │                  │  │
│  │  (Excellent)     │  │                  │  │                  │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  NEWS SENTIMENT ANALYSIS                                     │    │
│  │  ──────────────────────────────────────────────────────────      │
│  │  Overall Sentiment: +0.67 (POSITIVE) ✅                      │    │
│  │  News Volume: 156 articles (last 7 days)                    │    │
│  │                                                               │    │
│  │  Recent Headlines:                                            │    │
│  │  📰 "Apple reports record Q4 earnings, beats estimates"      │    │
│  │      Sentiment: +0.9 (Very Positive) | 2 hours ago          │    │
│  │                                                               │    │
│  │  📰 "iPhone 15 sales exceed expectations in China"           │    │
│  │      Sentiment: +0.8 (Positive) | 5 hours ago               │    │
│  │                                                               │    │
│  │  📰 "Apple faces regulatory scrutiny in EU markets"          │    │
│  │      Sentiment: -0.4 (Slightly Negative) | 1 day ago        │    │
│  │                                                               │    │
│  │  [View All News]                                             │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  AUTO-TRADING RECOMMENDATION                                 │    │
│  │  ──────────────────────────────────────────────────────────      │
│  │  Fundamental Filter: ✅ PASSED                               │    │
│  │  ✓ Score above 50 (85)                                       │    │
│  │  ✓ No earnings blackout (12 days away)                      │    │
│  │  ✓ Sentiment positive (+0.67)                               │    │
│  │  ✓ Financial health good                                     │    │
│  │                                                               │    │
│  │  Confidence Boost: +7%                                       │    │
│  │  + High fundamental score (80+): +5%                         │    │
│  │  + Analyst "Strong Buy": +3%                                 │    │
│  │  + Positive sentiment: +2%                                   │    │
│  │  - Earnings soon (12 days): -3%                              │    │
│  │                                                               │    │
│  │  Risk Adjustment: 1.2x                                       │    │
│  │  Recommended risk: 1.2% (vs standard 1.0%)                   │    │
│  │  Reason: Strong fundamentals justify increased position      │    │
│  │                                                               │    │
│  │  [Enable Auto-Trading for AAPL]                              │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

---

### **Sub-Tab: TECHNICAL VIEW**

```
┌──────────────────────────────────────────────────────────────────────┐
│  Technical Analysis - AAPL                                           │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  TECHNICAL SIGNAL SUMMARY                                    │    │
│  │  ──────────────────────────────────────────────────────────      │
│  │  Direction: BULLISH ✅                                       │    │
│  │  Confidence: 82%                                             │    │
│  │  [████████░░] 82%                                            │    │
│  │                                                               │    │
│  │  Trend Strength: Strong (9/10)                               │    │
│  │  Momentum: Bullish (8/10)                                    │    │
│  │  Volatility: Moderate (5/10)                                 │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  PATTERNS DETECTED (5 Active)                                │    │
│  │  ──────────────────────────────────────────────────────────      │
│  │                                                               │    │
│  │  ✅ Order Block (Bullish) - 15m chart                        │    │
│  │     Level: $150.00 | Confidence: 88%                        │    │
│  │     Status: Holding as support                              │    │
│  │                                                               │    │
│  │  ✅ Break of Structure - 1h chart                            │    │
│  │     Broke: $151.50 resistance | Confidence: 85%             │    │
│  │     Direction: Bullish continuation expected                │    │
│  │                                                               │    │
│  │  ✅ Fair Value Gap - 5m chart                                │    │
│  │     Gap: $149.80-$150.20 | Confidence: 78%                  │    │
│  │     Status: Filled, acting as support                       │    │
│  │                                                               │    │
│  │  ⚠️  RSI Divergence (Bearish) - 1h chart                     │    │
│  │     Type: Regular bearish divergence | Confidence: 65%      │    │
│  │     Warning: Potential correction forming                   │    │
│  │                                                               │    │
│  │  ✅ Elliott Wave (Impulse) - 4h chart                        │    │
│  │     Wave: 5 of impulse | Confidence: 72%                    │    │
│  │     Target: $158.00 (wave 5 extension)                      │    │
│  │                                                               │    │
│  │  [View All Patterns] [Pattern Education]                    │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  INDICATORS                                                   │    │
│  │  ──────────────────────────────────────────────────────────      │
│  │                                                               │    │
│  │  RSI (14): 68.3 ⚠️ (Approaching Overbought)                  │    │
│  │  MACD: BULLISH ✅ (Signal line cross up)                     │    │
│  │  Moving Averages: BULLISH ✅ (Price above 20, 50, 200 SMA)   │    │
│  │  Volume: INCREASING ✅ (Above 20-day average)                │    │
│  │  ATR (14): $2.34 (Moderate volatility)                      │    │
│  │  Stochastic: 78.2 ⚠️ (Overbought zone)                       │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  SUPPORT & RESISTANCE LEVELS                                 │    │
│  │  ──────────────────────────────────────────────────────────      │
│  │  Current Price: $152.50                                      │    │
│  │                                                               │    │
│  │  Resistance:                                                  │    │
│  │  R3: $158.00 (Strong) - Wave 5 target                       │    │
│  │  R2: $155.50 (Moderate) - Previous high                     │    │
│  │  R1: $153.80 (Weak) - Intraday resistance                   │    │
│  │                                                               │    │
│  │  ──────────── $152.50 (Current) ─────────────                │    │
│  │                                                               │    │
│  │  Support:                                                     │    │
│  │  S1: $150.00 (Strong) - Order block                         │    │
│  │  S2: $148.20 (Moderate) - 20 SMA                            │    │
│  │  S3: $145.50 (Strong) - Major support zone                  │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  AI REASONING                                                 │    │
│  │  ──────────────────────────────────────────────────────────      │
│  │  "Strong bullish structure detected on multiple timeframes.  │    │
│  │  Price has broken above $151.50 resistance with strong      │    │
│  │  volume confirmation. Order block at $150 providing solid   │    │
│  │  support. MACD showing bullish momentum.                     │    │
│  │                                                               │    │
│  │  However, RSI at 68.3 approaching overbought and bearish     │    │
│  │  divergence forming on 1h chart suggests caution. Recommend  │    │
│  │  entry on pullback to $150-$151 zone with tight stop at     │    │
│  │  $148.50.                                                     │    │
│  │                                                               │    │
│  │  Target: $158.00 (Wave 5 projection)                         │    │
│  │  Risk/Reward: 1:2.8 (Excellent)                              │    │
│  │  Timeframe: 2-5 days hold expected"                          │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  ENTRY RECOMMENDATION                                         │    │
│  │  ──────────────────────────────────────────────────────────      │
│  │  Action: BUY on pullback ✅                                  │    │
│  │  Entry Zone: $150.00 - $151.00                               │    │
│  │  Stop Loss: $148.50 (-1.67%)                                 │    │
│  │  Take Profit: $158.00 (+5.4%)                                │    │
│  │  Risk/Reward: 1:2.8                                           │    │
│  │                                                               │    │
│  │  Confidence: 82% (Technical) + 7% (Fundamental) = 89% 🔥     │    │
│  │                                                               │    │
│  │  [Enable Auto-Trading] [Set Price Alert]                     │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Integration with Auto-Trading Engine

### **Modified Decision Flow:**

```python
async def evaluate_entry_signal(config, symbol):
    """
    Evaluate if we should enter a trade, considering both
    technical and fundamental analysis
    """

    # 1. Get Technical Analysis (PRIMARY)
    technical = await technical_analyst.analyze(symbol)

    # 2. Get Fundamental Analysis (OPTIONAL)
    fundamental = None
    if config.use_fundamental_filter:
        fundamental = await fundamental_analyst.analyze(symbol)

    # 3. Check Fundamental Filter (if enabled)
    if fundamental:
        filter_result = apply_fundamental_filter(fundamental)
        if not filter_result.passed:
            logger.info(
                f"Symbol {symbol} failed fundamental filter: "
                f"{filter_result.reason}"
            )
            return Decision(
                should_enter=False,
                reason=f"Fundamental filter failed: {filter_result.reason}"
            )

    # 4. Check Technical Signal
    if technical.confidence < config.entry_confidence_threshold:
        return Decision(
            should_enter=False,
            reason=f"Technical confidence too low: {technical.confidence}%"
        )

    # 5. Apply Confluence Boost (if fundamental available)
    final_confidence = technical.confidence

    if fundamental:
        boost = calculate_confluence_boost(fundamental, technical)
        final_confidence += boost

        logger.info(
            f"Confidence boosted from {technical.confidence}% "
            f"to {final_confidence}% (+{boost}% fundamental)"
        )

    # 6. Adjust Risk Based on Fundamentals
    risk_multiplier = 1.0
    if fundamental:
        risk_multiplier = calculate_risk_multiplier(fundamental)

    # 7. Make Final Decision
    return Decision(
        should_enter=True,
        side=technical.direction,
        confidence=final_confidence,
        risk_multiplier=risk_multiplier,
        technical_analysis=technical,
        fundamental_analysis=fundamental,
        reasoning=generate_confluence_reasoning(technical, fundamental)
    )


def apply_fundamental_filter(fundamental: FundamentalAnalysis) -> FilterResult:
    """Apply fundamental screening filter"""

    reasons = []

    # Check fundamental score
    if fundamental.fundamental_score < 50:
        reasons.append(f"Low fundamental score: {fundamental.fundamental_score}/100")

    # Check earnings blackout
    if fundamental.days_until_earnings <= 3:
        reasons.append(f"Earnings in {fundamental.days_until_earnings} days (high volatility)")

    # Check sentiment
    if fundamental.sentiment_score < -0.7:
        reasons.append(f"Very negative sentiment: {fundamental.sentiment_score}")

    # Check financial health
    if fundamental.debt_to_equity > 3.0:
        reasons.append(f"High debt/equity: {fundamental.debt_to_equity}")

    passed = len(reasons) == 0

    return FilterResult(
        passed=passed,
        reason="; ".join(reasons) if not passed else "All checks passed"
    )


def calculate_confluence_boost(
    fundamental: FundamentalAnalysis,
    technical: TechnicalAnalysis
) -> float:
    """Calculate confidence boost from fundamental confluence"""

    boost = 0.0

    # Strong fundamentals boost
    if fundamental.fundamental_score >= 80:
        boost += 5.0
    elif fundamental.fundamental_score >= 70:
        boost += 3.0

    # Analyst rating boost
    if fundamental.analyst_rating == "Strong Buy":
        boost += 3.0
    elif fundamental.analyst_rating == "Buy":
        boost += 2.0

    # Sentiment boost
    if fundamental.sentiment_score >= 0.5:
        boost += 2.0
    elif fundamental.sentiment_score >= 0.3:
        boost += 1.0

    # Growth boost
    if fundamental.revenue_growth_yoy >= 0.20:  # 20%+
        boost += 2.0

    # Earnings warning (reduce)
    if fundamental.days_until_earnings <= 3:
        boost -= 5.0
    elif fundamental.days_until_earnings <= 7:
        boost -= 3.0

    # Negative sentiment warning
    if fundamental.sentiment_score < -0.3:
        boost -= 3.0

    # High debt warning
    if fundamental.debt_to_equity > 2.5:
        boost -= 2.0

    return boost


def calculate_risk_multiplier(fundamental: FundamentalAnalysis) -> float:
    """Adjust position size based on fundamental strength"""

    score = fundamental.fundamental_score

    if score >= 80:
        return 1.2  # Increase position by 20%
    elif score >= 60:
        return 1.0  # Standard position
    elif score >= 40:
        return 0.8  # Reduce position by 20%
    else:
        return 0.5  # Minimal position (50%)
```

---

## 📋 Database Schema Updates

### **Auto-Trading Config - Add Fundamental Options:**

```sql
ALTER TABLE auto_trading_configs
ADD COLUMN use_fundamental_filter BOOLEAN DEFAULT true,
ADD COLUMN min_fundamental_score DECIMAL(5,2) DEFAULT 50.0,
ADD COLUMN earnings_blackout_days INTEGER DEFAULT 3,
ADD COLUMN min_sentiment_score DECIMAL(3,2) DEFAULT -0.7;
```

### **New Table: Fundamental Data Cache:**

```sql
CREATE TABLE fundamental_data (
    id UUID PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,

    -- Company Info
    company_name VARCHAR(200),
    sector VARCHAR(100),
    industry VARCHAR(100),
    market_cap DECIMAL(20,2),

    -- Ratios
    pe_ratio DECIMAL(10,2),
    pb_ratio DECIMAL(10,2),
    ps_ratio DECIMAL(10,2),
    peg_ratio DECIMAL(10,2),

    -- Profitability
    profit_margin DECIMAL(5,2),
    operating_margin DECIMAL(5,2),
    roe DECIMAL(5,2),
    roa DECIMAL(5,2),

    -- Growth
    revenue_growth_yoy DECIMAL(5,2),
    earnings_growth_yoy DECIMAL(5,2),

    -- Financial Health
    current_ratio DECIMAL(10,2),
    debt_to_equity DECIMAL(10,2),
    free_cash_flow DECIMAL(20,2),

    -- Earnings
    next_earnings_date TIMESTAMPTZ,
    days_until_earnings INTEGER,
    estimated_eps DECIMAL(10,2),
    actual_eps DECIMAL(10,2),

    -- Analyst Data
    analyst_rating VARCHAR(20),
    price_target DECIMAL(10,2),
    num_analysts INTEGER,

    -- Sentiment
    sentiment_score DECIMAL(3,2),
    news_volume INTEGER,

    -- Overall Score
    fundamental_score DECIMAL(5,2),
    fundamental_rating VARCHAR(20),

    -- Metadata
    data_source VARCHAR(50),
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(symbol, fetched_at)
);

CREATE INDEX idx_fundamental_symbol ON fundamental_data(symbol);
CREATE INDEX idx_fundamental_score ON fundamental_data(fundamental_score DESC);
CREATE INDEX idx_fundamental_expires ON fundamental_data(expires_at);
```

---

## 🎯 Summary

### **What This Adds:**

1. **Symbol Research Dashboard** - View fundamental + technical for ANY symbol
2. **Fundamental Data Display** - Complete financial metrics, ratios, earnings, sentiment
3. **Technical Data Display** - Patterns, indicators, support/resistance, AI reasoning
4. **Confluence Score** - Visual representation of technical + fundamental alignment
5. **3-Tier Confluence System:**
   - Tier 1: Fundamental filtering (optional screening)
   - Tier 2: Confidence boosting (enhance technical signals)
   - Tier 3: Risk adjustment (modify position sizing)

### **User Benefits:**

- ✅ Research symbols before enabling auto-trading
- ✅ See complete picture (fundamental + technical)
- ✅ Understand why AI makes decisions
- ✅ Make informed choices about which symbols to trade
- ✅ View fundamental data even if not used for auto-trading
- ✅ Optional fundamental filtering (can disable if desired)

### **Technical Benefits:**

- ✅ Leverages existing Fundamental Analyst Service
- ✅ Non-intrusive (fundamental is optional, not mandatory)
- ✅ Increases signal quality through confluence
- ✅ Reduces risk on fundamentally weak symbols
- ✅ Caches fundamental data to reduce API calls

---

**Does this approach make sense for handling fundamental + technical confluence?** 🎯
