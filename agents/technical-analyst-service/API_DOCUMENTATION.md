# Technical Analyst Service - API Documentation

## Overview

The Technical Analyst Service provides enterprise-grade technical analysis and trading signal generation using institutional-quality patterns and indicators.

## Documentation Resources

### 🔗 Interactive API Documentation (Swagger UI)

Access the interactive API documentation at:
```
http://localhost:8000/docs
```

**Features:**
- Try all endpoints directly from the browser
- View request/response schemas
- See detailed parameter descriptions
- Execute requests with sample data

### 📖 Alternative Documentation (ReDoc)

Cleaner, more readable documentation at:
```
http://localhost:8000/redoc
```

**Features:**
- Better organized endpoint documentation
- Easier to read schemas
- Downloadable OpenAPI spec
- Better for reference documentation

### 📬 Postman Collection

Import the Postman collection for easy API testing:

**Files:**
- `Technical_Analyst_API.postman_collection.json` - Complete API collection
- `Technical_Analyst_Environments.postman_environment.json` - Environment variables

**How to Import:**
1. Open Postman
2. Click "Import" button
3. Select both JSON files
4. Collection and environment will be imported

**Collection Features:**
- Pre-configured requests for all endpoints
- Environment variables for easy testing
- Common test scripts for validation
- Organized by feature (Signals, Indicators, Elliott Wave, etc.)

## API Endpoints

### Base URL
```
http://localhost:8000/api/v1
```

---

## 🏥 Health Endpoints

### Health Check
```http
GET /health
```

Check if the service is running and healthy.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-09-19T02:00:00Z",
  "version": "2.0.0"
}
```

---

## 📊 Signal Endpoints

### Generate Signal
```http
POST /signals/generate
```

Generate a high-confidence trading signal using all available analysis methods.

**Request Body:**
```json
{
  "symbol": "AAPL",
  "timeframe": "1h"
}
```

**Parameters:**
- `symbol` (string, required): Trading symbol (e.g., AAPL, BTCUSD, EURUSD)
- `timeframe` (string, optional): Timeframe for analysis (1m, 5m, 15m, 1h, 4h, 1D)
  - Default: "1h"

**Response:**
```json
{
  "id": "signal-123",
  "symbol": "AAPL",
  "timeframe": "1h",
  "signal_type": "BUY",
  "status": "ACTIVE",
  "entry_price": 150.50,
  "current_price": 150.50,
  "target_price": 155.20,
  "stop_loss": 148.30,
  "confidence": 85.5,
  "strategy": "multi_indicator_pattern",
  "description": "RSI oversold (28.5); MACD bullish crossover; Price near lower Bollinger Band; EMA 9 above EMA 21 (bullish trend); Elliott Wave bullish impulse (Wave 3, 82% confidence); Regular Bullish Divergence (confirmed); Bullish FVG unfilled ($149.20-$150.10)",
  "generated_at": "2024-09-19T02:00:00Z",
  "expires_at": "2024-09-19T03:00:00Z"
}
```

**Analysis Includes:**
- 15 Technical Indicators (RSI, MACD, Bollinger Bands, EMAs, ATR, etc.)
- 10+ Candlestick & Chart Patterns
- Elliott Wave 5-wave impulse patterns
- RSI Divergences (Regular & Hidden)
- Smart Money Concepts (BOS, FVG, Supply/Demand)

### Get All Signals
```http
GET /signals?symbol={symbol}&status={status}&limit={limit}
```

Retrieve trading signals with optional filtering.

**Query Parameters:**
- `symbol` (string, optional): Filter by trading symbol
- `status` (string, optional): Filter by status (ACTIVE, TRIGGERED, EXPIRED, CANCELLED)
- `limit` (integer, optional): Maximum signals to return (max 500, default 100)

### Get Signal by ID
```http
GET /signals/{signal_id}
```

Retrieve a specific signal by its unique ID.

---

## 📈 Indicator Endpoints

### Get Technical Indicators
```http
GET /indicators/{symbol}?timeframe={timeframe}
```

Calculate and return current technical indicator values.

**Query Parameters:**
- `timeframe` (string, optional): Timeframe for analysis (default: 1h)

**Response:**
```json
{
  "symbol": "AAPL",
  "timeframe": "1h",
  "timestamp": "2024-09-19T02:00:00Z",
  "indicators": {
    "rsi": 45.3,
    "macd_line": 0.45,
    "macd_signal": 0.38,
    "macd_histogram": 0.07,
    "bb_upper": 152.50,
    "bb_middle": 150.00,
    "bb_lower": 147.50,
    "bb_percent_b": 0.55,
    "ema_9": 150.25,
    "ema_21": 149.80,
    "sma_50": 148.90,
    "atr": 2.35
  }
}
```

**Indicators Included:**
- **RSI** (Relative Strength Index)
- **MACD** (Moving Average Convergence Divergence)
- **Bollinger Bands** (upper, middle, lower, %B)
- **EMAs** (9, 21)
- **SMA** (50)
- **ATR** (Average True Range)

---

## 🌊 Elliott Wave Endpoints

### Detect Elliott Wave Pattern
```http
GET /elliott-wave/{symbol}?timeframe={timeframe}&direction={direction}
```

Detect Elliott Wave 5-wave impulse patterns with Fibonacci levels.

**Query Parameters:**
- `timeframe` (string, optional): Timeframe for analysis (default: 1h)
- `direction` (string, optional): Pattern direction - "bullish" or "bearish" (default: bullish)

**Response:**
```json
{
  "symbol": "AAPL",
  "timeframe": "1h",
  "timestamp": "2024-09-19T02:00:00Z",
  "pattern_type": "impulse",
  "direction": "bullish",
  "current_wave": 3,
  "confidence": 78.5,
  "is_complete": false,
  "waves": [
    {
      "wave_number": 1,
      "start_idx": 10,
      "end_idx": 25,
      "start_price": 145.50,
      "end_price": 152.30,
      "magnitude": 6.80,
      "is_up": true
    },
    {
      "wave_number": 2,
      "start_idx": 25,
      "end_idx": 35,
      "start_price": 152.30,
      "end_price": 148.20,
      "magnitude": 4.10,
      "is_up": false
    }
  ],
  "fibonacci_levels": [
    {
      "level": 0.382,
      "price": 149.70,
      "level_type": "retracement"
    },
    {
      "level": 0.618,
      "price": 148.10,
      "level_type": "retracement"
    },
    {
      "level": 1.618,
      "price": 159.20,
      "level_type": "extension"
    }
  ]
}
```

**Features:**
- Detects 5-wave impulse patterns (waves 1-5)
- Validates against Elliott Wave Theory rules
- Calculates Fibonacci retracements for Wave 2 & 4
- Calculates Fibonacci extensions for Wave 3 & 5
- Provides confidence score based on Fibonacci adherence

---

## 📉 Divergence Endpoints

### Detect RSI Divergences
```http
GET /divergences/{symbol}?timeframe={timeframe}
```

Detect RSI divergence patterns with Break of Structure confirmation.

**Query Parameters:**
- `timeframe` (string, optional): Timeframe for analysis (default: 1h)

**Response:**
```json
{
  "symbol": "AAPL",
  "timeframe": "1h",
  "timestamp": "2024-09-19T02:00:00Z",
  "divergences": [
    {
      "divergence_type": "regular_bullish",
      "start_idx": 45,
      "end_idx": 68,
      "price_start": 148.50,
      "price_end": 146.20,
      "rsi_start": 38.5,
      "rsi_end": 42.3,
      "confirmed": true,
      "confidence": 85.0,
      "description": "Regular Bullish Divergence: Price LL (148.50→146.20), RSI HL (38.5→42.3)",
      "is_bullish": true,
      "is_reversal": true
    }
  ]
}
```

**Divergence Types:**

1. **Regular Bullish** (Reversal UP)
   - Price: Lower Low (LL)
   - RSI: Higher Low (HL)
   - Signal: Potential reversal to upside

2. **Regular Bearish** (Reversal DOWN)
   - Price: Higher High (HH)
   - RSI: Lower High (LH)
   - Signal: Potential reversal to downside

3. **Hidden Bullish** (Continuation UP)
   - Price: Higher Low (HL)
   - RSI: Lower Low (LL)
   - Signal: Trend continuation upward

4. **Hidden Bearish** (Continuation DOWN)
   - Price: Lower High (LH)
   - RSI: Higher High (HH)
   - Signal: Trend continuation downward

**Break of Structure Confirmation:**
- `confirmed: true` - Price has broken previous high/low (higher confidence)
- `confirmed: false` - Divergence detected, awaiting BOS confirmation

---

## 💰 Smart Money Concepts Endpoints

### Detect Smart Money Patterns
```http
GET /smart-money/{symbol}?timeframe={timeframe}
```

Detect institutional trading patterns (Smart Money Concepts).

**Query Parameters:**
- `timeframe` (string, optional): Timeframe for analysis (default: 1h)

**Response:**
```json
{
  "symbol": "AAPL",
  "timeframe": "1h",
  "timestamp": "2024-09-19T02:00:00Z",
  "structure_breaks": [
    {
      "structure_type": "bos_bullish",
      "break_idx": 78,
      "break_price": 151.80,
      "previous_level": 150.20,
      "strength": 1.06,
      "volume_confirmation": true,
      "description": "BOS Bullish: Broke $150.20 at $151.80",
      "is_bullish": true
    }
  ],
  "fair_value_gaps": [
    {
      "direction": "bullish",
      "start_idx": 65,
      "end_idx": 67,
      "gap_high": 150.10,
      "gap_low": 149.20,
      "gap_size": 0.90,
      "midpoint": 149.65,
      "filled": false,
      "strength": 0.60
    }
  ],
  "supply_demand_zones": [
    {
      "zone_type": "demand",
      "start_idx": 50,
      "end_idx": 70,
      "zone_high": 148.75,
      "zone_low": 147.50,
      "zone_size": 1.25,
      "midpoint": 148.125,
      "strength": 80.0,
      "active": true,
      "touches": 4,
      "is_supply": false
    }
  ]
}
```

**Pattern Types:**

### Break of Structure (BOS)
- Price breaking previous swing high/low in trend direction
- Indicates trend continuation
- Volume confirmation strengthens signal

### Change of Character (CHoCH)
- Price breaking structure against trend
- Signals potential trend reversal
- Early warning of market shift

### Fair Value Gaps (FVG)
- Price imbalances between candles
- Bullish FVG: Candle 1 high < Candle 3 low
- Bearish FVG: Candle 1 low > Candle 3 high
- Often acts as support/resistance

### Supply/Demand Zones
- Areas where price reversed significantly
- Supply zones: Resistance (selling pressure)
- Demand zones: Support (buying pressure)
- Strength based on touches and reactions

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Insufficient data for AAPL. Need at least 50 bars."
}
```

### 404 Not Found
```json
{
  "detail": "No Elliott Wave bullish pattern detected for AAPL"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Failed to generate signal"
}
```

---

## Timeframe Options

All endpoints support the following timeframes:

- `1m` - 1 minute (day trading)
- `5m` - 5 minutes (day trading)
- `15m` - 15 minutes (day trading)
- `1h` - 1 hour (swing trading) **[DEFAULT]**
- `4h` - 4 hours (swing trading)
- `1D` - 1 day (position trading)

---

## Testing the API

### Using Swagger UI

1. Start the service: `make run-technical-analyst`
2. Open browser: `http://localhost:8000/docs`
3. Click on any endpoint
4. Click "Try it out"
5. Fill in parameters
6. Click "Execute"

### Using Postman

1. Import `Technical_Analyst_API.postman_collection.json`
2. Import `Technical_Analyst_Environments.postman_environment.json`
3. Select the environment in Postman
4. Edit variables if needed (symbol, timeframe)
5. Run any request from the collection

### Using cURL

```bash
# Generate signal
curl -X POST "http://localhost:8000/api/v1/signals/generate" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "timeframe": "1h"}'

# Get indicators
curl "http://localhost:8000/api/v1/indicators/AAPL?timeframe=1h"

# Detect Elliott Wave
curl "http://localhost:8000/api/v1/elliott-wave/AAPL?timeframe=1h&direction=bullish"

# Detect divergences
curl "http://localhost:8000/api/v1/divergences/AAPL?timeframe=1h"

# Detect Smart Money patterns
curl "http://localhost:8000/api/v1/smart-money/AAPL?timeframe=1h"
```

---

## Support

For issues, questions, or feature requests, contact the development team.

## Version

**API Version:** 2.0.0
**Last Updated:** 2024-09-19
