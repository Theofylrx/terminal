"""Broker Service - Manages user broker credentials and order execution."""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shared.database.models.broker_credential import BrokerCredential
from shared.database.models.user import User
from shared.utils.encryption import encrypt_string, decrypt_string
from shared.utils.broker_factory import BrokerFactory, BrokerClient, BrokerOrder, OrderSide, OrderType


class BrokerService:
    """
    Service for managing broker credentials and executing orders.

    CRITICAL SECURITY:
    - All operations are user-scoped (filter by user_id)
    - Credentials are encrypted at rest
    - API keys only decrypted when needed for broker API calls
    - No credential leakage between users
    """

    def __init__(self, session: AsyncSession, current_user: User):
        """
        Initialize broker service.

        Args:
            session: Database session
            current_user: Authenticated user (from JWT)
        """
        self.session = session
        self.current_user = current_user

    async def add_broker_credential(
        self,
        broker_name: str,
        api_key: str,
        api_secret: str,
        account_name: Optional[str] = None,
        passphrase: Optional[str] = None,
        is_paper_trading: bool = True,
        config: Optional[dict] = None,
    ) -> BrokerCredential:
        """
        Add new broker credentials for the current user.

        Args:
            broker_name: Name of the broker (e.g., "alpaca", "binance")
            api_key: Plain text API key (will be encrypted)
            api_secret: Plain text API secret (will be encrypted)
            account_name: User's friendly name for this account
            passphrase: Optional passphrase (some brokers require this)
            is_paper_trading: Whether this is a paper trading account
            config: Broker-specific configuration

        Returns:
            Created BrokerCredential

        Raises:
            Exception if broker not supported or credentials invalid
        """
        # Encrypt credentials before storage
        encrypted_api_key = encrypt_string(api_key)
        encrypted_api_secret = encrypt_string(api_secret)
        encrypted_passphrase = encrypt_string(passphrase) if passphrase else None

        # Create credential record
        credential = BrokerCredential(
            user_id=str(self.current_user.id),  # ← CRITICAL: User isolation
            broker_name=broker_name,
            account_name=account_name or f"{broker_name}_account",
            encrypted_api_key=encrypted_api_key,
            encrypted_api_secret=encrypted_api_secret,
            encrypted_passphrase=encrypted_passphrase,
            is_paper_trading=is_paper_trading,
            is_active=False,  # Not active until verified
            is_verified=False,
            config=config,
        )

        self.session.add(credential)
        await self.session.commit()
        await self.session.refresh(credential)

        return credential

    async def verify_broker_credential(self, credential_id: str) -> bool:
        """
        Verify broker credentials by testing connection.

        Args:
            credential_id: ID of the credential to verify

        Returns:
            True if verification successful

        Raises:
            Exception if verification fails or credential not found
        """
        # Fetch credential (with user isolation)
        result = await self.session.execute(
            select(BrokerCredential).where(
                BrokerCredential.id == credential_id,
                BrokerCredential.user_id == str(self.current_user.id),  # ← CRITICAL: User isolation
            )
        )
        credential = result.scalar_one_or_none()

        if not credential:
            raise ValueError("Broker credential not found")

        # Decrypt credentials
        api_key = decrypt_string(credential.encrypted_api_key)
        api_secret = decrypt_string(credential.encrypted_api_secret)

        # Create broker client
        broker_client = BrokerFactory.create_client(
            broker_name=credential.broker_name,
            api_key=api_key,
            api_secret=api_secret,
            config=credential.config,
        )

        # Test connection
        try:
            is_valid = await broker_client.verify_connection()

            if is_valid:
                credential.is_verified = True
                credential.verification_error = None
                await self.session.commit()

            return is_valid

        except Exception as e:
            credential.is_verified = False
            credential.verification_error = str(e)
            await self.session.commit()
            raise

    async def set_active_broker(self, credential_id: str) -> BrokerCredential:
        """
        Set a broker credential as the active one for this user.

        Args:
            credential_id: ID of the credential to activate

        Returns:
            Activated BrokerCredential

        Raises:
            ValueError if credential not found or not verified
        """
        # Fetch credential (with user isolation)
        result = await self.session.execute(
            select(BrokerCredential).where(
                BrokerCredential.id == credential_id,
                BrokerCredential.user_id == str(self.current_user.id),  # ← CRITICAL: User isolation
            )
        )
        credential = result.scalar_one_or_none()

        if not credential:
            raise ValueError("Broker credential not found")

        if not credential.is_verified:
            raise ValueError("Broker credential not verified. Please verify first.")

        # Deactivate all other credentials for this user
        result = await self.session.execute(
            select(BrokerCredential).where(
                BrokerCredential.user_id == str(self.current_user.id),
                BrokerCredential.is_active == True,
            )
        )
        active_credentials = result.scalars().all()

        for active_cred in active_credentials:
            active_cred.is_active = False

        # Activate the selected credential
        credential.is_active = True
        await self.session.commit()
        await self.session.refresh(credential)

        return credential

    async def get_active_broker_credential(self) -> Optional[BrokerCredential]:
        """
        Get the active broker credential for the current user.

        Returns:
            Active BrokerCredential or None if no active broker

        This is used for order execution.
        """
        result = await self.session.execute(
            select(BrokerCredential).where(
                BrokerCredential.user_id == str(self.current_user.id),  # ← CRITICAL: User isolation
                BrokerCredential.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def get_broker_client(self) -> BrokerClient:
        """
        Get broker client for the current user's active broker.

        Returns:
            BrokerClient instance

        Raises:
            ValueError if no active broker configured
        """
        credential = await self.get_active_broker_credential()

        if not credential:
            raise ValueError("No active broker configured. Please configure a broker first.")

        # Decrypt credentials
        api_key = decrypt_string(credential.encrypted_api_key)
        api_secret = decrypt_string(credential.encrypted_api_secret)

        # Create and return broker client
        return BrokerFactory.create_client(
            broker_name=credential.broker_name,
            api_key=api_key,
            api_secret=api_secret,
            config=credential.config,
        )

    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> BrokerOrder:
        """
        Place an order using the user's active broker.

        This is the main entry point for order execution.
        It automatically:
        1. Fetches user's active broker credentials
        2. Decrypts API keys
        3. Creates broker client
        4. Executes order
        5. Returns standardized response

        Args:
            symbol: Trading symbol
            side: Buy or sell
            order_type: Market, limit, stop, etc.
            quantity: Order quantity
            limit_price: Limit price (for limit orders)
            stop_price: Stop price (for stop orders)

        Returns:
            BrokerOrder with order details

        Raises:
            ValueError if no active broker or order fails
        """
        # Get broker client (with user's credentials)
        broker_client = await self.get_broker_client()

        # Place order through broker
        broker_order = await broker_client.place_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            limit_price=limit_price,
            stop_price=stop_price,
        )

        return broker_order

    async def get_user_broker_credentials(self) -> List[BrokerCredential]:
        """
        Get all broker credentials for the current user.

        Returns:
            List of BrokerCredential objects (without decrypted secrets)
        """
        result = await self.session.execute(
            select(BrokerCredential).where(
                BrokerCredential.user_id == str(self.current_user.id)  # ← CRITICAL: User isolation
            )
        )
        return result.scalars().all()
