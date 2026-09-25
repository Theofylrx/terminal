"""
Auto-Trading Session Repository
Handles database operations for auto-trading sessions
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database.models.auto_trading_session import AutoTradingSession, SessionStatus


class AutoTradingSessionRepository:
    """Repository for auto-trading session operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(self, session_obj: AutoTradingSession) -> AutoTradingSession:
        """
        Create new auto-trading session.

        Args:
            session_obj: AutoTradingSession instance

        Returns:
            Created session
        """
        self.session.add(session_obj)
        await self.session.commit()
        await self.session.refresh(session_obj)
        return session_obj

    async def get_by_id(self, session_id: str) -> Optional[AutoTradingSession]:
        """
        Get session by ID.

        Args:
            session_id: Session ID

        Returns:
            Session if found, None otherwise
        """
        result = await self.session.execute(
            select(AutoTradingSession).where(AutoTradingSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_by_config(self, config_id: str) -> Optional[AutoTradingSession]:
        """
        Get active session for a configuration.

        Args:
            config_id: Configuration ID

        Returns:
            Active session if found
        """
        result = await self.session.execute(
            select(AutoTradingSession).where(
                and_(
                    AutoTradingSession.config_id == config_id,
                    AutoTradingSession.status == SessionStatus.ACTIVE
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_active_sessions(self) -> List[AutoTradingSession]:
        """
        Get all active sessions.

        Returns:
            List of active sessions
        """
        result = await self.session.execute(
            select(AutoTradingSession).where(
                AutoTradingSession.status == SessionStatus.ACTIVE
            )
        )
        return list(result.scalars().all())

    async def get_user_sessions(
        self, user_id: str, status: Optional[SessionStatus] = None
    ) -> List[AutoTradingSession]:
        """
        Get sessions for a user, optionally filtered by status.

        Args:
            user_id: User ID
            status: Optional status filter

        Returns:
            List of user's sessions
        """
        query = select(AutoTradingSession).where(
            AutoTradingSession.user_id == user_id
        )

        if status:
            query = query.where(AutoTradingSession.status == status)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, session_obj: AutoTradingSession) -> AutoTradingSession:
        """
        Update session.

        Args:
            session_obj: Session to update

        Returns:
            Updated session
        """
        await self.session.commit()
        await self.session.refresh(session_obj)
        return session_obj

    async def record_trade(
        self, session_id: str, pnl: float
    ) -> Optional[AutoTradingSession]:
        """
        Record a trade result in the session.

        Args:
            session_id: Session ID
            pnl: Profit/loss of the trade

        Returns:
            Updated session if found
        """
        session_obj = await self.get_by_id(session_id)
        if session_obj:
            session_obj.record_trade(pnl)
            return await self.update(session_obj)
        return None

    async def record_error(
        self, session_id: str, error_message: str
    ) -> Optional[AutoTradingSession]:
        """
        Record an error in the session.

        Args:
            session_id: Session ID
            error_message: Error description

        Returns:
            Updated session if found
        """
        session_obj = await self.get_by_id(session_id)
        if session_obj:
            session_obj.record_error(error_message)
            return await self.update(session_obj)
        return None

    async def update_activity(self, session_id: str) -> Optional[AutoTradingSession]:
        """
        Update last activity timestamp.

        Args:
            session_id: Session ID

        Returns:
            Updated session if found
        """
        session_obj = await self.get_by_id(session_id)
        if session_obj:
            session_obj.last_activity_at = datetime.utcnow()
            return await self.update(session_obj)
        return None

    async def pause(self, session_id: str) -> Optional[AutoTradingSession]:
        """
        Pause a session.

        Args:
            session_id: Session ID

        Returns:
            Updated session if found
        """
        session_obj = await self.get_by_id(session_id)
        if session_obj:
            session_obj.status = SessionStatus.PAUSED
            return await self.update(session_obj)
        return None

    async def resume(self, session_id: str) -> Optional[AutoTradingSession]:
        """
        Resume a paused session.

        Args:
            session_id: Session ID

        Returns:
            Updated session if found
        """
        session_obj = await self.get_by_id(session_id)
        if session_obj:
            session_obj.status = SessionStatus.ACTIVE
            return await self.update(session_obj)
        return None

    async def stop(self, session_id: str) -> Optional[AutoTradingSession]:
        """
        Stop a session.

        Args:
            session_id: Session ID

        Returns:
            Updated session if found
        """
        session_obj = await self.get_by_id(session_id)
        if session_obj:
            session_obj.status = SessionStatus.STOPPED
            session_obj.stopped_at = datetime.utcnow()
            return await self.update(session_obj)
        return None

    async def reset_daily_loss(self, session_id: str) -> Optional[AutoTradingSession]:
        """
        Reset daily loss counter (call at start of new trading day).

        Args:
            session_id: Session ID

        Returns:
            Updated session if found
        """
        session_obj = await self.get_by_id(session_id)
        if session_obj:
            session_obj.reset_daily_loss()
            return await self.update(session_obj)
        return None
