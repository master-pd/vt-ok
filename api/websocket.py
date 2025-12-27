"""
WebSocket API for VT ULTRA PRO
Real-time updates and notifications
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect, Depends
from fastapi.routing import APIRouter
from pydantic import BaseModel
import jwt

# Setup logging
logger = logging.getLogger(__name__)

# WebSocket router
router = APIRouter()

# Connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[str, List[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = []
            self.user_connections[user_id].append(websocket)
        
        logger.info(f"WebSocket connected: {user_id or 'anonymous'}")
        
    def disconnect(self, websocket: WebSocket, user_id: str = None):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        if user_id and user_id in self.user_connections:
            if websocket in self.user_connections[user_id]:
                self.user_connections[user_id].remove(websocket)
            
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        logger.info(f"WebSocket disconnected: {user_id or 'anonymous'}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass
    
    async def send_to_user(self, user_id: str, message: str):
        if user_id in self.user_connections:
            for connection in self.user_connections[user_id]:
                try:
                    await connection.send_text(message)
                except:
                    pass

# Initialize connection manager
manager = ConnectionManager()

# Models
class WebSocketMessage(BaseModel):
    type: str
    data: Dict[str, Any]
    timestamp: str = None
    
    class Config:
        schema_extra = {
            "example": {
                "type": "order_update",
                "data": {
                    "order_id": "ORD123456",
                    "status": "processing",
                    "progress": 50
                },
                "timestamp": "2024-01-01T10:30:00Z"
            }
        }

# Authentication helper
async def authenticate_websocket(websocket: WebSocket) -> Optional[str]:
    try:
        token = websocket.query_params.get("token")
        if not token:
            return None
        
        # Verify JWT token
        SECRET_KEY = "your-secret-key-change-in-production"
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        
        return user_id
    except:
        return None

# WebSocket endpoint
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint"""
    user_id = await authenticate_websocket(websocket)
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                await handle_websocket_message(message, websocket, user_id)
            except json.JSONDecodeError:
                await send_error(websocket, "Invalid JSON format")
            except Exception as e:
                logger.error(f"WebSocket message handling error: {e}")
                await send_error(websocket, "Internal server error")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, user_id)

async def handle_websocket_message(message: Dict, websocket: WebSocket, user_id: str):
    """Handle incoming WebSocket messages"""
    message_type = message.get("type")
    
    if message_type == "ping":
        await send_pong(websocket)
    
    elif message_type == "subscribe":
        await handle_subscribe(message, websocket, user_id)
    
    elif message_type == "unsubscribe":
        await handle_unsubscribe(message, websocket, user_id)
    
    elif message_type == "order_status":
        await handle_order_status(message, websocket, user_id)
    
    elif message_type == "system_status":
        await handle_system_status(websocket, user_id)
    
    else:
        await send_error(websocket, f"Unknown message type: {message_type}")

async def handle_subscribe(message: Dict, websocket: WebSocket, user_id: str):
    """Handle subscription requests"""
    channel = message.get("channel")
    
    if not channel:
        await send_error(websocket, "Channel not specified")
        return
    
    # Store subscription (in production, use Redis or database)
    # For now, just acknowledge
    await send_message(websocket, {
        "type": "subscription_confirmed",
        "data": {
            "channel": channel,
            "status": "subscribed"
        },
        "timestamp": datetime.now().isoformat()
    })
    
    # Send initial data for the channel
    if channel == "system_stats":
        await send_system_stats(websocket)
    elif channel.startswith("order_"):
        order_id = channel.replace("order_", "")
        await send_order_update(websocket, order_id, user_id)

async def handle_unsubscribe(message: Dict, websocket: WebSocket, user_id: str):
    """Handle unsubscribe requests"""
    channel = message.get("channel")
    
    await send_message(websocket, {
        "type": "unsubscription_confirmed",
        "data": {
            "channel": channel,
            "status": "unsubscribed"
        },
        "timestamp": datetime.now().isoformat()
    })

async def handle_order_status(message: Dict, websocket: WebSocket, user_id: str):
    """Handle order status requests"""
    order_id = message.get("order_id")
    
    if not order_id:
        await send_error(websocket, "Order ID not specified")
        return
    
    if not user_id:
        await send_error(websocket, "Authentication required")
        return
    
    # Check if user has access to this order
    from telegram_bot.database.order_db import OrderDatabase
    order_db = OrderDatabase()
    order = order_db.get_order(order_id)
    
    if not order:
        await send_error(websocket, "Order not found")
        return
    
    if str(order.get("user_id")) != user_id:
        await send_error(websocket, "Access denied")
        return
    
    # Send current order status
    await send_order_update(websocket, order_id, user_id)

async def handle_system_status(websocket: WebSocket, user_id: str):
    """Handle system status requests"""
    if not user_id:
        await send_error(websocket, "Authentication required")
        return
    
    # Check if user is admin
    from telegram_bot.database.user_db import UserDatabase
    user_db = UserDatabase()
    user = user_db.get_user(int(user_id))
    
    if not user or not user.get("is_admin"):
        await send_error(websocket, "Admin access required")
        return
    
    await send_system_stats(websocket)

async def send_order_update(websocket: WebSocket, order_id: str, user_id: str):
    """Send order update to WebSocket client"""
    try:
        from telegram_bot.database.order_db import OrderDatabase
        order_db = OrderDatabase()
        
        order = order_db.get_order(order_id)
        if not order:
            return
        
        progress = order_db.get_order_progress_history(order_id)
        
        message = WebSocketMessage(
            type="order_update",
            data={
                "order_id": order_id,
                "status": order.get("status"),
                "target_views": order.get("target_views"),
                "delivered_views": order.get("delivered_views", 0),
                "progress_percentage": int((order.get("delivered_views", 0) / order["target_views"]) * 100),
                "created_at": order.get("created_at"),
                "started_at": order.get("started_at"),
                "completed_at": order.get("completed_at"),
                "recent_progress": progress[-5:] if progress else []
            },
            timestamp=datetime.now().isoformat()
        )
        
        await websocket.send_text(message.json())
        
    except Exception as e:
        logger.error(f"Error sending order update: {e}")

async def send_system_stats(websocket: WebSocket):
    """Send system statistics to WebSocket client"""
    try:
        from monitoring.realtime_monitor import RealTimeMonitor
        from monitoring.health_check import HealthCheck
        
        monitor = RealTimeMonitor()
        health_check = HealthCheck()
        
        metrics = await monitor.get_current_metrics()
        health_status = await health_check.get_current_status()
        
        message = WebSocketMessage(
            type="system_stats",
            data={
                "health": health_status,
                "metrics": metrics,
                "timestamp": datetime.now().isoformat()
            },
            timestamp=datetime.now().isoformat()
        )
        
        await websocket.send_text(message.json())
        
    except Exception as e:
        logger.error(f"Error sending system stats: {e}")

async def send_pong(websocket: WebSocket):
    """Send pong response to ping"""
    await send_message(websocket, {
        "type": "pong",
        "data": {},
        "timestamp": datetime.now().isoformat()
    })

async def send_message(websocket: WebSocket, message: Dict):
    """Send message to WebSocket client"""
    try:
        await websocket.send_text(json.dumps(message))
    except Exception as e:
        logger.error(f"Error sending WebSocket message: {e}")

async def send_error(websocket: WebSocket, error_message: str):
    """Send error message to WebSocket client"""
    await send_message(websocket, {
        "type": "error",
        "data": {
            "message": error_message
        },
        "timestamp": datetime.now().isoformat()
    })

# Background task for broadcasting updates
async def broadcast_updates():
    """Background task to broadcast updates to all connected clients"""
    while True:
        try:
            # Broadcast system stats to admin users every 30 seconds
            from monitoring.realtime_monitor import RealTimeMonitor
            monitor = RealTimeMonitor()
            
            metrics = await monitor.get_current_metrics()
            
            message = WebSocketMessage(
                type="system_update",
                data={
                    "metrics": metrics,
                    "timestamp": datetime.now().isoformat()
                },
                timestamp=datetime.now().isoformat()
            )
            
            await manager.broadcast(message.json())
            
            # Sleep for 30 seconds
            await asyncio.sleep(30)
            
        except Exception as e:
            logger.error(f"Broadcast updates error: {e}")
            await asyncio.sleep(10)

# Order update handler
async def notify_order_update(order_id: str, user_id: str, update_data: Dict):
    """Notify specific user about order update"""
    message = WebSocketMessage(
        type="order_update",
        data={
            "order_id": order_id,
            **update_data
        },
        timestamp=datetime.now().isoformat()
    )
    
    await manager.send_to_user(str(user_id), message.json())

# System alert handler
async def notify_system_alert(alert_data: Dict):
    """Notify all admin users about system alert"""
    message = WebSocketMessage(
        type="system_alert",
        data=alert_data,
        timestamp=datetime.now().isoformat()
    )
    
    # Send to all admin users
    from telegram_bot.database.user_db import UserDatabase
    user_db = UserDatabase()
    
    # Get admin users (simplified - in production, cache this)
    # For now, broadcast to all connected clients
    await manager.broadcast(message.json())

# Startup function
async def start_websocket_server():
    """Start WebSocket server and background tasks"""
    logger.info("Starting WebSocket server...")
    
    # Start broadcast updates task
    asyncio.create_task(broadcast_updates())
    
    logger.info("WebSocket server started")

# Export router
websocket_router = router