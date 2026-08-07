# Professional AI - Credit System API Documentation

## Overview
The credit system provides a comprehensive billing and usage tracking solution for Professional AI. It supports free and pro plans, monthly credit resets, and real-time usage tracking.

## Database Schema

### Tables
- **credits** - User credit balances and reset dates
- **credit_transactions** - Audit trail of all credit changes

## API Endpoints

### 1. Get Credit Information
```http
GET /credits/info
Authorization: Bearer {token}
```

**Response:**
```json
{
  "balance": 1500,
  "total_granted": 2000,
  "total_consumed": 500,
  "plan": "pro",
  "last_reset_at": "2025-01-01T00:00:00Z",
  "next_reset_at": "2025-02-01T00:00:00Z",
  "rollover_percentage": 20,
  "display_text": "Credits left: 1,500 / 2,000"
}
```

### 2. Use a Feature
```http
POST /credits/use
Authorization: Bearer {token}
Content-Type: application/json

{
  "feature": "chat",
  "language": "en",
  "usage_log_id": "optional-uuid"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Credits consumed",
  "credit_info": {
    "balance": 1499,
    "total_granted": 2000,
    "total_consumed": 501,
    "plan": "pro",
    "display_text": "Credits left: 1,499 / 2,000"
  },
  "can_retry": false
}
```

**Feature Types & Costs:**
- `chat` - 1 credit
- `code_generation` - 5 credits
- `image_generation` - 10 credits
- `voice_message` - 2 credits
- `premium_language` - 2 credits
- `security_tool` - 5 credits

### 3. Get Plan Limits
```http
GET /credits/limits
Authorization: Bearer {token}
```

**Response:**
```json
{
  "plan": "free",
  "daily_code_generation": 3,
  "daily_chat": 50,
  "monthly_credits": 0,
  "vault_storage_mb": 3,
  "free_languages": ["en", "ur", "hi", "bn"],
  "credit_costs": {
    "chat": 1,
    "code_generation": 5,
    "image_generation": 10,
    "voice_message": 2,
    "premium_language": 2,
    "security_tool": 5
  },
  "features": ["chat", "code_generation", "vault"]
}
```

### 4. Get Usage Statistics
```http
GET /credits/stats?days=30
Authorization: Bearer {token}
```

**Response:**
```json
{
  "stats": {
    "chat": {
      "count": 150,
      "total_tokens": 15000
    },
    "code_generation": {
      "count": 25,
      "total_tokens": 5000
    }
  },
  "period_days": 30
}
```

### 5. Admin: Adjust Credits
```http
POST /credits/admin/adjust
Authorization: Bearer {token}
Content-Type: application/json

{
  "user_id": "user-uuid",
  "amount": 100,
  "reason": "Promotional bonus"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully adjusted 100 credits for user@example.com",
  "new_balance": 2100,
  "user_email": "user@example.com"
}
```

### 6. Admin: Grant Trial
```http
POST /credits/admin/grant-trial
Authorization: Bearer {token}
Content-Type: application/json

{
  "user_id": "user-uuid"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Granted 3-day trial to user@example.com",
  "trial_end": "2025-01-04T00:00:00Z",
  "credits_granted": 2000
}
```

### 7. Admin: Revoke Trial
```http
POST /credits/admin/revoke-trial
Authorization: Bearer {token}
Content-Type: application/json

{
  "user_id": "user-uuid"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Revoked trial for user@example.com. Downgraded to free plan."
}
```

## Credit Costs

| Action | Credits | Notes |
|--------|---------|-------|
| Chat Message | 1 | Per message |
| Code Generation | 5 | Per generation |
| Image Generation | 10 | Per image |
| Voice Message | 2 | Per message |
| Premium Language | 2 | Per message (non-free languages) |
| Security Tool | 5 | Per query |

## Plan Comparison

### Free Plan
- **Daily Limits:**
  - 3 code generations per day
  - 50 chat messages per day
- **Vault Storage:** 3 MB
- **Languages:** English, Urdu, Hindi, Bengali only
- **Credits:** 0 (uses daily limits instead)

### Pro Plan ($X/month)
- **Monthly Credits:** 2,000
- **Rollover:** 20% of unused credits
- **Vault Storage:** Unlimited
- **Languages:** All 30+ languages
- **Features:** All features unlocked

### Trial Plan
- **Duration:** 3 days
- **Credits:** 2,000 (same as Pro)
- **Auto-charge:** Yes (requires consent)
- **Notifications:** Email + SMS before charge

## Credit Flow

### Monthly Reset
1. Check if `next_reset_at` has passed
2. Calculate rollover: `balance * 0.2`
3. Set new balance: `2000 + rollover`
4. Update `last_reset_at` and `next_reset_at`
5. Create transaction record

### Credit Consumption
1. Check user's plan
2. If free plan: check daily limits
3. If pro/trial: check credit balance
4. Deduct credits atomically (SELECT FOR UPDATE)
5. Update Redis cache
6. Create transaction record

### Payment Webhook
1. Receive Stripe webhook
2. Verify signature (production)
3. Update subscription plan to "pro"
4. Grant 2000 credits
5. Set reset dates
6. Create revenue log

### Refund
1. Verify admin privileges
2. Check revenue log exists and not refunded
3. Calculate credits to refund
4. Grant credits back to user
5. Update revenue log status
6. Create refund log

## Redis Caching

### Keys
- `credits:{user_id}` - Cached credit balance (TTL: 5 minutes)

### Operations
- **GET** - Fast credit balance reads
- **SETEX** - Update cache with TTL
- **DEL** - Invalidate on updates

## Error Handling

### Insufficient Credits
```json
{
  "success": false,
  "message": "Insufficient credits. You need 5 credits but have 3.",
  "credit_info": {...},
  "can_retry": true
}
```

### Free Plan Limit Reached
```json
{
  "success": false,
  "message": "Free plan limit reached: 3 code generations per day. Upgrade to Pro for unlimited access.",
  "can_retry": true
}
```

### Premium Language Restriction
```json
{
  "success": false,
  "message": "Language 'fr' requires Pro plan. Upgrade to access 30+ premium languages.",
  "can_retry": true
}
```

## Integration Guide

### Using Credits in AI Features

```python
from app.services.credit_service import CreditService
from app.routes.credits import get_redis

# In your endpoint
@router.post("/chat")
async def chat_endpoint(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    # Check if user can use the feature
    credit_service = CreditService(db, redis_client)
    success, message, credit_info = await credit_service.use_feature(
        user_id=str(current_user.id),
        feature="chat",
        language=request.language
    )
    
    if not success:
        raise HTTPException(status_code=403, detail=message)
    
    # Process the chat message
    response = await process_chat(request.message)
    
    return {
        "response": response,
        "credits_remaining": credit_info["balance"]
    }
```

## Testing

### Test Credit Consumption
```bash
# Use a feature
curl -X POST http://localhost:8000/credits/use \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"feature": "chat", "language": "en"}'
```

### Test Admin Adjust
```bash
# Adjust credits
curl -X POST http://localhost:8000/credits/admin/adjust \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-uuid", "amount": 100, "reason": "Bonus"}'
```

### Test Trial Grant
```bash
# Grant trial
curl -X POST http://localhost:8000/credits/admin/grant-trial \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-uuid"}'
```

## Monitoring

### Key Metrics
- Total credits granted per day
- Total credits consumed per day
- Active subscriptions
- Trial conversions
- Failed payments
- Refund rate

### Alerts
- Credits running low (< 10% remaining)
- Payment failures
- Trial expiring (< 24 hours)
- Unusual usage patterns

## Security

### Race Condition Prevention
- Uses `SELECT FOR UPDATE` for atomic operations
- PostgreSQL row-level locking
- Redis for fast reads with DB as source of truth

### Access Control
- Admin endpoints require `is_admin=True`
- Users can only view their own credits
- All transactions are logged

### Data Integrity
- Foreign key constraints
- Unique constraints on user_id
- Transaction audit trail
- Rollover percentage validation

## Deployment

### Environment Variables
```bash
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/professional_ai
```

### Database Migration
```bash
# Run schema
psql -U postgres -d professional_ai -f database/schema.sql

# Or use Alembic
alembic revision --autogenerate -m "Add credit system"
alembic upgrade head
```

### Redis Setup
```bash
# Install Redis
docker run -d -p 6379:6379 redis:alpine

# Or use Redis Cloud
```

## Troubleshooting

### Credits Not Updating
1. Check Redis connection
2. Verify database commit
3. Check transaction logs
4. Review application logs

### Race Conditions
- Ensure `with_for_update()` is used
- Check database isolation level
- Monitor lock wait timeouts

### Cache Invalidation
- Cache auto-invalidates on updates
- TTL: 5 minutes
- Manual invalidation available

## Support

For issues or questions:
- Email: support@professionalai.com
- Documentation: /api/docs
- Health Check: /api/health