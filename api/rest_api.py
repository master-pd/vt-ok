"""
REST API for VT ULTRA PRO System
"""
from fastapi import FastAPI, HTTPException, Depends, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta
import json
import os
from pathlib import Path

# Import system modules
from core.security import SecuritySystem
from utils.logger import get_logger
from tiktok_engine.workers.worker_manager import WorkerManager
from payment_system.crypto_payments import CryptoPaymentProcessor
from admin_panel.admin_dashboard import AdminDashboard

# Initialize components
app = FastAPI(
    title="VT ULTRA PRO API",
    description="Complete TikTok View Boosting System API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Security
security_system = SecuritySystem(secret_key=os.getenv("SECRET_KEY", "vt-ultra-pro-secret-key-2024"))
security = HTTPBearer()

# Logger
logger = get_logger()

# Worker Manager
worker_manager = WorkerManager()

# Payment Processor
payment_processor = CryptoPaymentProcessor()

# Admin Dashboard
admin_dashboard = AdminDashboard()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class UserCreate(BaseModel):
    """User creation model"""
    email: str
    username: str
    password: str
    full_name: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v
    
    @validator('email')
    def validate_email(cls, v):
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v

class UserLogin(BaseModel):
    """User login model"""
    email: str
    password: str

class OrderCreate(BaseModel):
    """Order creation model"""
    video_url: str
    target_views: int = Field(..., gt=0, le=100000)
    view_method: str = Field("auto", regex="^(browser|api|cloud|hybrid|auto)$")
    priority: str = Field("normal", regex="^(low|normal|high|urgent)$")
    schedule_time: Optional[datetime] = None
    
    @validator('video_url')
    def validate_video_url(cls, v):
        if not v.startswith(('https://tiktok.com/', 'https://www.tiktok.com/')):
            raise ValueError('Invalid TikTok URL')
        return v

class PaymentRequest(BaseModel):
    """Payment request model"""
    order_id: str
    amount: float = Field(..., gt=0)
    currency: str = Field("USD", regex="^(USD|EUR|GBP|BTC|ETH)$")
    payment_method: str = Field(..., regex="^(credit_card|crypto|paypal|bank_transfer)$")

class AnalyticsRequest(BaseModel):
    """Analytics request model"""
    start_date: datetime
    end_date: datetime
    metrics: List[str] = Field(default=["views", "success_rate", "revenue"])
    group_by: str = Field("day", regex="^(hour|day|week|month)$")

# Database (in production, use real database)
users_db = {}
orders_db = {}
payments_db = {}

# Dependency functions
async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Get current user from JWT token"""
    token = credentials.credentials
    payload = security_system.verify_jwt_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user_id = payload.get('user_id')
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return users_db[user_id]

async def require_admin(user: Dict = Depends(get_current_user)):
    """Require admin privileges"""
    if not user.get('is_admin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user

# Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "VT ULTRA PRO API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "auth": "/api/auth/*",
            "orders": "/api/orders/*",
            "payments": "/api/payments/*",
            "analytics": "/api/analytics/*",
            "admin": "/api/admin/*"
        }
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": "connected",
            "workers": worker_manager.get_status(),
            "security": "operational",
            "logging": "active"
        }
    }

# Authentication endpoints
@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register new user"""
    # Check if user exists
    for user in users_db.values():
        if user['email'] == user_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Create user
    user_id = f"user_{len(users_db) + 1}"
    
    user = {
        'user_id': user_id,
        'email': user_data.email,
        'username': user_data.username,
        'full_name': user_data.full_name,
        'password_hash': security_system.hash_password(user_data.password),
        'created_at': datetime.utcnow().isoformat(),
        'last_login': None,
        'is_active': True,
        'is_admin': False,
        'balance': 0.0,
        'total_orders': 0,
        'total_views': 0
    }
    
    users_db[user_id] = user
    
    # Log registration
    logger.audit(
        action="user_registration",
        user=user_id,
        resource="users",
        status="success",
        details={"email": user_data.email}
    )
    
    return {
        "message": "User registered successfully",
        "user_id": user_id
    }

@app.post("/api/auth/login")
async def login(login_data: UserLogin):
    """User login"""
    # Find user
    user = None
    for u in users_db.values():
        if u['email'] == login_data.email:
            user = u
            break
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verify password
    if not security_system.verify_password(login_data.password, user['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Update last login
    user['last_login'] = datetime.utcnow().isoformat()
    
    # Generate tokens
    access_token = security_system.create_jwt_token(user['user_id'], {
        'email': user['email'],
        'username': user['username'],
        'is_admin': user.get('is_admin', False)
    })
    
    refresh_token = security_system.create_refresh_token(user['user_id'])
    
    # Log login
    logger.audit(
        action="user_login",
        user=user['user_id'],
        resource="auth",
        status="success"
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 86400,  # 24 hours
        "user": {
            "user_id": user['user_id'],
            "email": user['email'],
            "username": user['username'],
            "is_admin": user.get('is_admin', False)
        }
    }

@app.post("/api/auth/refresh")
async def refresh_token(refresh_token: str):
    """Refresh access token"""
    new_token = security_system.refresh_access_token(refresh_token)
    
    if not new_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    return {
        "access_token": new_token,
        "token_type": "bearer",
        "expires_in": 86400
    }

@app.get("/api/auth/profile")
async def get_profile(user: Dict = Depends(get_current_user)):
    """Get user profile"""
    return {
        "user_id": user['user_id'],
        "email": user['email'],
        "username": user['username'],
        "full_name": user.get('full_name'),
        "created_at": user['created_at'],
        "last_login": user.get('last_login'),
        "balance": user.get('balance', 0),
        "total_orders": user.get('total_orders', 0),
        "total_views": user.get('total_views', 0),
        "success_rate": user.get('success_rate', 0)
    }

# Order endpoints
@app.post("/api/orders/create")
async def create_order(
    order_data: OrderCreate,
    user: Dict = Depends(get_current_user)
):
    """Create new order"""
    # Validate user balance (if paid service)
    if order_data.target_views > 1000:  # Example: free tier limit
        if user.get('balance', 0) < 10:  # Minimum balance check
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Insufficient balance"
            )
    
    # Generate order ID
    order_id = f"ORD{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{user['user_id'][-6:]}"
    
    # Calculate price (example pricing)
    price_per_1000 = {
        'browser': 2.99,
        'api': 1.99,
        'cloud': 0.99,
        'hybrid': 3.99,
        'auto': 2.49
    }
    
    method = order_data.view_method
    price = (order_data.target_views / 1000) * price_per_1000.get(method, 2.49)
    
    # Create order
    order = {
        'order_id': order_id,
        'user_id': user['user_id'],
        'video_url': order_data.video_url,
        'target_views': order_data.target_views,
        'delivered_views': 0,
        'view_method': method,
        'priority': order_data.priority,
        'price': price,
        'status': 'pending',
        'created_at': datetime.utcnow().isoformat(),
        'started_at': None,
        'completed_at': None,
        'success_rate': 0,
        'schedule_time': order_data.schedule_time.isoformat() if order_data.schedule_time else None
    }
    
    orders_db[order_id] = order
    
    # Update user stats
    user['total_orders'] = user.get('total_orders', 0) + 1
    
    # Add to worker queue
    if not order_data.schedule_time or order_data.schedule_time <= datetime.utcnow():
        worker_manager.add_order(order)
    
    # Log order creation
    logger.audit(
        action="order_created",
        user=user['user_id'],
        resource="orders",
        status="success",
        details={
            'order_id': order_id,
            'target_views': order_data.target_views,
            'price': price
        }
    )
    
    return {
        "message": "Order created successfully",
        "order_id": order_id,
        "order": order
    }

@app.get("/api/orders")
async def get_orders(
    user: Dict = Depends(get_current_user),
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Get user orders"""
    # Filter user orders
    user_orders = [
        order for order in orders_db.values()
        if order['user_id'] == user['user_id']
    ]
    
    # Apply status filter
    if status:
        user_orders = [order for order in user_orders if order['status'] == status]
    
    # Sort by creation date (newest first)
    user_orders.sort(key=lambda x: x['created_at'], reverse=True)
    
    # Paginate
    paginated_orders = user_orders[offset:offset + limit]
    
    return {
        "orders": paginated_orders,
        "total": len(user_orders),
        "limit": limit,
        "offset": offset
    }

@app.get("/api/orders/{order_id}")
async def get_order(
    order_id: str,
    user: Dict = Depends(get_current_user)
):
    """Get specific order"""
    if order_id not in orders_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    order = orders_db[order_id]
    
    # Check ownership
    if order['user_id'] != user['user_id'] and not user.get('is_admin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get order progress
    progress = worker_manager.get_order_progress(order_id)
    
    return {
        "order": order,
        "progress": progress,
        "estimated_completion": worker_manager.get_estimated_completion(order_id)
    }

@app.put("/api/orders/{order_id}/cancel")
async def cancel_order(
    order_id: str,
    user: Dict = Depends(get_current_user)
):
    """Cancel order"""
    if order_id not in orders_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    order = orders_db[order_id]
    
    # Check ownership
    if order['user_id'] != user['user_id']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check if can be cancelled
    if order['status'] not in ['pending', 'processing']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order in {order['status']} status"
        )
    
    # Update order
    order['status'] = 'cancelled'
    order['cancelled_at'] = datetime.utcnow().isoformat()
    
    # Remove from worker queue
    worker_manager.cancel_order(order_id)
    
    # Log cancellation
    logger.audit(
        action="order_cancelled",
        user=user['user_id'],
        resource="orders",
        status="success",
        details={'order_id': order_id}
    )
    
    return {
        "message": "Order cancelled successfully",
        "order": order
    }

# Payment endpoints
@app.post("/api/payments/deposit")
async def deposit_funds(
    payment_data: PaymentRequest,
    user: Dict = Depends(get_current_user)
):
    """Deposit funds"""
    # Generate payment ID
    payment_id = f"PAY{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{user['user_id'][-6:]}"
    
    # Process payment based on method
    if payment_data.payment_method == 'crypto':
        # Generate crypto address
        crypto_address = payment_processor.generate_address(
            user['user_id'],
            payment_data.amount,
            payment_data.currency
        )
        
        payment = {
            'payment_id': payment_id,
            'user_id': user['user_id'],
            'order_id': payment_data.order_id,
            'amount': payment_data.amount,
            'currency': payment_data.currency,
            'method': payment_data.payment_method,
            'status': 'pending',
            'crypto_address': crypto_address,
            'created_at': datetime.utcnow().isoformat()
        }
    
    elif payment_data.payment_method == 'credit_card':
        # Process credit card (simulated)
        payment = {
            'payment_id': payment_id,
            'user_id': user['user_id'],
            'order_id': payment_data.order_id,
            'amount': payment_data.amount,
            'currency': payment_data.currency,
            'method': payment_data.payment_method,
            'status': 'completed',
            'transaction_id': f"TXN{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            'created_at': datetime.utcnow().isoformat(),
            'completed_at': datetime.utcnow().isoformat()
        }
        
        # Update user balance
        user['balance'] = user.get('balance', 0) + payment_data.amount
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment method {payment_data.payment_method} not supported"
        )
    
    payments_db[payment_id] = payment
    
    # Log payment
    logger.audit(
        action="payment_created",
        user=user['user_id'],
        resource="payments",
        status="success",
        details={
            'payment_id': payment_id,
            'amount': payment_data.amount,
            'currency': payment_data.currency
        }
    )
    
    return {
        "message": "Payment processed",
        "payment_id": payment_id,
        "payment": payment
    }

@app.get("/api/payments/status/{payment_id}")
async def get_payment_status(
    payment_id: str,
    user: Dict = Depends(get_current_user)
):
    """Get payment status"""
    if payment_id not in payments_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    payment = payments_db[payment_id]
    
    # Check ownership
    if payment['user_id'] != user['user_id'] and not user.get('is_admin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check crypto payment status
    if payment['method'] == 'crypto' and payment['status'] == 'pending':
        status_info = payment_processor.check_payment(payment['crypto_address'])
        payment['status'] = status_info.get('status', 'pending')
        
        if payment['status'] == 'completed':
            payment['completed_at'] = datetime.utcnow().isoformat()
            # Update user balance
            user['balance'] = user.get('balance', 0) + payment['amount']
    
    return {
        "payment": payment,
        "status_info": payment_processor.get_payment_info(payment_id) if payment['method'] == 'crypto' else None
    }

# Analytics endpoints
@app.post("/api/analytics/user")
async def get_user_analytics(
    analytics_request: AnalyticsRequest,
    user: Dict = Depends(get_current_user)
):
    """Get user analytics"""
    # Filter user orders in date range
    user_orders = [
        order for order in orders_db.values()
        if order['user_id'] == user['user_id'] and
        analytics_request.start_date <= datetime.fromisoformat(order['created_at']) <= analytics_request.end_date
    ]
    
    # Calculate metrics
    analytics = {
        'period': {
            'start': analytics_request.start_date.isoformat(),
            'end': analytics_request.end_date.isoformat()
        },
        'summary': {
            'total_orders': len(user_orders),
            'total_views': sum(order.get('target_views', 0) for order in user_orders),
            'delivered_views': sum(order.get('delivered_views', 0) for order in user_orders),
            'total_spent': sum(order.get('price', 0) for order in user_orders),
            'success_rate': self._calculate_success_rate(user_orders)
        },
        'daily_metrics': self._calculate_daily_metrics(user_orders, analytics_request.group_by),
        'method_distribution': self._calculate_method_distribution(user_orders),
        'performance_trend': self._calculate_performance_trend(user_orders)
    }
    
    return analytics

def _calculate_success_rate(self, orders: List[Dict]) -> float:
    """Calculate success rate"""
    if not orders:
        return 0
    
    completed_orders = [o for o in orders if o.get('delivered_views', 0) > 0]
    if not completed_orders:
        return 0
    
    total_target = sum(o.get('target_views', 0) for o in completed_orders)
    total_delivered = sum(o.get('delivered_views', 0) for o in completed_orders)
    
    return (total_delivered / total_target * 100) if total_target > 0 else 0

def _calculate_daily_metrics(self, orders: List[Dict], group_by: str) -> List[Dict]:
    """Calculate daily metrics"""
    metrics_by_date = {}
    
    for order in orders:
        # Group by date
        order_date = datetime.fromisoformat(order['created_at'])
        
        if group_by == 'hour':
            date_key = order_date.strftime('%Y-%m-%d %H:00')
        elif group_by == 'day':
            date_key = order_date.strftime('%Y-%m-%d')
        elif group_by == 'week':
            date_key = order_date.strftime('%Y-W%W')
        elif group_by == 'month':
            date_key = order_date.strftime('%Y-%m')
        else:
            date_key = order_date.strftime('%Y-%m-%d')
        
        if date_key not in metrics_by_date:
            metrics_by_date[date_key] = {
                'date': date_key,
                'orders': 0,
                'views_ordered': 0,
                'views_delivered': 0,
                'revenue': 0
            }
        
        metrics_by_date[date_key]['orders'] += 1
        metrics_by_date[date_key]['views_ordered'] += order.get('target_views', 0)
        metrics_by_date[date_key]['views_delivered'] += order.get('delivered_views', 0)
        metrics_by_date[date_key]['revenue'] += order.get('price', 0)
    
    return sorted(metrics_by_date.values(), key=lambda x: x['date'])

def _calculate_method_distribution(self, orders: List[Dict]) -> Dict:
    """Calculate method distribution"""
    distribution = {}
    
    for order in orders:
        method = order.get('view_method', 'unknown')
        if method not in distribution:
            distribution[method] = {
                'count': 0,
                'views': 0,
                'success_rate': 0
            }
        
        distribution[method]['count'] += 1
        distribution[method]['views'] += order.get('target_views', 0)
    
    return distribution

def _calculate_performance_trend(self, orders: List[Dict]) -> List[Dict]:
    """Calculate performance trend"""
    # Group by date and calculate success rates
    performance_by_date = {}
    
    for order in orders:
        if order.get('delivered_views', 0) > 0:
            date = datetime.fromisoformat(order['created_at']).strftime('%Y-%m-%d')
            
            if date not in performance_by_date:
                performance_by_date[date] = {
                    'date': date,
                    'success_rates': [],
                    'delivery_times': []
                }
            
            success_rate = (order['delivered_views'] / order['target_views']) * 100
            performance_by_date[date]['success_rates'].append(success_rate)
    
    # Calculate averages
    trend_data = []
    for date, data in performance_by_date.items():
        if data['success_rates']:
            avg_success = sum(data['success_rates']) / len(data['success_rates'])
            trend_data.append({
                'date': date,
                'avg_success_rate': avg_success,
                'order_count': len(data['success_rates'])
            })
    
    return sorted(trend_data, key=lambda x: x['date'])

# Admin endpoints
@app.get("/api/admin/stats")
async def get_admin_stats(
    admin: Dict = Depends(require_admin),
    period: str = "day"
):
    """Get admin statistics"""
    stats = admin_dashboard.get_system_stats(period)
    
    # Add real-time data
    stats['realtime'] = {
        'active_workers': worker_manager.get_active_worker_count(),
        'queued_orders': worker_manager.get_queued_order_count(),
        'system_load': self._get_system_load()
    }
    
    return stats

@app.get("/api/admin/users")
async def get_all_users(
    admin: Dict = Depends(require_admin),
    limit: int = 100,
    offset: int = 0,
    search: Optional[str] = None
):
    """Get all users (admin only)"""
    filtered_users = list(users_db.values())
    
    # Apply search
    if search:
        filtered_users = [
            user for user in filtered_users
            if search.lower() in user.get('email', '').lower() or
               search.lower() in user.get('username', '').lower()
        ]
    
    # Paginate
    paginated_users = filtered_users[offset:offset + limit]
    
    # Remove sensitive data
    for user in paginated_users:
        user.pop('password_hash', None)
    
    return {
        "users": paginated_users,
        "total": len(filtered_users),
        "limit": limit,
        "offset": offset
    }

@app.get("/api/admin/orders")
async def get_all_orders(
    admin: Dict = Depends(require_admin),
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """Get all orders (admin only)"""
    all_orders = list(orders_db.values())
    
    # Apply status filter
    if status:
        all_orders = [order for order in all_orders if order['status'] == status]
    
    # Sort by creation date
    all_orders.sort(key=lambda x: x['created_at'], reverse=True)
    
    # Paginate
    paginated_orders = all_orders[offset:offset + limit]
    
    return {
        "orders": paginated_orders,
        "total": len(all_orders),
        "limit": limit,
        "offset": offset
    }

@app.put("/api/admin/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    status_update: Dict[str, str],
    admin: Dict = Depends(require_admin)
):
    """Update order status (admin only)"""
    if order_id not in orders_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    order = orders_db[order_id]
    new_status = status_update.get('status')
    
    if not new_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status is required"
        )
    
    # Validate status transition
    valid_transitions = {
        'pending': ['processing', 'cancelled'],
        'processing': ['completed', 'failed', 'cancelled'],
        'completed': ['refunded'],
        'failed': ['retrying', 'cancelled']
    }
    
    current_status = order['status']
    if new_status not in valid_transitions.get(current_status, []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition from {current_status} to {new_status}"
        )
    
    # Update order
    order['status'] = new_status
    
    if new_status == 'processing' and not order.get('started_at'):
        order['started_at'] = datetime.utcnow().isoformat()
    elif new_status in ['completed', 'failed', 'cancelled']:
        order['completed_at'] = datetime.utcnow().isoformat()
    
    # Update worker manager
    if new_status == 'cancelled':
        worker_manager.cancel_order(order_id)
    elif new_status == 'processing':
        worker_manager.add_order(order)
    
    # Log status change
    logger.audit(
        action="order_status_changed",
        user=admin['user_id'],
        resource="orders",
        status="success",
        details={
            'order_id': order_id,
            'old_status': current_status,
            'new_status': new_status
        }
    )
    
    return {
        "message": f"Order status updated to {new_status}",
        "order": order
    }

@app.get("/api/admin/system/logs")
async def get_system_logs(
    admin: Dict = Depends(require_admin),
    log_type: str = "all",
    limit: int = 100
):
    """Get system logs (admin only)"""
    # In production, query from log database
    # This is a simplified version
    
    logs = logger.get_security_logs(hours=24)  # Last 24 hours
    
    if log_type != 'all':
        logs = [log for log in logs if log.get('event_type') == log_type]
    
    return {
        "logs": logs[-limit:],  # Most recent logs
        "total": len(logs),
        "log_type": log_type
    }

@app.post("/api/admin/system/maintenance")
async def system_maintenance(
    action: str,
    admin: Dict = Depends(require_admin)
):
    """System maintenance actions (admin only)"""
    if action == 'restart_workers':
        result = worker_manager.restart_all_workers()
        message = "Workers restarted successfully"
    elif action == 'clear_queue':
        result = worker_manager.clear_queue()
        message = "Queue cleared successfully"
    elif action == 'backup_database':
        result = self._backup_database()
        message = "Database backup created"
    elif action == 'cleanup_logs':
        logger.cleanup_old_logs(days_to_keep=7)
        message = "Old logs cleaned up"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown action: {action}"
        )
    
    # Log maintenance action
    logger.audit(
        action="system_maintenance",
        user=admin['user_id'],
        resource="system",
        status="success",
        details={'action': action}
    )
    
    return {
        "message": message,
        "action": action,
        "timestamp": datetime.utcnow().isoformat()
    }

# Worker management endpoints
@app.get("/api/workers/status")
async def get_workers_status(
    admin: Dict = Depends(require_admin)
):
    """Get worker status (admin only)"""
    return worker_manager.get_detailed_status()

@app.post("/api/workers/scale")
async def scale_workers(
    scale_request: Dict[str, int],
    admin: Dict = Depends(require_admin)
):
    """Scale workers up/down (admin only)"""
    count = scale_request.get('count', 1)
    
    if count > 0:
        result = worker_manager.scale_up(count)
        message = f"Added {count} workers"
    elif count < 0:
        result = worker_manager.scale_down(abs(count))
        message = f"Removed {abs(count)} workers"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Count cannot be zero"
        )
    
    return {
        "message": message,
        "current_workers": worker_manager.get_active_worker_count(),
        "result": result
    }

# System endpoints
@app.get("/api/system/config")
async def get_system_config(
    admin: Dict = Depends(require_admin)
):
    """Get system configuration (admin only)"""
    config = {
        'system': {
            'version': '1.0.0',
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'startup_time': self._get_startup_time()
        },
        'workers': worker_manager.get_config(),
        'security': security_system.get_security_audit(),
        'logging': logger.get_logger_stats()
    }
    
    return config

@app.put("/api/system/config")
async def update_system_config(
    config_update: Dict[str, Any],
    admin: Dict = Depends(require_admin)
):
    """Update system configuration (admin only)"""
    # Validate config update
    valid_sections = ['workers', 'security', 'logging']
    
    for section in config_update.keys():
        if section not in valid_sections:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid section: {section}"
            )
    
    # Apply updates
    if 'workers' in config_update:
        worker_manager.update_config(config_update['workers'])
    
    if 'logging' in config_update:
        logger.set_log_level(config_update['logging'].get('level', 'INFO'))
    
    # Log config update
    logger.audit(
        action="config_updated",
        user=admin['user_id'],
        resource="system",
        status="success",
        details={'sections': list(config_update.keys())}
    )
    
    return {
        "message": "Configuration updated successfully",
        "updated_sections": list(config_update.keys())
    }

# Utility methods
def _get_system_load(self) -> Dict:
    """Get system load information"""
    import psutil
    
    return {
        'cpu_percent': psutil.cpu_percent(),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_percent': psutil.disk_usage('/').percent,
        'active_connections': len(psutil.net_connections()),
        'process_count': len(psutil.pids())
    }

def _get_startup_time(self) -> str:
    """Get system startup time"""
    import time
    return datetime.fromtimestamp(time.time() - psutil.boot_time()).isoformat()

def _backup_database(self) -> str:
    """Backup database"""
    backup_file = f"backup/db_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    
    os.makedirs('backup', exist_ok=True)
    
    backup_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'users': users_db,
        'orders': orders_db,
        'payments': payments_db
    }
    
    with open(backup_file, 'w') as f:
        json.dump(backup_data, f, indent=2, default=str)
    
    return backup_file

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    logger.error(
        f"HTTP error {exc.status_code}: {exc.detail}",
        path=request.url.path,
        method=request.method,
        status_code=exc.status_code
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": request.url.path
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.exception(
        f"Unhandled exception: {str(exc)}",
        path=request.url.path,
        method=request.method
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc) if os.getenv('ENVIRONMENT') == 'development' else None
        }
    )

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/dashboard")
async def serve_dashboard():
    """Serve admin dashboard"""
    return FileResponse("static/admin_dashboard.html")

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("VT ULTRA PRO API starting up")
    
    # Initialize worker manager
    worker_manager.initialize()
    
    # Start workers
    worker_manager.start_workers(min_workers=3)
    
    logger.info("API startup completed")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info("VT ULTRA PRO API shutting down")
    
    # Stop workers
    worker_manager.stop_all_workers()
    
    # Close connections
    await payment_processor.close()
    
    logger.info("API shutdown completed")

# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "api.rest_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )