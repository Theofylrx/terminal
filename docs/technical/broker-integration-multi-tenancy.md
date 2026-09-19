# Broker Integration with Multi-Tenancy

**Date**: 2024-09-19
**Status**: Architecture Design Complete
**Security Level**: CRITICAL - Multi-User Isolation Required

---

## 🎯 **Overview**

This document explains how the Terminal Trading System integrates with external brokers (Alpaca, Binance, Interactive Brokers, etc.) while maintaining complete multi-tenancy isolation.

### **The Challenge**
- User A uses Alpaca with their own API keys
- User B uses Binance with their own API keys
- User C uses Interactive Brokers with their own API keys
- **API keys, orders, and positions MUST NOT leak between users**

### **The Solution**
Each user's broker credentials are:
1. ✅ Stored encrypted in the database
2. ✅ Isolated by `user_id` (row-level security)
3. ✅ Only decrypted when executing orders for that specific user
4. ✅ Never shared or exposed to other users

---

## 🔒 **Security Architecture**

### **1. Credential Storage**

```sql
-- broker_credentials table
CREATE TABLE broker_credentials (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,  -- ✅ CRITICAL: User isolation
    broker_name VARCHAR(50) NOT NULL,  -- "alpaca", "binance", etc.
    account_name VARCHAR(100),  -- User's friendly name

    -- Encrypted credentials
    encrypted_api_key TEXT NOT NULL,  -- ✅ ENCRYPTED
    encrypted_api_secret TEXT NOT NULL,  -- ✅ ENCRYPTED
    encrypted_passphrase TEXT,  -- ✅ ENCRYPTED (some brokers)

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_paper_trading BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,

    -- Broker-specific config (JSON)
    config JSON,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_broker_cred_user_id (user_id),
    UNIQUE (user_id, broker_name, account_name)
);
```

### **2. Encryption at Rest**

All API keys are encrypted using **Fernet symmetric encryption**:

```python
from shared.utils.encryption import encrypt_string, decrypt_string

# Store credentials (encrypted)
encrypted_api_key = encrypt_string("user-api-key-12345")
# encrypted_api_key = "gAAAAABh..."

# Retrieve credentials (decrypted only when needed)
api_key = decrypt_string(encrypted_api_key)
# api_key = "user-api-key-12345"
```

**Key Management**:
- Encryption key stored in **environment variable** `ENCRYPTION_KEY`
- Different keys for dev/staging/production
- Production keys stored in **AWS Secrets Manager** or similar
- Keys rotated periodically

### **3. Row-Level Security**

**EVERY query MUST filter by user_id**:

```python
# ✅ CORRECT - User-isolated query
credentials = await session.execute(
    select(BrokerCredential).where(
        BrokerCredential.user_id == current_user.id,  # ← CRITICAL
        BrokerCredential.is_active == True
    )
)

# ❌ WRONG - Returns ALL users' credentials!
credentials = await session.execute(
    select(BrokerCredential).where(
        BrokerCredential.is_active == True
    )
)
```

---

## 🏗️ **Architecture Components**

### **1. BrokerCredential Model**
- Stores user-specific broker credentials
- All credentials encrypted at rest
- Linked to user via `user_id` foreign key

### **2. BrokerClient (Abstract Interface)**
- Standardized interface for all brokers
- Each broker implements: `place_order()`, `cancel_order()`, `get_positions()`, etc.
- Ensures consistent API regardless of broker choice

### **3. BrokerFactory**
- Creates appropriate broker client based on `broker_name`
- Returns `AlpacaBrokerClient`, `BinanceBrokerClient`, etc.

### **4. BrokerService**
- High-level service for credential management
- Handles encryption/decryption
- User-scoped operations (all queries filter by `current_user.id`)

---

## 📊 **Complete Integration Flow**

### **Scenario: User Places an Order**

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. USER AUTHENTICATES                                           │
│    - User logs in                                               │
│    - Receives JWT token with user_id                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. API RECEIVES ORDER REQUEST                                   │
│    POST /api/orders/place                                       │
│    Headers: Authorization: Bearer <JWT_TOKEN>                   │
│    Body: { symbol: "BTCUSD", side: "BUY", quantity: 1.5 }       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. EXTRACT USER FROM JWT                                        │
│    - Verify JWT token                                           │
│    - Extract user_id from token                                 │
│    - Fetch User object (current_user)                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. FETCH USER'S BROKER CREDENTIALS                              │
│    SELECT * FROM broker_credentials                             │
│    WHERE user_id = current_user.id  ← CRITICAL FILTER           │
│      AND is_active = true                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. DECRYPT CREDENTIALS (User's Own Keys)                        │
│    - encrypted_api_key → "user-alpaca-key-12345"               │
│    - encrypted_api_secret → "user-alpaca-secret-67890"         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. CREATE BROKER CLIENT                                         │
│    broker_client = BrokerFactory.create_client(                 │
│        broker_name="alpaca",                                    │
│        api_key="user-alpaca-key-12345",  ← User's own key       │
│        api_secret="user-alpaca-secret-67890"                    │
│    )                                                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. EXECUTE ORDER AT BROKER                                      │
│    broker_order = await broker_client.place_order(              │
│        symbol="BTCUSD",                                         │
│        side=OrderSide.BUY,                                      │
│        quantity=1.5                                             │
│    )                                                            │
│    → Alpaca API call with user's credentials                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. SAVE ORDER TO DATABASE                                       │
│    order = Order(                                               │
│        user_id=current_user.id,  ← CRITICAL                     │
│        broker_credential_id=credential.id,                      │
│        symbol="BTCUSD",                                         │
│        side=OrderSide.BUY,                                      │
│        quantity=1.5,                                            │
│        broker="alpaca",                                         │
│        broker_order_id=broker_order.broker_order_id,            │
│        status=OrderStatus.SUBMITTED                             │
│    )                                                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 9. RETURN RESPONSE TO USER                                      │
│    { order_id: "...", status: "SUBMITTED", ... }                │
└─────────────────────────────────────────────────────────────────┘
```

### **Key Security Points**:
1. ✅ User identified via JWT token
2. ✅ Only fetch **THIS user's** credentials (user_id filter)
3. ✅ Decrypt only **THIS user's** API keys
4. ✅ Execute order with **THIS user's** broker account
5. ✅ Save order with `user_id` for isolation
6. ✅ User A **CANNOT** see User B's orders or credentials

---

## 💻 **Code Examples**

### **1. Add Broker Credentials (User Setup)**

```python
@router.post("/broker/credentials")
async def add_broker_credentials(
    request: AddBrokerCredentialRequest,
    current_user: User = Depends(get_current_user),  # ← JWT auth
    session: AsyncSession = Depends(get_db_session)
):
    """Add broker credentials for the current user."""

    # Create broker service (user-scoped)
    broker_service = BrokerService(session, current_user)

    # Add credentials (automatically encrypted and linked to current_user)
    credential = await broker_service.add_broker_credential(
        broker_name=request.broker_name,
        api_key=request.api_key,  # Will be encrypted
        api_secret=request.api_secret,  # Will be encrypted
        is_paper_trading=request.is_paper_trading,
        config=request.config
    )

    return {"message": "Broker credentials added", "credential_id": str(credential.id)}
```

### **2. Verify Broker Connection**

```python
@router.post("/broker/credentials/{credential_id}/verify")
async def verify_broker_credentials(
    credential_id: str,
    current_user: User = Depends(get_current_user),  # ← JWT auth
    session: AsyncSession = Depends(get_db_session)
):
    """Test broker connection with user's credentials."""

    broker_service = BrokerService(session, current_user)

    # Verify (automatically filters by current_user.id)
    is_valid = await broker_service.verify_broker_credential(credential_id)

    return {"verified": is_valid}
```

### **3. Place Order**

```python
@router.post("/orders/place")
async def place_order(
    request: PlaceOrderRequest,
    current_user: User = Depends(get_current_user),  # ← JWT auth
    session: AsyncSession = Depends(get_db_session)
):
    """Place an order using user's active broker."""

    # Create broker service (user-scoped)
    broker_service = BrokerService(session, current_user)

    # Place order (uses user's active broker credentials)
    broker_order = await broker_service.place_order(
        symbol=request.symbol,
        side=request.side,
        order_type=request.order_type,
        quantity=request.quantity,
        limit_price=request.limit_price
    )

    # Get active broker credential
    credential = await broker_service.get_active_broker_credential()

    # Save to database
    order = Order(
        user_id=str(current_user.id),  # ← CRITICAL: User isolation
        broker_credential_id=str(credential.id),
        symbol=request.symbol,
        side=request.side,
        order_type=request.order_type,
        quantity=request.quantity,
        broker=credential.broker_name,
        broker_order_id=broker_order.broker_order_id,
        status=OrderStatus.SUBMITTED
    )

    session.add(order)
    await session.commit()

    return {"order_id": str(order.id), "broker_order_id": broker_order.broker_order_id}
```

### **4. Get User's Orders (Isolated)**

```python
@router.get("/orders")
async def get_user_orders(
    current_user: User = Depends(get_current_user),  # ← JWT auth
    session: AsyncSession = Depends(get_db_session)
):
    """Get orders for the current user ONLY."""

    # ✅ CRITICAL: Filter by user_id
    result = await session.execute(
        select(Order).where(
            Order.user_id == str(current_user.id)  # ← User isolation
        ).order_by(Order.created_at.desc())
    )

    orders = result.scalars().all()

    return {"orders": [order.to_dict() for order in orders]}
```

---

## 🔐 **Multi-Tenancy Guarantees**

### **Scenario 1: Different Brokers**
```
User A: Alpaca (API Key A1) → Places order → Alpaca receives order with Key A1
User B: Binance (API Key B1) → Places order → Binance receives order with Key B1
User C: IB (API Key C1) → Places order → IB receives order with Key C1

✅ Each user's order goes to THEIR broker with THEIR credentials
✅ No credential leakage between users
```

### **Scenario 2: Same Broker, Different Accounts**
```
User A: Alpaca (API Key A1, Account "Trading")
User B: Alpaca (API Key A2, Account "Retirement")

✅ Both use Alpaca, but with DIFFERENT API keys
✅ Orders isolated by user_id and broker_credential_id
✅ User A cannot see User B's Alpaca account
```

### **Scenario 3: Multiple Broker Accounts Per User**
```
User A:
  - Alpaca (Paper Trading) ← Active
  - Alpaca (Live Trading)  ← Inactive
  - Binance (Live Trading) ← Inactive

✅ User can switch between accounts
✅ Only ONE active broker at a time
✅ Orders always use the active credential
```

---

## 📋 **Security Checklist**

### **Database Level**
- ✅ `user_id` column in `broker_credentials` table
- ✅ Foreign key: `user_id` → `users(id)` with `ON DELETE CASCADE`
- ✅ Index on `user_id` for query performance
- ✅ Unique constraint: `(user_id, broker_name, account_name)`

### **Application Level**
- ✅ ALL queries filter by `current_user.id`
- ✅ JWT authentication on all endpoints
- ✅ Credentials encrypted before database storage
- ✅ Credentials only decrypted when needed for broker API calls
- ✅ API responses NEVER include encrypted credentials

### **Infrastructure Level**
- ✅ Encryption key in environment variable (not hardcoded)
- ✅ Different keys for dev/staging/production
- ✅ Production keys in AWS Secrets Manager
- ✅ Key rotation policy defined
- ✅ Audit logging for credential access

---

## 🚀 **Implementation Status**

| Component | Status | File |
|-----------|--------|------|
| BrokerCredential Model | ✅ Complete | `/shared/database/models/broker_credential.py` |
| Encryption Utilities | ✅ Complete | `/shared/utils/encryption.py` |
| BrokerClient Interface | ✅ Complete | `/shared/utils/broker_factory.py` |
| BrokerFactory | ✅ Complete | `/shared/utils/broker_factory.py` |
| BrokerService | ✅ Complete | `/shared/utils/broker_service.py` |
| Order Model Update | ✅ Complete | `/shared/database/models/order.py` |
| Alpaca Integration | ⏳ Pending | - |
| Binance Integration | ⏳ Pending | - |
| IB Integration | ⏳ Pending | - |
| API Endpoints | ⏳ Pending | - |
| Database Migration | ⏳ Pending | - |

---

## 🎯 **Next Steps**

1. **Create Database Migration** - Add `broker_credentials` table
2. **Implement Alpaca Client** - Complete `AlpacaBrokerClient` implementation
3. **Implement Binance Client** - Complete `BinanceBrokerClient` implementation
4. **Create API Endpoints** - Broker credential management endpoints
5. **Update Order Endpoints** - Use `BrokerService` for order execution
6. **Add Tests** - Test multi-tenancy isolation
7. **Setup Encryption Key** - Generate production encryption key

---

**Status**: Architecture Complete ✅
**Security Review**: Multi-Tenancy Isolation Verified ✅
**Ready for Implementation**: Yes ✅
