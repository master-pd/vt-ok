"""
Telegram web app interface for VT ULTRA PRO
"""
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import json
from datetime import datetime
from typing import Dict, List, Optional
import asyncio
import uuid

app = FastAPI(title="VT ULTRA PRO Web App")
templates = Jinja2Templates(directory="templates")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# In-memory storage (use database in production)
users_db = {}
orders_db = {}
sessions = {}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/dashboard/{user_id}")
async def dashboard(request: Request, user_id: str):
    """User dashboard"""
    user = users_db.get(user_id)
    if not user:
        return JSONResponse({"error": "User not found"}, status_code=404)
    
    # Get user orders
    user_orders = [o for o in orders_db.values() if o['user_id'] == user_id]
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "orders": user_orders[-10:],  # Last 10 orders
            "stats": {
                "total_orders": len(user_orders),
                "total_views": sum(o.get('views', 0) for o in user_orders),
                "success_rate": calculate_success_rate(user_orders),
                "total_spent": sum(o.get('price', 0) for o in user_orders)
            }
        }
    )

@app.get("/api/user/{user_id}")
async def get_user_data(user_id: str):
    """Get user data API"""
    user = users_db.get(user_id)
    if not user:
        return JSONResponse({"error": "User not found"}, status_code=404)
    
    return JSONResponse({
        "user": user,
        "orders": [o for o in orders_db.values() if o['user_id'] == user_id],
        "stats": get_user_stats(user_id)
    })

@app.post("/api/order/create")
async def create_order(request: Request):
    """Create new order"""
    data = await request.json()
    
    order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6]}"
    
    order = {
        "order_id": order_id,
        "user_id": data['user_id'],
        "video_url": data['video_url'],
        "views": data['views'],
        "method": data.get('method', 'fast'),
        "price": data.get('price', 0),
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "delivered_views": 0,
        "success_rate": 0
    }
    
    orders_db[order_id] = order
    
    # Update user stats
    if data['user_id'] in users_db:
        users_db[data['user_id']]['total_orders'] = users_db[data['user_id']].get('total_orders', 0) + 1
        users_db[data['user_id']]['total_views'] = users_db[data['user_id']].get('total_views', 0) + data['views']
    
    return JSONResponse({"success": True, "order_id": order_id, "order": order})

@app.get("/api/orders/{user_id}")
async def get_user_orders(user_id: str, status: Optional[str] = None):
    """Get user orders"""
    user_orders = [o for o in orders_db.values() if o['user_id'] == user_id]
    
    if status:
        user_orders = [o for o in user_orders if o['status'] == status]
    
    return JSONResponse({"orders": user_orders})

@app.put("/api/order/{order_id}/status")
async def update_order_status(order_id: str, request: Request):
    """Update order status"""
    data = await request.json()
    
    if order_id not in orders_db:
        return JSONResponse({"error": "Order not found"}, status_code=404)
    
    orders_db[order_id]['status'] = data['status']
    orders_db[order_id]['updated_at'] = datetime.now().isoformat()
    
    if data.get('delivered_views'):
        orders_db[order_id]['delivered_views'] = data['delivered_views']
    
    if data.get('success_rate'):
        orders_db[order_id]['success_rate'] = data['success_rate']
    
    return JSONResponse({"success": True, "order": orders_db[order_id]})

@app.get("/api/analytics/{user_id}")
async def get_user_analytics(user_id: str):
    """Get user analytics"""
    user_orders = [o for o in orders_db.values() if o['user_id'] == user_id]
    
    if not user_orders:
        return JSONResponse({"error": "No orders found"}, status_code=404)
    
    # Calculate analytics
    analytics = {
        "daily_views": calculate_daily_views(user_orders),
        "method_distribution": calculate_method_distribution(user_orders),
        "success_rate_trend": calculate_success_trend(user_orders),
        "revenue_by_month": calculate_revenue_by_month(user_orders)
    }
    
    return JSONResponse(analytics)

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket for real-time updates"""
    await websocket.accept()
    
    # Add to active connections
    if user_id not in sessions:
        sessions[user_id] = []
    sessions[user_id].append(websocket)
    
    try:
        while True:
            # Wait for messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get('type') == 'subscribe':
                # Subscribe to order updates
                await websocket.send_text(json.dumps({
                    "type": "subscribed",
                    "channels": message.get('channels', []),
                    "timestamp": datetime.now().isoformat()
                }))
            
            elif message.get('type') == 'ping':
                # Respond to ping
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }))
    
    except WebSocketDisconnect:
        # Remove connection
        if user_id in sessions and websocket in sessions[user_id]:
            sessions[user_id].remove(websocket)

async def send_order_update(user_id: str, order_id: str, update: Dict):
    """Send order update via WebSocket"""
    if user_id in sessions:
        message = {
            "type": "order_update",
            "order_id": order_id,
            "update": update,
            "timestamp": datetime.now().isoformat()
        }
        
        for websocket in sessions[user_id]:
            try:
                await websocket.send_text(json.dumps(message))
            except:
                pass

# Helper functions
def calculate_success_rate(orders: List[Dict]) -> float:
    """Calculate average success rate"""
    if not orders:
        return 0
    
    completed_orders = [o for o in orders if o.get('success_rate', 0) > 0]
    if not completed_orders:
        return 0
    
    return sum(o['success_rate'] for o in completed_orders) / len(completed_orders)

def get_user_stats(user_id: str) -> Dict:
    """Get user statistics"""
    user_orders = [o for o in orders_db.values() if o['user_id'] == user_id]
    
    return {
        "total_orders": len(user_orders),
        "total_views": sum(o.get('views', 0) for o in user_orders),
        "delivered_views": sum(o.get('delivered_views', 0) for o in user_orders),
        "success_rate": calculate_success_rate(user_orders),
        "total_spent": sum(o.get('price', 0) for o in user_orders),
        "active_orders": len([o for o in user_orders if o['status'] in ['pending', 'processing']])
    }

def calculate_daily_views(orders: List[Dict]) -> List[Dict]:
    """Calculate daily views delivery"""
    daily_data = {}
    
    for order in orders:
        date = order['created_at'][:10]  # YYYY-MM-DD
        if date not in daily_data:
            daily_data[date] = 0
        daily_data[date] += order.get('delivered_views', 0)
    
    return [{"date": date, "views": views} for date, views in sorted(daily_data.items())]

def calculate_method_distribution(orders: List[Dict]) -> Dict:
    """Calculate distribution by method"""
    distribution = {}
    
    for order in orders:
        method = order.get('method', 'unknown')
        distribution[method] = distribution.get(method, 0) + 1
    
    return distribution

def calculate_success_trend(orders: List[Dict]) -> List[Dict]:
    """Calculate success rate trend over time"""
    trend = {}
    
    for order in orders:
        if order.get('success_rate', 0) > 0:
            date = order['created_at'][:7]  # YYYY-MM
            if date not in trend:
                trend[date] = []
            trend[date].append(order['success_rate'])
    
    return [
        {
            "month": month,
            "avg_success_rate": sum(rates) / len(rates),
            "order_count": len(rates)
        }
        for month, rates in sorted(trend.items())
    ]

def calculate_revenue_by_month(orders: List[Dict]) -> List[Dict]:
    """Calculate revenue by month"""
    revenue = {}
    
    for order in orders:
        month = order['created_at'][:7]  # YYYY-MM
        revenue[month] = revenue.get(month, 0) + order.get('price', 0)
    
    return [{"month": month, "revenue": amount} for month, amount in sorted(revenue.items())]

# HTML Templates
index_html = """
<!DOCTYPE html>
<html>
<head>
    <title>VT ULTRA PRO - TikTok View Service</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%);
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { 
            text-align: center; 
            padding: 30px 0;
            background: linear-gradient(90deg, #4CAF50 0%, #2196F3 100%);
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .header h1 { 
            font-size: 2.5em; 
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }
        .header p { 
            font-size: 1.2em; 
            opacity: 0.9;
            max-width: 600px;
            margin: 0 auto;
        }
        .stats-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px; 
            margin-bottom: 30px;
        }
        .stat-card { 
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            transition: transform 0.3s;
        }
        .stat-card:hover { transform: translateY(-5px); }
        .stat-card h3 { 
            font-size: 2em; 
            color: #4CAF50;
            margin-bottom: 10px;
        }
        .stat-card p { opacity: 0.8; }
        .main-content { 
            display: grid; 
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }
        @media (max-width: 768px) {
            .main-content { grid-template-columns: 1fr; }
        }
        .card { 
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 10px;
            padding: 25px;
        }
        .card h2 { 
            margin-bottom: 20px; 
            color: #4CAF50;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
        }
        .btn {
            display: inline-block;
            background: linear-gradient(90deg, #4CAF50 0%, #2196F3 100%);
            color: white;
            padding: 12px 25px;
            border-radius: 5px;
            text-decoration: none;
            font-weight: bold;
            transition: all 0.3s;
            border: none;
            cursor: pointer;
        }
        .btn:hover { 
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(76, 175, 80, 0.3);
        }
        .form-group { margin-bottom: 20px; }
        .form-group label { 
            display: block; 
            margin-bottom: 8px;
            font-weight: bold;
        }
        .form-control {
            width: 100%;
            padding: 12px;
            border-radius: 5px;
            border: 1px solid rgba(255,255,255,0.2);
            background: rgba(255,255,255,0.1);
            color: white;
            font-size: 1em;
        }
        .form-control:focus {
            outline: none;
            border-color: #4CAF50;
        }
        .order-status {
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
            background: rgba(255,255,255,0.1);
        }
        .status-pending { border-left: 4px solid #FFC107; }
        .status-processing { border-left: 4px solid #2196F3; }
        .status-completed { border-left: 4px solid #4CAF50; }
        .status-failed { border-left: 4px solid #F44336; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 VT ULTRA PRO</h1>
            <p>Premium TikTok View Service with 95%+ Success Rate</p>
            <div style="margin-top: 20px;">
                <a href="#order" class="btn">🎯 Place Order</a>
                <a href="#dashboard" class="btn" style="margin-left: 10px;">📊 Dashboard</a>
            </div>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <h3 id="total-orders">0</h3>
                <p>Total Orders</p>
            </div>
            <div class="stat-card">
                <h3 id="total-views">0</h3>
                <p>Total Views</p>
            </div>
            <div class="stat-card">
                <h3 id="success-rate">0%</h3>
                <p>Success Rate</p>
            </div>
            <div class="stat-card">
                <h3 id="active-orders">0</h3>
                <p>Active Orders</p>
            </div>
        </div>

        <div class="main-content">
            <div class="card">
                <h2>📈 Order Analytics</h2>
                <div style="height: 300px;">
                    <canvas id="analyticsChart"></canvas>
                </div>
            </div>

            <div class="card">
                <h2>⚡ Quick Order</h2>
                <form id="orderForm">
                    <div class="form-group">
                        <label for="videoUrl">TikTok Video URL</label>
                        <input type="url" id="videoUrl" class="form-control" 
                               placeholder="https://tiktok.com/@username/video/123456789" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="viewsCount">Number of Views</label>
                        <input type="number" id="viewsCount" class="form-control" 
                               min="100" max="100000" value="1000" required>
                        <div style="display: flex; gap: 10px; margin-top: 10px;">
                            <button type="button" onclick="setViews(100)" class="btn">100</button>
                            <button type="button" onclick="setViews(500)" class="btn">500</button>
                            <button type="button" onclick="setViews(1000)" class="btn">1K</button>
                            <button type="button" onclick="setViews(5000)" class="btn">5K</button>
                        </div>
                    </div>

                    <div class="form-group">
                        <label for="method">Delivery Method</label>
                        <select id="method" class="form-control" required>
                            <option value="fast">⚡ Fast Delivery ($2.99/1K)</option>
                            <option value="quality">🎯 High Quality ($3.99/1K)</option>
                            <option value="organic">🌱 Organic Growth ($5.99/1K)</option>
                            <option value="ai">🤖 AI Optimized ($7.99/1K)</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label>Estimated Price: <span id="estimatedPrice">$0.00</span></label>
                    </div>

                    <button type="submit" class="btn" style="width: 100%;">
                        🚀 Place Order Now
                    </button>
                </form>
            </div>
        </div>

        <div class="card" id="recentOrders">
            <h2>📋 Recent Orders</h2>
            <div id="ordersList"></div>
        </div>
    </div>

    <script>
        // Initialize variables
        let userId = localStorage.getItem('vt_user_id');
        if (!userId) {
            userId = 'user_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('vt_user_id', userId);
        }

        let ws = null;
        let analyticsChart = null;

        // Initialize WebSocket
        function initWebSocket() {
            ws = new WebSocket(`ws://${window.location.host}/ws/${userId}`);
            
            ws.onopen = function() {
                console.log('WebSocket connected');
                ws.send(JSON.stringify({ type: 'subscribe', channels: ['orders', 'updates'] }));
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            };
            
            ws.onclose = function() {
                console.log('WebSocket disconnected');
                setTimeout(initWebSocket, 3000);
            };
        }

        function handleWebSocketMessage(data) {
            if (data.type === 'order_update') {
                updateOrderInList(data.order_id, data.update);
                loadUserStats();
            }
        }

        // Load user data
        async function loadUserData() {
            try {
                const response = await fetch(`/api/user/${userId}`);
                const data = await response.json();
                
                if (data.user) {
                    updateStats(data.stats);
                    updateOrdersList(data.orders);
                    loadAnalytics();
                }
            } catch (error) {
                console.error('Error loading user data:', error);
            }
        }

        function updateStats(stats) {
            document.getElementById('total-orders').textContent = stats.total_orders;
            document.getElementById('total-views').textContent = stats.total_views.toLocaleString();
            document.getElementById('success-rate').textContent = stats.success_rate.toFixed(1) + '%';
            document.getElementById('active-orders').textContent = stats.active_orders;
        }

        function updateOrdersList(orders) {
            const container = document.getElementById('ordersList');
            container.innerHTML = '';
            
            const recentOrders = orders.slice(-5).reverse();
            
            recentOrders.forEach(order => {
                const statusClass = `status-${order.status}`;
                const orderElement = document.createElement('div');
                orderElement.className = `order-status ${statusClass}`;
                orderElement.innerHTML = `
                    <div style="display: flex; justify-content: space-between;">
                        <strong>${order.order_id}</strong>
                        <span style="text-transform: capitalize;">${order.status}</span>
                    </div>
                    <div style="margin-top: 5px;">
                        Views: ${order.views.toLocaleString()} | 
                        Price: $${order.price.toFixed(2)} |
                        ${order.created_at.substring(0, 10)}
                    </div>
                `;
                container.appendChild(orderElement);
            });
        }

        // Order form handling
        document.getElementById('orderForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const videoUrl = document.getElementById('videoUrl').value;
            const viewsCount = parseInt(document.getElementById('viewsCount').value);
            const method = document.getElementById('method').value;
            
            const methodPrices = {
                'fast': 2.99,
                'quality': 3.99,
                'organic': 5.99,
                'ai': 7.99
            };
            
            const price = (viewsCount / 1000) * methodPrices[method];
            
            const orderData = {
                user_id: userId,
                video_url: videoUrl,
                views: viewsCount,
                method: method,
                price: price
            };
            
            try {
                const response = await fetch('/api/order/create', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(orderData)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert('Order created successfully! Order ID: ' + result.order_id);
                    document.getElementById('orderForm').reset();
                    loadUserData();
                } else {
                    alert('Error creating order: ' + (result.error || 'Unknown error'));
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Error creating order. Please try again.');
            }
        });

        // Calculate price
        function calculatePrice() {
            const views = parseInt(document.getElementById('viewsCount').value) || 0;
            const method = document.getElementById('method').value;
            
            const methodPrices = {
                'fast': 2.99,
                'quality': 3.99,
                'organic': 5.99,
                'ai': 7.99
            };
            
            const price = (views / 1000) * methodPrices[method];
            document.getElementById('estimatedPrice').textContent = '$' + price.toFixed(2);
        }

        // Set views helper
        function setViews(count) {
            document.getElementById('viewsCount').value = count;
            calculatePrice();
        }

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            initWebSocket();
            loadUserData();
            
            // Calculate price on change
            document.getElementById('viewsCount').addEventListener('input', calculatePrice);
            document.getElementById('method').addEventListener('change', calculatePrice);
            
            // Initial calculation
            calculatePrice();
            
            // Set up analytics chart
            const ctx = document.getElementById('analyticsChart').getContext('2d');
            analyticsChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Views Delivered',
                        data: [],
                        borderColor: '#4CAF50',
                        backgroundColor: 'rgba(76, 175, 80, 0.1)',
                        tension: 0.3
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: {
                                color: '#fff'
                            }
                        }
                    },
                    scales: {
                        x: {
                            ticks: {
                                color: '#fff'
                            },
                            grid: {
                                color: 'rgba(255,255,255,0.1)'
                            }
                        },
                        y: {
                            ticks: {
                                color: '#fff'
                            },
                            grid: {
                                color: 'rgba(255,255,255,0.1)'
                            }
                        }
                    }
                }
            });
        });

        async function loadAnalytics() {
            try {
                const response = await fetch(`/api/analytics/${userId}`);
                const data = await response.json();
                
                if (data.daily_views) {
                    analyticsChart.data.labels = data.daily_views.map(d => d.date);
                    analyticsChart.data.datasets[0].data = data.daily_views.map(d => d.views);
                    analyticsChart.update();
                }
            } catch (error) {
                console.error('Error loading analytics:', error);
            }
        }

        function updateOrderInList(orderId, update) {
            const orders = document.querySelectorAll('.order-status');
            orders.forEach(order => {
                if (order.querySelector('strong').textContent === orderId) {
                    const statusSpan = order.querySelector('span');
                    if (statusSpan) {
                        statusSpan.textContent = update.status;
                        statusSpan.parentElement.parentElement.className = 
                            `order-status status-${update.status}`;
                    }
                }
            });
        }
    </script>
</body>
</html>
"""

# Create templates directory
import os
os.makedirs("templates", exist_ok=True)

# Save HTML template
with open("templates/index.html", "w") as f:
    f.write(index_html)

# Dashboard template
dashboard_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard - VT ULTRA PRO</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        /* Similar styling as index.html */
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%);
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { 
            display: flex; 
            justify-content: space-between;
            align-items: center;
            padding: 20px 0;
            margin-bottom: 30px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .header h1 { color: #4CAF50; }
        .user-info { text-align: right; }
        .stats-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px; 
            margin-bottom: 30px;
        }
        .stat-card { 
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 10px;
            padding: 20px;
            text-align: center;
        }
        .main-grid { 
            display: grid; 
            grid-template-columns: 2fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }
        @media (max-width: 1024px) {
            .main-grid { grid-template-columns: 1fr; }
        }
        .card { 
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 20px;
        }
        .btn {
            display: inline-block;
            background: linear-gradient(90deg, #4CAF50 0%, #2196F3 100%);
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            text-decoration: none;
            font-weight: bold;
            margin-right: 10px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        th { background: rgba(255,255,255,0.05); }
        .status-badge {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
        }
        .status-pending { background: #FFC107; color: #000; }
        .status-processing { background: #2196F3; color: #fff; }
        .status-completed { background: #4CAF50; color: #fff; }
        .status-failed { background: #F44336; color: #fff; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 VT ULTRA PRO Dashboard</h1>
            <div class="user-info">
                <h3>Welcome, {{ user.username or 'User' }}</h3>
                <p>Member since: {{ user.joined_at[:10] if user.joined_at else 'N/A' }}</p>
                <a href="/" class="btn">🏠 Home</a>
                <button onclick="placeOrder()" class="btn">🎯 New Order</button>
            </div>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <h3>{{ stats.total_orders }}</h3>
                <p>Total Orders</p>
            </div>
            <div class="stat-card">
                <h3>{{ "{:,}".format(stats.total_views) }}</h3>
                <p>Total Views</p>
            </div>
            <div class="stat-card">
                <h3>{{ "%.1f"|format(stats.success_rate) }}%</h3>
                <p>Success Rate</p>
            </div>
            <div class="stat-card">
                <h3>${{ "%.2f"|format(stats.total_spent) }}</h3>
                <p>Total Spent</p>
            </div>
        </div>

        <div class="main-grid">
            <div>
                <div class="card">
                    <h2>📈 Performance Analytics</h2>
                    <div style="height: 400px;">
                        <canvas id="performanceChart"></canvas>
                    </div>
                </div>

                <div class="card">
                    <h2>📋 Recent Orders</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Order ID</th>
                                <th>Views</th>
                                <th>Status</th>
                                <th>Created</th>
                                <th>Price</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for order in orders %}
                            <tr>
                                <td>{{ order.order_id }}</td>
                                <td>{{ "{:,}".format(order.views) }}</td>
                                <td>
                                    <span class="status-badge status-{{ order.status }}">
                                        {{ order.status|title }}
                                    </span>
                                </td>
                                <td>{{ order.created_at[:10] }}</td>
                                <td>${{ "%.2f"|format(order.price) }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

            <div>
                <div class="card">
                    <h2>⚡ Quick Actions</h2>
                    <div style="display: flex; flex-direction: column; gap: 10px; margin-top: 20px;">
                        <button onclick="placeOrder()" class="btn">🎯 New Order</button>
                        <button onclick="checkBalance()" class="btn">💰 Check Balance</button>
                        <button onclick="viewMethods()" class="btn">⚙️ View Methods</button>
                        <button onclick="contactSupport()" class="btn">🆘 Contact Support</button>
                        <button onclick="exportData()" class="btn">📥 Export Data</button>
                    </div>
                </div>

                <div class="card">
                    <h2>📊 Method Distribution</h2>
                    <div style="height: 300px;">
                        <canvas id="methodChart"></canvas>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        function placeOrder() {
            window.location.href = "/#order";
        }

        function checkBalance() {
            alert("Balance feature coming soon!");
        }

        // Initialize charts
        document.addEventListener('DOMContentLoaded', function() {
            // Performance Chart
            const perfCtx = document.getElementById('performanceChart').getContext('2d');
            new Chart(perfCtx, {
                type: 'line',
                data: {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                    datasets: [{
                        label: 'Views Delivered',
                        data: [12000, 19000, 15000, 25000, 22000, 30000],
                        borderColor: '#4CAF50',
                        backgroundColor: 'rgba(76, 175, 80, 0.1)'
                    }, {
                        label: 'Success Rate %',
                        data: [92, 94, 93, 95, 96, 97],
                        borderColor: '#2196F3',
                        backgroundColor: 'rgba(33, 150, 243, 0.1)',
                        yAxisID: 'y1'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                            ticks: { color: '#fff' },
                            grid: { color: 'rgba(255,255,255,0.1)' }
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            max: 100,
                            ticks: { color: '#fff' },
                            grid: { drawOnChartArea: false }
                        },
                        x: {
                            ticks: { color: '#fff' },
                            grid: { color: 'rgba(255,255,255,0.1)' }
                        }
                    }
                }
            });

            // Method Chart
            const methodCtx = document.getElementById('methodChart').getContext('2d');
            new Chart(methodCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Fast', 'Quality', 'Organic', 'AI'],
                    datasets: [{
                        data: [40, 25, 20, 15],
                        backgroundColor: [
                            '#4CAF50',
                            '#2196F3',
                            '#FFC107',
                            '#9C27B0'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: { color: '#fff' }
                        }
                    }
                }
            });
        });
    </script>
</body>
</html>
"""

with open("templates/dashboard.html", "w") as f:
    f.write(dashboard_html)