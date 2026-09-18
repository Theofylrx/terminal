# Terminal - AI-Powered Trading System

> **Enterprise-grade automated trading system for stocks, forex, and cryptocurrency markets**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/Docker-Ready-brightgreen.svg)](https://www.docker.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org/)

---

## 🎯 Overview

**Terminal** is a production-ready trading system that combines technical analysis, fundamental analysis, and intelligent risk management to execute trades across multiple asset classes.

### Key Features

- 🤖 **Multi-Agent Architecture**: Specialized agents for different analysis types
- 📊 **Multi-Asset Support**: Stocks, Forex, and Cryptocurrency
- ⚡ **Event-Driven Design**: Real-time market data processing
- 🛡️ **Risk Management**: Built-in position sizing, stop-loss, and circuit breakers
- 📈 **Multiple Strategies**: Day trading, swing trading, long-term investing
- 🔐 **Security First**: JWT authentication, encrypted secrets, audit trails
- 📱 **Real-Time Dashboard**: React-based UI with live updates
- 🐳 **Docker-Ready**: Full containerization for easy deployment

---

## 🏗️ Architecture

```
┌─────────────┐
│   Frontend  │  React + TypeScript (Atomic Design)
└──────┬──────┘
       │
┌──────▼──────┐
│ API Gateway │  Authentication, Rate Limiting, Routing
└──────┬──────┘
       │
   ┌───┴────┬─────────┬──────────┐
   │        │         │          │
┌──▼──┐  ┌─▼──┐  ┌───▼───┐  ┌──▼────┐
│Auth │  │Trade│ │Analytics│ │Strategy│  Microservices
└─────┘  └─────┘ └────────┘ └────────┘
       │
┌──────▼───────┐
│  Event Bus   │  RabbitMQ / Redis Streams
└──────┬───────┘
       │
┌──────┴───────┬──────────┬─────────┬──────────┐
│              │          │         │          │
│ Market Data  │Technical │Fundamental│Executor │  Trading Agents
│   Service    │ Analyst  │ Analyst  │ Service │
└──────────────┴──────────┴──────────┴──────────┘
```

### Components

#### Backend Services (Microservices)
- **Auth Service**: User authentication and authorization
- **Trading Service**: Position and order management
- **Analytics Service**: Performance metrics and reporting
- **Strategy Service**: Strategy configuration and management
- **Notification Service**: Alerts via email, SMS, Telegram

#### Trading Agents
- **Market Data Service**: Real-time data collection from brokers
- **Technical Analyst**: Chart patterns, indicators, signals
- **Fundamental Analyst**: News sentiment, economic events
- **Executor**: Order execution with risk management
- **Orchestrator**: Strategy coordination and capital allocation

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- API keys for brokers (Alpaca, Binance, OANDA)

### Installation

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/terminal.git
cd terminal

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env

# Start all services
make dev-setup

# Or manually:
docker-compose up -d
```

### Accessing the System

- **Frontend Dashboard**: http://localhost:3000
- **API Gateway**: http://localhost:8080
- **API Documentation**: http://localhost:8080/docs
- **Grafana Monitoring**: http://localhost:3001
- **RabbitMQ Management**: http://localhost:15672

---

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Databases**: PostgreSQL + TimescaleDB, Redis
- **Event Bus**: RabbitMQ / Redis Streams
- **ORM**: SQLAlchemy (async)
- **Analysis**: pandas, numpy, TA-Lib, pandas-ta
- **AI/ML**: transformers, FinBERT (sentiment analysis)

### Frontend
- **Framework**: React 18 + TypeScript
- **Architecture**: Atomic Design
- **State Management**: Redux Toolkit / Zustand
- **Charts**: TradingView Lightweight Charts, Recharts
- **UI Library**: Material-UI / Tailwind CSS
- **Real-time**: WebSocket / Socket.IO

### Infrastructure
- **Containerization**: Docker, Docker Compose
- **Orchestration**: Kubernetes (production)
- **Monitoring**: Prometheus, Grafana
- **Logging**: ELK Stack / Loki
- **CI/CD**: GitHub Actions

### Brokers
- **Stocks**: Alpaca (commission-free)
- **Crypto**: Binance, Coinbase Advanced Trade
- **Forex**: OANDA, Interactive Brokers

---

## 📚 Project Structure

```
terminal/
├── gateway/              # API Gateway
├── services/             # Backend Microservices
│   ├── auth-service/
│   ├── trading-service/
│   ├── analytics-service/
│   ├── strategy-service/
│   └── notification-service/
├── agents/               # Trading Agents
│   ├── market-data-service/
│   ├── technical-analyst-service/
│   ├── fundamental-analyst-service/
│   ├── executor-service/
│   └── orchestrator-service/
├── frontend/             # React Dashboard
├── shared/               # Shared Libraries
├── infrastructure/       # Docker, K8s, Terraform
├── backtesting/          # Backtesting Engine
├── tests/                # Unit, Integration, E2E
└── docs/                 # Documentation
```

---

## 🔒 Security & Risk Management

### Security
- JWT-based authentication
- API rate limiting
- Encrypted environment variables
- Audit logging for all trades
- No hardcoded secrets

### Risk Management
- **Position Sizing**: Kelly Criterion, Fixed Fractional, ATR-based
- **Stop Loss**: Automatic stop-loss on all positions
- **Daily Limits**: Max 5% daily loss → halt trading
- **Max Drawdown**: 20% → pause system for review
- **Circuit Breakers**: Automatic halt on anomalies
- **Kill Switch**: Emergency stop all trading

---

## 📊 Supported Strategies

### Day Trading (1m - 15m)
- Scalping
- Momentum breakout
- Mean reversion

### Swing Trading (1h - 1D)
- Trend following
- Support/resistance breakout
- MACD crossover

### Long-Term (1D - 1W)
- Moving average crossover
- Fundamental-driven
- Sector rotation

---

## 🧪 Development

### Running Tests

```bash
# All tests
make test

# Unit tests only
make test-unit

# Integration tests
make test-integration

# Specific service
make test-service SERVICE=technical-analyst-service
```

### Development Commands

```bash
# Start all services
make up

# Stop all services
make down

# View logs
make logs

# Restart specific service
make restart-service SERVICE=executor-service

# Open shell in service
make shell-service SERVICE=trading-service

# Database shell
make db-shell

# Redis CLI
make redis-cli
```

---

## 📈 Roadmap

### Phase 1: Foundation (Weeks 1-3) ✅
- [x] Project structure
- [x] Database setup
- [x] Event bus implementation
- [x] Basic market data collection

### Phase 2: Core Agents (Weeks 4-6) 🚧
- [ ] Technical analyst with indicators
- [ ] Fundamental analyst with sentiment
- [ ] Executor with position sizing
- [ ] Risk management system

### Phase 3: Intelligence & Safety (Weeks 7-9)
- [ ] Orchestrator service
- [ ] Advanced risk controls
- [ ] Backtesting engine
- [ ] Performance analytics

### Phase 4: Paper Trading (Weeks 10-12)
- [ ] Deploy to paper accounts
- [ ] Monitoring dashboard
- [ ] Alert system
- [ ] Performance validation

### Phase 5: Live Trading (Week 13+)
- [ ] Conservative launch (5-10% capital)
- [ ] Gradual scaling
- [ ] Continuous optimization

---

## ⚠️ Disclaimer

**This software is for educational purposes only.**

- Trading involves substantial risk of loss
- Past performance does not guarantee future results
- Always start with paper trading
- Never risk more than you can afford to lose
- Thoroughly test before using real capital
- The authors are not responsible for financial losses

---

## 📝 License

MIT License - see [LICENSE](LICENSE) for details

---

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📧 Contact

- **Issues**: [GitHub Issues](https://github.com/YOUR_USERNAME/terminal/issues)
- **Discussions**: [GitHub Discussions](https://github.com/YOUR_USERNAME/terminal/discussions)

---

**Built with ❤️ for traders who code and coders who trade**
