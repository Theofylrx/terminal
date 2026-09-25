#!/bin/bash
# Setup API Credentials for Terminal Trading System
# This script helps you configure Alpaca and Binance API credentials

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}║           Terminal AI Trading System                          ║${NC}"
echo -e "${BLUE}║           API Credentials Setup                               ║${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: .env file not found at $ENV_FILE${NC}"
    echo -e "${YELLOW}Please create one from .env.example:${NC}"
    echo "  cp .env.example .env"
    exit 1
fi

echo -e "${GREEN}✓${NC} Found .env file at: $ENV_FILE"
echo ""

# Function to update .env file
update_env() {
    local key=$1
    local value=$2
    local env_file=$3

    # Escape special characters in value
    escaped_value=$(echo "$value" | sed 's/[&/\]/\\&/g')

    # Check if key exists
    if grep -q "^${key}=" "$env_file"; then
        # Update existing key
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s/^${key}=.*/${key}=${escaped_value}/" "$env_file"
        else
            # Linux
            sed -i "s/^${key}=.*/${key}=${escaped_value}/" "$env_file"
        fi
        echo -e "${GREEN}✓${NC} Updated $key"
    else
        # Add new key
        echo "${key}=${value}" >> "$env_file"
        echo -e "${GREEN}✓${NC} Added $key"
    fi
}

# ===========================
# Alpaca Setup
# ===========================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Alpaca Configuration (Stock Market Data)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Alpaca provides free real-time US stock market data with paper trading."
echo "You need an Alpaca paper trading account (free, no deposit required)."
echo ""
echo "📚 Setup Guide: docs/guides/API_CREDENTIALS_SETUP.md"
echo "🔗 Get API Keys: https://app.alpaca.markets/paper/dashboard/overview"
echo ""

read -p "Do you want to configure Alpaca? (y/n): " configure_alpaca

if [[ $configure_alpaca =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${YELLOW}Alpaca API Key Setup:${NC}"
    echo "1. Go to: https://app.alpaca.markets/paper/dashboard/overview"
    echo "2. Navigate to 'Your API Keys'"
    echo "3. Under 'Paper Trading', click 'Generate New Key'"
    echo "4. Copy both the API Key ID and Secret Key"
    echo ""

    read -p "Enter your Alpaca API Key ID: " alpaca_key
    read -s -p "Enter your Alpaca Secret Key: " alpaca_secret
    echo ""

    if [ -z "$alpaca_key" ] || [ -z "$alpaca_secret" ]; then
        echo -e "${RED}✗${NC} Error: API credentials cannot be empty"
    else
        update_env "ENABLE_ALPACA" "true" "$ENV_FILE"
        update_env "ALPACA_API_KEY" "$alpaca_key" "$ENV_FILE"
        update_env "ALPACA_API_SECRET" "$alpaca_secret" "$ENV_FILE"
        update_env "ALPACA_BASE_URL" "https://paper-api.alpaca.markets" "$ENV_FILE"
        update_env "ALPACA_PAPER" "true" "$ENV_FILE"

        echo ""
        echo -e "${GREEN}✓${NC} Alpaca credentials configured successfully!"

        # Test credentials
        echo ""
        read -p "Would you like to test the Alpaca connection now? (y/n): " test_alpaca

        if [[ $test_alpaca =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}Testing Alpaca connection...${NC}"

            python3 << EOF
try:
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame
    from datetime import datetime, timedelta

    client = StockHistoricalDataClient("$alpaca_key", "$alpaca_secret")

    request = StockBarsRequest(
        symbol_or_symbols='AAPL',
        timeframe=TimeFrame.Hour,
        start=datetime.now() - timedelta(days=1),
        end=datetime.now()
    )

    bars = client.get_stock_bars(request)
    count = len(bars['AAPL'])
    print(f"✅ Success! Fetched {count} bars for AAPL")
    print(f"✅ Alpaca connection is working!")

except Exception as e:
    print(f"❌ Error: {e}")
    print(f"❌ Please check your API credentials and try again")
    exit(1)
EOF
        fi
    fi
else
    echo -e "${YELLOW}⊘${NC} Skipping Alpaca configuration"
fi

echo ""

# ===========================
# Binance Setup
# ===========================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Binance Configuration (Cryptocurrency Data)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Binance provides cryptocurrency market data and trading."
echo "You can use the free testnet for development (recommended)."
echo ""
echo "📚 Setup Guide: docs/guides/API_CREDENTIALS_SETUP.md"
echo "🔗 Testnet Keys: https://testnet.binance.vision/"
echo "🔗 Production Keys: https://www.binance.com/en/my/settings/api-management"
echo ""

read -p "Do you want to configure Binance? (y/n): " configure_binance

if [[ $configure_binance =~ ^[Yy]$ ]]; then
    echo ""
    echo "Which Binance environment do you want to use?"
    echo "  1) Testnet (recommended for development, no real money)"
    echo "  2) Production (CAUTION: real trading, requires account)"
    read -p "Enter choice (1 or 2): " binance_env

    if [ "$binance_env" == "1" ]; then
        echo ""
        echo -e "${YELLOW}Binance Testnet Setup:${NC}"
        echo "1. Go to: https://testnet.binance.vision/"
        echo "2. Log in with GitHub"
        echo "3. Click 'Generate HMAC_SHA256 Key'"
        echo "4. Copy both API Key and Secret Key"
        echo ""

        read -p "Enter your Binance Testnet API Key: " binance_key
        read -s -p "Enter your Binance Testnet Secret Key: " binance_secret
        echo ""

        if [ -z "$binance_key" ] || [ -z "$binance_secret" ]; then
            echo -e "${RED}✗${NC} Error: API credentials cannot be empty"
        else
            update_env "ENABLE_BINANCE" "true" "$ENV_FILE"
            update_env "BINANCE_API_KEY" "$binance_key" "$ENV_FILE"
            update_env "BINANCE_API_SECRET" "$binance_secret" "$ENV_FILE"
            update_env "BINANCE_BASE_URL" "https://testnet.binance.vision" "$ENV_FILE"
            update_env "BINANCE_WS_URL" "wss://testnet.binance.vision/ws" "$ENV_FILE"
            update_env "BINANCE_TESTNET" "true" "$ENV_FILE"

            echo ""
            echo -e "${GREEN}✓${NC} Binance Testnet credentials configured successfully!"

            # Test credentials
            echo ""
            read -p "Would you like to test the Binance connection now? (y/n): " test_binance

            if [[ $test_binance =~ ^[Yy]$ ]]; then
                echo -e "${YELLOW}Testing Binance connection...${NC}"

                python3 << EOF
import asyncio

async def test():
    try:
        from binance import AsyncClient

        client = await AsyncClient.create("$binance_key", "$binance_secret", testnet=True)

        # Get server time
        server_time = await client.get_server_time()
        print(f"✅ Success! Connected to Binance Testnet")
        print(f"✅ Server time: {server_time['serverTime']}")

        # Get klines
        klines = await client.get_klines(symbol='BTCUSDT', interval='1h', limit=5)
        print(f"✅ Fetched {len(klines)} candles for BTCUSDT")

        await client.close_connection()

    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"❌ Please check your API credentials and try again")
        exit(1)

asyncio.run(test())
EOF
            fi
        fi

    elif [ "$binance_env" == "2" ]; then
        echo ""
        echo -e "${RED}⚠️  WARNING: Production Environment${NC}"
        echo -e "${RED}This will use REAL MONEY and execute REAL TRADES!${NC}"
        echo ""
        read -p "Are you absolutely sure? Type 'YES' to continue: " confirm

        if [ "$confirm" == "YES" ]; then
            echo ""
            echo -e "${YELLOW}Binance Production Setup:${NC}"
            echo "1. Go to: https://www.binance.com/en/my/settings/api-management"
            echo "2. Create new API key"
            echo "3. Enable 'Enable Reading' permission"
            echo "4. DO NOT enable trading permissions until ready"
            echo "5. Set up IP whitelist for security"
            echo ""

            read -p "Enter your Binance Production API Key: " binance_key
            read -s -p "Enter your Binance Production Secret Key: " binance_secret
            echo ""

            if [ -z "$binance_key" ] || [ -z "$binance_secret" ]; then
                echo -e "${RED}✗${NC} Error: API credentials cannot be empty"
            else
                update_env "ENABLE_BINANCE" "true" "$ENV_FILE"
                update_env "BINANCE_API_KEY" "$binance_key" "$ENV_FILE"
                update_env "BINANCE_API_SECRET" "$binance_secret" "$ENV_FILE"
                update_env "BINANCE_BASE_URL" "https://api.binance.com" "$ENV_FILE"
                update_env "BINANCE_WS_URL" "wss://stream.binance.com:9443" "$ENV_FILE"
                update_env "BINANCE_TESTNET" "false" "$ENV_FILE"

                echo ""
                echo -e "${GREEN}✓${NC} Binance Production credentials configured"
                echo -e "${YELLOW}⚠️  Remember to enable trading permissions when ready${NC}"
            fi
        else
            echo -e "${YELLOW}⊘${NC} Production setup cancelled"
        fi
    else
        echo -e "${RED}✗${NC} Invalid choice"
    fi
else
    echo -e "${YELLOW}⊘${NC} Skipping Binance configuration"
fi

echo ""

# ===========================
# Summary
# ===========================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Configuration Summary${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check what's enabled
ALPACA_ENABLED=$(grep "^ENABLE_ALPACA=" "$ENV_FILE" | cut -d'=' -f2)
BINANCE_ENABLED=$(grep "^ENABLE_BINANCE=" "$ENV_FILE" | cut -d'=' -f2)

echo "Enabled Connectors:"
if [ "$ALPACA_ENABLED" == "true" ]; then
    echo -e "  ${GREEN}✓${NC} Alpaca (Stock Market Data)"
else
    echo -e "  ${YELLOW}⊘${NC} Alpaca (disabled)"
fi

if [ "$BINANCE_ENABLED" == "true" ]; then
    BINANCE_TESTNET=$(grep "^BINANCE_TESTNET=" "$ENV_FILE" | cut -d'=' -f2)
    if [ "$BINANCE_TESTNET" == "true" ]; then
        echo -e "  ${GREEN}✓${NC} Binance Testnet (Crypto Data)"
    else
        echo -e "  ${GREEN}✓${NC} Binance Production (Crypto Data) ${RED}[LIVE TRADING]${NC}"
    fi
else
    echo -e "  ${YELLOW}⊘${NC} Binance (disabled)"
fi

echo ""
echo -e "${GREEN}✓${NC} Configuration saved to: $ENV_FILE"
echo ""

# Next steps
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Next Steps${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "1. Start the Market Data Service:"
echo "   cd agents/market-data-service"
echo "   uvicorn main:app --host 0.0.0.0 --port 8001 --reload"
echo ""
echo "2. Verify service is running:"
echo "   curl http://localhost:8001/api/v1/health"
echo ""
echo "3. Subscribe to symbols and start receiving data"
echo ""
echo "4. View API documentation:"
echo "   http://localhost:8001/docs"
echo ""
echo -e "${GREEN}Setup complete! Happy trading! 📈${NC}"
echo ""
