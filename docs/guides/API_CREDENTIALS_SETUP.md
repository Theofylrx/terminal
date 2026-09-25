# API Credentials Setup Guide
**Last Updated:** 2026-09-20

This guide explains how to obtain API credentials for real market data from Alpaca (stocks) and Binance (crypto).

---

## 🎯 Overview

Terminal connects to real market data providers to fetch live and historical data:

- **Alpaca** - US stocks, ETFs, options (free paper trading)
- **Binance** - Cryptocurrency markets (testnet available)
- **OANDA** - Forex markets (practice account available) [Optional]

---

## 📈 Alpaca (Stock Market Data)

### Step 1: Create Alpaca Account

1. Visit [Alpaca Markets](https://alpaca.markets/)
2. Click **"Sign Up"** (top right)
3. Choose **"Paper Trading Only"** (free, no funding required)
4. Fill in registration form:
   - Name
   - Email
   - Password
   - Country (must be eligible country)

5. Verify your email address

### Step 2: Get API Keys

1. Log in to [Alpaca Dashboard](https://app.alpaca.markets/)
2. Navigate to **"Your API Keys"** (left sidebar)
3. Under **"Paper Trading"** section:
   - Click **"Generate New Key"**
   - Copy the **API Key ID**
   - Copy the **Secret Key** (shown only once!)
   - ⚠️ **Save both immediately** - you can't view the secret again

### Step 3: Add to Terminal

Open `/terminal/.env` and add:

```bash
# Enable Alpaca
ENABLE_ALPACA=true

# Alpaca API Credentials (Paper Trading)
ALPACA_API_KEY=PK1234567890ABCDEF    # Your API Key ID
ALPACA_API_SECRET=xyz1234567890abc   # Your Secret Key
ALPACA_BASE_URL=https://paper-api.alpaca.markets  # Paper trading
ALPACA_PAPER=true
```

### Step 4: Verify Access

Test your credentials:

```bash
# From terminal root directory
python3 -c "
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta

# Your credentials
API_KEY = 'YOUR_API_KEY'
API_SECRET = 'YOUR_SECRET_KEY'

# Initialize client
client = StockHistoricalDataClient(API_KEY, API_SECRET)

# Fetch 1 day of AAPL data
request = StockBarsRequest(
    symbol_or_symbols='AAPL',
    timeframe=TimeFrame.Hour,
    start=datetime.now() - timedelta(days=1),
    end=datetime.now()
)

bars = client.get_stock_bars(request)
print(f'✅ Success! Fetched {len(bars[\"AAPL\"])} bars for AAPL')
"
```

Expected output:
```
✅ Success! Fetched 6 bars for AAPL
```

### Alpaca Features

✅ **Free Paper Trading**
- No deposit required
- $100,000 virtual cash
- Real-time market data
- Full API access

✅ **Data Available**
- Real-time trades (IEX)
- Real-time quotes
- Historical OHLCV bars (1m, 5m, 15m, 1h, 1d)
- Multiple timeframes
- US stocks, ETFs

✅ **Rate Limits**
- 200 requests/minute (data API)
- Unlimited WebSocket connections
- Free for paper trading

---

## ₿ Binance (Cryptocurrency Data)

### Step 1: Create Binance Account

1. Visit [Binance](https://www.binance.com/)
2. Click **"Register"** (top right)
3. Sign up with:
   - Email or phone
   - Password
   - Referral ID (optional)

4. Complete email/phone verification
5. Complete identity verification (KYC) if required

### Step 2: Get API Keys

#### Option A: Testnet (Recommended for Testing)

1. Visit [Binance Testnet](https://testnet.binance.vision/)
2. Log in with GitHub account
3. Click **"Generate HMAC_SHA256 Key"**
4. Copy:
   - **API Key**
   - **Secret Key**
5. Save both securely

#### Option B: Production (Real Trading)

⚠️ **CAUTION**: Production API keys can execute real trades!

1. Log in to [Binance](https://www.binance.com/)
2. Go to **Account** > **API Management**
3. Create a new API key:
   - Enter label (e.g., "Terminal Trading")
   - Complete 2FA verification
   - Copy API Key and Secret Key immediately
4. **Security Settings**:
   - Enable **"Reading"** permissions
   - Disable **"Trading"** initially (enable only when ready)
   - Enable IP whitelist for security
   - Set withdrawal address whitelist

### Step 3: Add to Terminal

#### For Testnet:
```bash
# Enable Binance
ENABLE_BINANCE=true

# Binance API Credentials (TESTNET)
BINANCE_API_KEY=your_testnet_api_key
BINANCE_API_SECRET=your_testnet_secret_key
BINANCE_BASE_URL=https://testnet.binance.vision
BINANCE_WS_URL=wss://testnet.binance.vision/ws
BINANCE_TESTNET=true
```

#### For Production:
```bash
# Enable Binance
ENABLE_BINANCE=true

# Binance API Credentials (PRODUCTION - CAUTION!)
BINANCE_API_KEY=your_production_api_key
BINANCE_API_SECRET=your_production_secret_key
BINANCE_BASE_URL=https://api.binance.com
BINANCE_WS_URL=wss://stream.binance.com:9443
BINANCE_TESTNET=false
```

### Step 4: Verify Access

Test your credentials:

```bash
python3 -c "
import asyncio
from binance import AsyncClient

async def test():
    # Your credentials
    API_KEY = 'YOUR_API_KEY'
    API_SECRET = 'YOUR_SECRET_KEY'

    # Initialize client (testnet=True for testnet)
    client = await AsyncClient.create(API_KEY, API_SECRET, testnet=True)

    # Get server time
    server_time = await client.get_server_time()
    print(f'✅ Success! Server time: {server_time}')

    # Get klines for BTC
    klines = await client.get_klines(symbol='BTCUSDT', interval='1h', limit=5)
    print(f'✅ Fetched {len(klines)} candles for BTCUSDT')

    await client.close_connection()

asyncio.run(test())
"
```

Expected output:
```
✅ Success! Server time: {'serverTime': 1726825600000}
✅ Fetched 5 candles for BTCUSDT
```

### Binance Features

✅ **Testnet Available**
- No real money required
- Test all features safely
- Same API as production

✅ **Data Available**
- Real-time trades
- Real-time order book
- Kline/candlestick data (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
- 1000+ cryptocurrency pairs
- Futures and spot markets

✅ **Rate Limits**
- 1200 requests/minute (REST)
- 10 connections per IP (WebSocket)
- Free API access

---

## 🌍 OANDA (Forex Data) [Optional]

### Step 1: Create OANDA Account

1. Visit [OANDA](https://www.oanda.com/)
2. Click **"Open Account"**
3. Choose **"Practice Account"** (free, no deposit)
4. Fill in registration
5. Verify email

### Step 2: Get API Keys

1. Log in to [OANDA Dashboard](https://www.oanda.com/demo-account/tpa/personal_token)
2. Go to **Manage API Access**
3. Generate new Personal Access Token
4. Copy:
   - **API Token**
   - **Account ID**

### Step 3: Add to Terminal

```bash
# Enable OANDA
ENABLE_OANDA=true

# OANDA API Credentials (Practice)
OANDA_API_KEY=your_api_token
OANDA_ACCOUNT_ID=your_account_id
OANDA_BASE_URL=https://api-fxpractice.oanda.com
OANDA_STREAM_URL=https://stream-fxpractice.oanda.com
```

### OANDA Features

✅ **Free Practice Account**
- $100,000 virtual funds
- Real-time forex data
- 70+ currency pairs

✅ **Data Available**
- Real-time quotes
- Historical candles (multiple timeframes)
- Bid/ask spreads
- Economic calendar

---

## 🔐 Security Best Practices

### 1. API Key Security

❌ **NEVER**:
- Commit API keys to git
- Share API keys publicly
- Use production keys for testing
- Store keys in code

✅ **ALWAYS**:
- Use environment variables (.env file)
- Keep .env file in .gitignore
- Use paper/testnet accounts for development
- Rotate keys periodically
- Use IP whitelisting (if available)

### 2. Permissions

**Alpaca**:
- Paper trading keys have limited permissions automatically
- Cannot withdraw or transfer funds
- Safe for development

**Binance**:
- Disable "Spot & Margin Trading" until ready
- Disable "Futures" until ready
- Enable "Enable Reading" only initially
- Whitelist your IP addresses
- Never enable withdrawal permissions for trading bots

**OANDA**:
- Practice account cannot access real funds
- Safe for development

### 3. Environment File

Ensure your `.env` file is in `.gitignore`:

```bash
# Check if .env is ignored
git check-ignore .env

# Expected output:
.env
```

If not ignored, add to `.gitignore`:

```bash
echo ".env" >> .gitignore
```

---

## ✅ Verification Checklist

Before starting the Market Data Service, verify:

- [ ] ✅ Alpaca account created (paper trading)
- [ ] ✅ Alpaca API keys generated and saved
- [ ] ✅ Alpaca keys added to `.env` file
- [ ] ✅ Alpaca `ENABLE_ALPACA=true` in `.env`
- [ ] ✅ Binance account created (testnet or production)
- [ ] ✅ Binance API keys generated and saved
- [ ] ✅ Binance keys added to `.env` file
- [ ] ✅ Binance `ENABLE_BINANCE=true` in `.env`
- [ ] ✅ `.env` file is in `.gitignore`
- [ ] ✅ Tested credentials with verification scripts

---

## 🚀 Next Steps

Once your API credentials are configured:

1. **Install dependencies**:
   ```bash
   cd agents/market-data-service
   pip install -r requirements.txt
   ```

2. **Start Market Data Service**:
   ```bash
   cd agents/market-data-service
   uvicorn main:app --host 0.0.0.0 --port 8001 --reload
   ```

3. **Verify service health**:
   ```bash
   curl http://localhost:8001/api/v1/health
   ```

4. **Check real-time data**:
   - Open http://localhost:8001/docs
   - Try the `/api/v1/subscribe` endpoint
   - Monitor logs for incoming data

---

## 🆘 Troubleshooting

### "Authentication failed" error

**Alpaca**:
- Verify API key and secret are correct
- Ensure using paper trading keys with paper trading URL
- Check for extra spaces in `.env` file
- Regenerate keys if needed

**Binance**:
- Verify API key and secret match
- Check if using testnet keys with testnet URL
- Ensure API key permissions are enabled
- Check if IP is whitelisted (if enabled)

### "Rate limit exceeded" error

**Alpaca**:
- Wait 1 minute before retrying
- Reduce request frequency
- Use WebSocket for real-time data instead of polling

**Binance**:
- Implement request throttling
- Use WebSocket streams
- Cache responses when possible

### "Invalid symbol" error

**Alpaca**:
- Use uppercase symbols: `AAPL` not `aapl`
- Use valid US stock symbols
- Check if symbol is supported on Alpaca

**Binance**:
- Use correct pair format: `BTCUSDT` not `BTC/USDT`
- Verify pair exists on Binance
- Check if using spot vs futures symbol

---

## 📚 Additional Resources

### Alpaca
- [API Documentation](https://alpaca.markets/docs/)
- [Python SDK](https://github.com/alpacahq/alpaca-trade-api-python)
- [Market Data API](https://alpaca.markets/docs/market-data/)
- [WebSocket Streaming](https://alpaca.markets/docs/market-data/streaming/)

### Binance
- [API Documentation](https://binance-docs.github.io/apidocs/spot/en/)
- [Python Connector](https://github.com/binance/binance-connector-python)
- [Testnet](https://testnet.binance.vision/)
- [API Limits](https://binance-docs.github.io/apidocs/spot/en/#limits)

### OANDA
- [API Documentation](https://developer.oanda.com/rest-live-v20/introduction/)
- [Python SDK](https://github.com/oanda/v20-python)
- [Practice Account](https://www.oanda.com/demo-account/)

---

**Need Help?** Check the logs in `/tmp/market_data_service.log` or open an issue on GitHub.

*Last updated: 2026-09-20*
