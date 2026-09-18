"""
WebSocket Routes
Real-time updates for positions, orders, market data
"""

from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status
from gateway.middleware.auth import verify_token
import json
import asyncio

router = APIRouter()

# Connection manager for WebSocket clients
class ConnectionManager:
    """Manages WebSocket connections and broadcasts."""

    def __init__(self):
        # user_id -> Set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept WebSocket connection and track it."""
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()

        self.active_connections[user_id].add(websocket)
        print(f"Client connected: {user_id} (total: {len(self.active_connections[user_id])})")

    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove disconnected WebSocket."""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        print(f"Client disconnected: {user_id}")

    async def send_personal_message(self, message: dict, user_id: str):
        """Send message to specific user's all connections."""
        if user_id in self.active_connections:
            message_json = json.dumps(message)
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(message_json)
                except Exception as e:
                    print(f"Error sending to {user_id}: {e}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected users."""
        message_json = json.dumps(message)
        for user_connections in self.active_connections.values():
            for connection in user_connections:
                try:
                    await connection.send_text(message_json)
                except Exception as e:
                    print(f"Broadcast error: {e}")


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = None):
    """
    WebSocket endpoint for real-time updates.

    Client should connect with JWT token as query parameter:
    ws://localhost:8080/ws?token=<jwt_token>

    Messages format:
    {
        "type": "position_update" | "order_update" | "price_update",
        "data": {...}
    }
    """
    # Authenticate user
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        # Verify JWT token
        payload = verify_token(token)
        user_id = payload.get("sub")

        if not user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    except Exception as e:
        print(f"WebSocket auth failed: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Connect user
    await manager.connect(websocket, user_id)

    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "user_id": user_id
        })

        # Keep connection alive and handle incoming messages
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)

                # Handle ping/pong for keep-alive
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    continue

                # Handle subscription requests
                if message.get("type") == "subscribe":
                    channels = message.get("channels", [])
                    await websocket.send_json({
                        "type": "subscribed",
                        "channels": channels
                    })
                    # In a real implementation, you'd track subscriptions
                    # and only send relevant updates

                # Echo other messages (for testing)
                await websocket.send_json({
                    "type": "echo",
                    "data": message
                })

            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON"
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        print(f"User {user_id} disconnected")

    except Exception as e:
        print(f"WebSocket error for {user_id}: {e}")
        manager.disconnect(websocket, user_id)


# Helper function for services to send updates
async def send_position_update(user_id: str, position_data: dict):
    """
    Send position update to user's WebSocket connections.

    Args:
        user_id: User to notify
        position_data: Position data

    Example:
        await send_position_update(
            "user-123",
            {"symbol": "BTCUSDT", "unrealized_pnl": 500.0}
        )
    """
    await manager.send_personal_message(
        {
            "type": "position_update",
            "data": position_data,
            "timestamp": asyncio.get_event_loop().time()
        },
        user_id
    )


async def send_order_update(user_id: str, order_data: dict):
    """Send order update to user."""
    await manager.send_personal_message(
        {
            "type": "order_update",
            "data": order_data,
            "timestamp": asyncio.get_event_loop().time()
        },
        user_id
    )


async def send_price_update(symbol: str, price_data: dict):
    """Broadcast price update to all users."""
    await manager.broadcast(
        {
            "type": "price_update",
            "symbol": symbol,
            "data": price_data,
            "timestamp": asyncio.get_event_loop().time()
        }
    )
