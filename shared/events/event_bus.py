"""
Event Bus Implementation using Redis Streams
Enables event-driven communication between microservices
"""

import os
import json
import asyncio
from typing import Dict, Any, Callable, Awaitable, Optional
from datetime import datetime
import redis.asyncio as redis
from redis.asyncio import Redis
from redis.exceptions import RedisError

# Global Redis client
_redis_client: Optional[Redis] = None


def get_redis_url() -> str:
    """
    Get Redis URL from environment variables.

    Returns:
        Redis connection string

    Raises:
        ValueError: If REDIS_URL not set
    """
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    return redis_url


async def get_redis_client() -> Redis:
    """
    Get or create Redis client.

    Returns:
        Redis client

    Example:
        client = await get_redis_client()
    """
    global _redis_client

    if _redis_client is None:
        url = get_redis_url()
        _redis_client = await redis.from_url(
            url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50
        )

    return _redis_client


async def close_redis():
    """
    Close Redis connection.
    Call this on application shutdown.

    Example:
        @app.on_event("shutdown")
        async def shutdown():
            await close_redis()
    """
    global _redis_client

    if _redis_client:
        await _redis_client.close()
        _redis_client = None


class EventPublisher:
    """
    Event Publisher for publishing events to Redis Streams.

    Usage:
        publisher = EventPublisher()
        await publisher.publish(
            "market.data.btcusdt.1m",
            {"price": 50000, "volume": 123.45}
        )
    """

    def __init__(self):
        """Initialize event publisher."""
        self.redis_client: Optional[Redis] = None

    async def connect(self):
        """Connect to Redis."""
        if self.redis_client is None:
            self.redis_client = await get_redis_client()

    async def publish(
        self,
        event_type: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Publish an event to Redis Stream.

        Args:
            event_type: Event type (e.g., "market.data.btcusdt.1m")
            data: Event payload
            metadata: Optional metadata (timestamp added automatically)

        Returns:
            Event ID from Redis

        Example:
            await publisher.publish(
                "execution.order.created",
                {
                    "order_id": "abc123",
                    "symbol": "BTCUSDT",
                    "side": "BUY",
                    "quantity": 0.5
                }
            )
        """
        await self.connect()

        # Prepare event payload
        event = {
            "type": event_type,
            "data": json.dumps(data),
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": json.dumps(metadata or {})
        }

        # Publish to Redis Stream
        # Stream name is the event type (e.g., "market.data.btcusdt.1m")
        try:
            event_id = await self.redis_client.xadd(
                event_type,
                event,
                maxlen=10000  # Keep last 10k events per stream
            )
            return event_id
        except RedisError as e:
            print(f"Failed to publish event {event_type}: {e}")
            raise


class EventSubscriber:
    """
    Event Subscriber for consuming events from Redis Streams.

    Usage:
        async def handle_market_data(event):
            print(f"Received: {event}")

        subscriber = EventSubscriber()
        await subscriber.subscribe(
            "market.data.btcusdt.1m",
            handle_market_data
        )
        await subscriber.start()
    """

    def __init__(self, consumer_group: str, consumer_name: str):
        """
        Initialize event subscriber.

        Args:
            consumer_group: Name of consumer group (e.g., "technical-analyst")
            consumer_name: Name of this consumer instance (e.g., "technical-analyst-1")
        """
        self.redis_client: Optional[Redis] = None
        self.consumer_group = consumer_group
        self.consumer_name = consumer_name
        self.subscriptions: Dict[str, Callable[[Dict], Awaitable[None]]] = {}
        self.running = False

    async def connect(self):
        """Connect to Redis."""
        if self.redis_client is None:
            self.redis_client = await get_redis_client()

    async def subscribe(
        self,
        event_type: str,
        handler: Callable[[Dict[str, Any]], Awaitable[None]]
    ):
        """
        Subscribe to an event type.

        Args:
            event_type: Event type pattern (e.g., "market.data.*" or specific "market.data.btcusdt.1m")
            handler: Async function to handle events

        Example:
            async def handle_signal(event):
                print(f"Signal received: {event}")

            await subscriber.subscribe("analysis.technical.*", handle_signal)
        """
        await self.connect()

        # Create consumer group if it doesn't exist
        try:
            await self.redis_client.xgroup_create(
                event_type,
                self.consumer_group,
                id='0',
                mkstream=True
            )
        except redis.ResponseError as e:
            # Group already exists
            if "BUSYGROUP" not in str(e):
                raise

        self.subscriptions[event_type] = handler

    async def start(self):
        """
        Start consuming events.
        Blocks until stopped.

        Example:
            await subscriber.start()
        """
        await self.connect()
        self.running = True

        print(f"[{self.consumer_name}] Started consuming events...")

        while self.running:
            try:
                # Read from multiple streams
                streams = {event_type: '>' for event_type in self.subscriptions.keys()}

                if not streams:
                    await asyncio.sleep(1)
                    continue

                # Read new messages
                messages = await self.redis_client.xreadgroup(
                    self.consumer_group,
                    self.consumer_name,
                    streams,
                    count=10,
                    block=1000  # Block for 1 second
                )

                # Process messages
                for stream, events in messages:
                    handler = self.subscriptions.get(stream)

                    if handler:
                        for event_id, event_data in events:
                            try:
                                # Parse event
                                parsed_event = {
                                    "id": event_id,
                                    "type": event_data.get("type"),
                                    "data": json.loads(event_data.get("data", "{}")),
                                    "timestamp": event_data.get("timestamp"),
                                    "metadata": json.loads(event_data.get("metadata", "{}"))
                                }

                                # Call handler
                                await handler(parsed_event)

                                # Acknowledge message
                                await self.redis_client.xack(
                                    stream,
                                    self.consumer_group,
                                    event_id
                                )

                            except Exception as e:
                                print(f"Error processing event {event_id}: {e}")
                                # Don't acknowledge - will be retried

            except RedisError as e:
                print(f"Redis error: {e}")
                await asyncio.sleep(1)

            except Exception as e:
                print(f"Unexpected error: {e}")
                await asyncio.sleep(1)

    async def stop(self):
        """
        Stop consuming events.

        Example:
            await subscriber.stop()
        """
        self.running = False
        print(f"[{self.consumer_name}] Stopped consuming events")


async def get_event_publisher() -> EventPublisher:
    """
    Dependency for FastAPI to inject event publisher.

    Returns:
        Event publisher

    Example:
        @app.post("/orders")
        async def create_order(
            publisher: EventPublisher = Depends(get_event_publisher)
        ):
            await publisher.publish("execution.order.created", {...})
    """
    publisher = EventPublisher()
    await publisher.connect()
    return publisher
