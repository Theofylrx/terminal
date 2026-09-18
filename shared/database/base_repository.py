"""
Base Repository Pattern Implementation
Provides common CRUD operations for all entities
"""

from typing import TypeVar, Generic, Optional, List, Dict, Any, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import DeclarativeMeta

T = TypeVar('T', bound=DeclarativeMeta)


class BaseRepository(Generic[T]):
    """
    Base Repository implementing common CRUD operations.
    All repositories inherit from this to avoid code duplication.

    Usage:
        class UserRepository(BaseRepository[User]):
            def __init__(self, session: AsyncSession):
                super().__init__(User, session)
    """

    def __init__(self, model: Type[T], session: AsyncSession):
        """
        Initialize repository with model and database session.

        Args:
            model: SQLAlchemy model class
            session: Async database session
        """
        self.model = model
        self.session = session

    async def create(self, **kwargs) -> T:
        """
        Create a new entity.

        Args:
            **kwargs: Model fields and values

        Returns:
            Created entity

        Example:
            user = await user_repo.create(
                email="user@example.com",
                username="trader1"
            )
        """
        entity = self.model(**kwargs)
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def get_by_id(self, entity_id: Any) -> Optional[T]:
        """
        Get entity by primary key ID.

        Args:
            entity_id: Primary key value

        Returns:
            Entity if found, None otherwise

        Example:
            user = await user_repo.get_by_id("user-123")
        """
        query = select(self.model).where(self.model.id == entity_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None
    ) -> List[T]:
        """
        Get all entities with optional filters and pagination.

        Args:
            filters: Dictionary of field:value filters
            limit: Maximum number of results
            offset: Number of results to skip
            order_by: Field name to order by (prepend '-' for desc)

        Returns:
            List of entities

        Example:
            positions = await position_repo.get_all(
                filters={'user_id': 'user-123', 'status': 'OPEN'},
                limit=10,
                order_by='-created_at'
            )
        """
        query = select(self.model)

        # Apply filters
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)

        # Apply ordering
        if order_by:
            if order_by.startswith('-'):
                field = order_by[1:]
                if hasattr(self.model, field):
                    query = query.order_by(getattr(self.model, field).desc())
            else:
                if hasattr(self.model, order_by):
                    query = query.order_by(getattr(self.model, order_by))

        # Apply pagination
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_one(self, **filters) -> Optional[T]:
        """
        Get single entity by filters.

        Args:
            **filters: Field-value pairs to filter by

        Returns:
            Entity if found, None otherwise

        Example:
            user = await user_repo.get_one(email="user@example.com")
        """
        query = select(self.model)

        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update(self, entity_id: Any, **kwargs) -> Optional[T]:
        """
        Update entity by ID.

        Args:
            entity_id: Primary key value
            **kwargs: Fields to update

        Returns:
            Updated entity if found, None otherwise

        Example:
            position = await position_repo.update(
                "pos-123",
                current_price=50100.0,
                unrealized_pnl=500.0
            )
        """
        query = (
            update(self.model)
            .where(self.model.id == entity_id)
            .values(**kwargs)
            .returning(self.model)
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.scalar_one_or_none()

    async def delete(self, entity_id: Any) -> bool:
        """
        Delete entity by ID.

        Args:
            entity_id: Primary key value

        Returns:
            True if deleted, False if not found

        Example:
            deleted = await order_repo.delete("order-123")
        """
        query = delete(self.model).where(self.model.id == entity_id)
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0

    async def count(self, **filters) -> int:
        """
        Count entities matching filters.

        Args:
            **filters: Field-value pairs to filter by

        Returns:
            Count of matching entities

        Example:
            open_positions = await position_repo.count(
                user_id="user-123",
                status="OPEN"
            )
        """
        query = select(func.count()).select_from(self.model)

        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)

        result = await self.session.execute(query)
        return result.scalar_one()

    async def exists(self, **filters) -> bool:
        """
        Check if entity exists matching filters.

        Args:
            **filters: Field-value pairs to filter by

        Returns:
            True if exists, False otherwise

        Example:
            has_position = await position_repo.exists(
                user_id="user-123",
                symbol="BTCUSDT"
            )
        """
        count = await self.count(**filters)
        return count > 0
