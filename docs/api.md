# VT ULTRA PRO API Documentation

## 📖 Overview

This document provides comprehensive documentation for the VT ULTRA PRO REST API and WebSocket API. The API follows RESTful principles and uses JSON for data exchange.

## 🔑 Authentication

### JWT Authentication

All API endpoints (except public ones) require JWT authentication.


## Authentication

### Telegram WebApp Authentication

For WebApp endpoints, authentication is handled via Telegram's WebApp init data:

1. Telegram sends `initData` parameter containing user information
2. Server verifies the hash using bot token
3. Server creates JWT token for subsequent requests

### JWT Token Authentication

For API endpoints, include JWT token in Authorization header:


## Rate Limiting

- **Public endpoints**: 100 requests per hour per IP
- **Authenticated endpoints**: 1000 requests per hour per user
- **Admin endpoints**: 5000 requests per hour per admin

## Error Codes

---

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 429 | Too Many Requests |
| 500 | Internal Server Error |

---

## User Endpoints

### Get User Information


**Response:**
```json
{
  "success": true,
  "user": {
    "id": 123456789,
    "telegram_id": 123456789,
    "username": "john_doe",
    "first_name": "John",
    "last_name": "Doe",
    "language": "en",
    "balance": 150.50,
    "total_spent": 500.00,
    "views_bought": 25000,
    "role": "user",
    "status": "active",
    "registered_at": "2024-01-15T10:30:00",
    "last_seen": "2024-01-20T14:45:00"
  },
  "stats": {
    "today_activity": 5,
    "referrals_count": 3,
    "active_sessions": 1
  }
}

{
  "success": true,
  "orders": [
    {
      "id": 1,
      "order_id": "ORD-20240120-ABC123",
      "video_url": "https://tiktok.com/@user/video/123456789",
      "video_id": "123456789",
      "view_count": 1000,
      "view_count_sent": 850,
      "view_count_delivered": 800,
      "status": "completed",
      "price": 3.50,
      "payment_method": "balance",
      "payment_status": "paid",
      "started_at": "2024-01-20T10:30:00",
      "completed_at": "2024-01-20T12:45:00",
      "created_at": "2024-01-20T10:25:00"
    }
  ],
  "total": 15,
  "limit": 20,
  "offset": 0
}

{
  "success": true,
  "order": {
    "id": 1,
    "order_id": "ORD-20240120-ABC123",
    "video_url": "https://tiktok.com/@user/video/123456789",
    "video_id": "123456789",
    "view_count": 1000,
    "view_count_sent": 850,
    "view_count_delivered": 800,
    "status": "completed",
    "price": 3.50,
    "payment_method": "balance",
    "payment_status": "paid",
    "started_at": "2024-01-20T10:30:00",
    "completed_at": "2024-01-20T12:45:00",
    "created_at": "2024-01-20T10:25:00"
  },
  "progress": [
    {
      "timestamp": "2024-01-20T10:30:00",
      "progress_percent": 0,
      "status": "created",
      "details": {}
    },
    {
      "timestamp": "2024-01-20T11:00:00",
      "progress_percent": 50,
      "status": "processing",
      "details": {"views_sent": 500, "views_delivered": 450}
    },
    {
      "timestamp": "2024-01-20T12:45:00",
      "progress_percent": 100,
      "status": "completed",
      "details": {"views_sent": 850, "views_delivered": 800}
    }
  ],
  "methods": [
    {
      "method_name": "browser_automation",
      "views_sent": 500,
      "views_delivered": 480,
      "success_rate": 96.0,
      "start_time": "2024-01-20T10:35:00",
      "end_time": "2024-01-20T11:30:00",
      "status": "completed"
    }
  ]
}


#### Login
```http
POST /api/auth/login