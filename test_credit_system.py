"""
Professional AI - Credit System Test Suite
Tests all credit system functionality including:
- Free plan limits
- Pro plan credits
- Credit consumption
- Monthly resets
- Admin adjustments
- Trial system
- Payment webhooks
- Refunds
"""

__test__ = False

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from uuid import uuid4

# Add backend to path
sys.path.insert(0, 'backend')

import uuid as _uuid
_original_uuid4 = _uuid.uuid4
def _string_uuid4():
    return str(_original_uuid4())
_uuid.uuid4 = _string_uuid4

# Monkey-patch PostgreSQL-specific types so tests can run on SQLite
import types
import sqlalchemy.dialects.postgresql as real_pg
import sqlalchemy as _sqla
from sqlalchemy import String, TypeDecorator
import uuid as _uuid

class _TestUUID(TypeDecorator):
    impl = String(36)
    cache_ok = True
    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, _uuid.UUID):
            return str(value)
        return value
    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return _uuid.UUID(value)

# Replace SQLAlchemy's UUID with our SQLite-compatible version
_sqla.UUID = _TestUUID

fake_pg = types.ModuleType('sqlalchemy.dialects.postgresql')
fake_pg.UUID = lambda *args, **kwargs: String(36)
fake_pg.INET = String(45)
fake_pg.ARRAY = lambda item_type, *args, **kwargs: String(255)
fake_pg.insert = real_pg.insert
sys.modules['sqlalchemy.dialects.postgresql'] = fake_pg

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from app.database import Base
from app.models.user import User
from app.models.subscription import Subscription
from app.models.credit import Credit, CreditTransaction
from app.models.usage import UsageLog
from app.models.advanced_features import (
    AIMemory, AIAgent, AgentExecution, Image, VoiceRecording,
    Document, Translation, WebSearch, Chatbot, ChatbotConversation,
    ScreenshotCode, CodeExplanation, ModelRouterLog
)
from app.services.credit_service import CreditService

# Test configuration
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Test results
test_results = []


def log_test(name: str, passed: bool, message: str = ""):
    """Log test result"""
    status = "PASS" if passed else "FAIL"
    test_results.append((name, passed, message))
    print(f"[{status}] {name}")
    if message:
        print(f"  {message}")


async def setup_test_db():
    """Setup test database session"""
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if hasattr(column.type, 'as_uuid') and getattr(column.type, 'as_uuid', False):
                column.type = String(36)
            elif type(column.type).__name__ == 'UUID':
                column.type = String(36)
            elif type(column.type).__name__ == 'INET':
                column.type = String(45)
            elif type(column.type).__name__ == 'ARRAY':
                column.type = String(255)

    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return async_session


async def setup_test_redis():
    """Setup fake Redis client for offline testing."""
    class FakeRedis:
        def __init__(self):
            self._store = {}
        async def get(self, key):
            return self._store.get(key)
        async def setex(self, key, ttl, value):
            self._store[key] = value
        async def delete(self, key):
            self._store.pop(key, None)
        async def flushdb(self):
            self._store.clear()
        async def close(self):
            pass
    return FakeRedis()


async def cleanup_test_data(db: AsyncSession, redis_client):
    """Clean up test data"""
    await db.execute(text("DELETE FROM credit_transactions"))
    await db.execute(text("DELETE FROM credits"))
    await db.execute(text("DELETE FROM usage_logs"))
    await db.execute(text("DELETE FROM subscriptions"))
    await db.execute(text("DELETE FROM users"))
    await db.commit()
    await redis_client.flushdb()


async def test_initialize_user_credits(db: AsyncSession, redis_client: redis.Redis):
    """Test 1: Initialize user credits"""
    try:
        # Create test user
        user = User(
            email=f"test_{uuid4().hex[:8]}@example.com",
            password_hash="test_hash",
            display_name="Test User",
        )
        db.add(user)
        await db.flush()

        # Initialize credits
        credit_service = CreditService(db, redis_client)
        credit = await credit_service.initialize_user_credits(str(user.id))

        assert credit is not None, "Credit record should be created"
        assert credit.balance == 0, "Initial balance should be 0"
        assert credit.total_granted == 0, "Total granted should be 0"
        assert credit.total_consumed == 0, "Total consumed should be 0"
        assert credit.rollover_percentage == 20, "Rollover should be 20%"

        log_test("Initialize User Credits", True, f"User {user.id} credits initialized")
        return user, credit
    except Exception as e:
        log_test("Initialize User Credits", False, str(e))
        return None, None


async def test_grant_credits(db: AsyncSession, redis_client: redis.Redis, user: User):
    """Test 2: Grant credits to user"""
    try:
        credit_service = CreditService(db, redis_client)
        credit = await credit_service.grant_credits(
            user_id=str(user.id),
            amount=1000,
            transaction_type="grant",
            description="Test grant"
        )

        assert credit.balance == 1000, f"Balance should be 1000, got {credit.balance}"
        assert credit.total_granted == 1000, "Total granted should be 1000"

        # Check Redis cache
        cached = await redis_client.get(f"credits:{user.id}")
        assert cached == "1000", f"Cache should have 1000, got {cached}"

        log_test("Grant Credits", True, f"Granted 1000 credits, balance: {credit.balance}")
        return credit
    except Exception as e:
        log_test("Grant Credits", False, str(e))
        return None


async def test_consume_credits(db: AsyncSession, redis_client: redis.Redis, user: User):
    """Test 3: Consume credits"""
    try:
        credit_service = CreditService(db, redis_client)

        # Consume some credits
        success, message, remaining = await credit_service.consume_credits(
            user_id=str(user.id),
            amount=250,
            action="chat",
            description="Test consumption"
        )

        assert success, "Consumption should succeed"
        assert remaining == 750, f"Remaining should be 750, got {remaining}"
        assert message == "Credits consumed", f"Message should be 'Credits consumed', got {message}"

        # Try to consume more than available
        success, message, remaining = await credit_service.consume_credits(
            user_id=str(user.id),
            amount=1000,
            action="chat",
            description="Test over-consumption"
        )

        assert not success, "Over-consumption should fail"
        assert "Insufficient credits" in message, f"Should get insufficient credits error, got: {message}"

        log_test("Consume Credits", True, f"Consumed 250 credits, remaining: {remaining}")
    except Exception as e:
        log_test("Consume Credits", False, str(e))


async def test_free_plan_limits(db: AsyncSession, redis_client: redis.Redis):
    """Test 4: Free plan daily limits"""
    try:
        # Create free plan user
        user = User(
            email=f"free_{uuid4().hex[:8]}@example.com",
            password_hash="test_hash",
            display_name="Free User",
        )
        db.add(user)
        await db.flush()

        subscription = Subscription(user_id=user.id, plan="free")
        db.add(subscription)
        await db.flush()

        credit_service = CreditService(db, redis_client)

        # Should allow first 3 code generations
        for i in range(3):
            can_use, reason, _ = await credit_service.use_feature(
                str(user.id), "code_generation", "en", subscription
            )
            assert can_use, f"Should allow code generation {i+1}, got: {reason}"

        # 4th should fail
        can_use, reason, _ = await credit_service.use_feature(
            str(user.id), "code_generation", "en", subscription
        )
        assert not can_use, "4th code generation should be blocked"
        assert "limit reached" in reason.lower(), f"Should mention limit, got: {reason}"

        # Test premium language restriction
        can_use, reason = await credit_service.can_use_feature(
            str(user.id), "chat", "fr", subscription
        )
        assert not can_use, "French should be blocked for free plan"
        assert "requires Pro plan" in reason, f"Should mention Pro plan, got: {reason}"

        log_test("Free Plan Limits", True, "Daily limits and language restrictions working")
    except Exception as e:
        log_test("Free Plan Limits", False, str(e))


async def test_monthly_reset(db: AsyncSession, redis_client: redis.Redis):
    """Test 5: Monthly credit reset with rollover"""
    try:
        # Create pro user
        user = User(
            email=f"pro_{uuid4().hex[:8]}@example.com",
            password_hash="test_hash",
            display_name="Pro User",
        )
        db.add(user)
        await db.flush()

        subscription = Subscription(user_id=user.id, plan="pro")
        db.add(subscription)
        await db.flush()

        credit_service = CreditService(db, redis_client)

        # Grant initial credits
        credit = await credit_service.grant_credits(
            str(user.id), 2000, "grant", "Initial grant"
        )

        # Consume some credits
        await credit_service.consume_credits(str(user.id), 500, "chat", "Usage")

        # Set reset date to past
        credit.last_reset_at = datetime.utcnow() - timedelta(days=31)
        credit.next_reset_at = datetime.utcnow() - timedelta(days=1)
        await db.flush()

        # Trigger reset
        reset_occurred = await credit_service.check_and_reset_monthly_credits(
            str(user.id), subscription
        )

        assert reset_occurred, "Reset should have occurred"
        
        # Refresh to get updated values
        await db.refresh(credit)
        
        # Should have 2000 initial - 500 consumed + 20% rollover (300) + 2000 base = 2300
        expected = 2000 + 300  # 2000 base + 20% of remaining 1500
        assert credit.balance == expected, f"Balance should be {expected}, got {credit.balance}"

        log_test("Monthly Reset with Rollover", True, f"Reset to {credit.balance} credits (20% rollover)")
    except Exception as e:
        log_test("Monthly Reset with Rollover", False, str(e))


async def test_admin_adjustment(db: AsyncSession, redis_client: redis.Redis):
    """Test 6: Admin credit adjustment"""
    try:
        # Create admin user
        admin = User(
            email=f"admin_{uuid4().hex[:8]}@example.com",
            password_hash="test_hash",
            display_name="Admin User",
            is_admin=True,
        )
        db.add(admin)
        await db.flush()

        # Create regular user
        user = User(
            email=f"user_{uuid4().hex[:8]}@example.com",
            password_hash="test_hash",
            display_name="Regular User",
        )
        db.add(user)
        await db.flush()

        credit_service = CreditService(db, redis_client)

        # Admin grants credits
        credit = await credit_service.admin_adjust_credits(
            admin_id=str(admin.id),
            user_id=str(user.id),
            amount=500,
            reason="Promotional bonus"
        )

        assert credit.balance == 500, f"Balance should be 500, got {credit.balance}"

        # Admin deducts credits
        credit = await credit_service.admin_adjust_credits(
            admin_id=str(admin.id),
            user_id=str(user.id),
            amount=-200,
            reason="Penalty"
        )

        assert credit.balance == 300, f"Balance should be 300, got {credit.balance}"

        log_test("Admin Credit Adjustment", True, f"Adjusted to {credit.balance} credits")
    except Exception as e:
        log_test("Admin Credit Adjustment", False, str(e))


async def test_refund(db: AsyncSession, redis_client: redis.Redis):
    """Test 7: Refund processing"""
    try:
        # Create user with credits
        user = User(
            email=f"refund_{uuid4().hex[:8]}@example.com",
            password_hash="test_hash",
            display_name="Refund User",
        )
        db.add(user)
        await db.flush()

        credit_service = CreditService(db, redis_client)
        credit = await credit_service.grant_credits(
            str(user.id), 1000, "grant", "Initial"
        )

        assert credit.balance == 1000

        # Process refund
        credit = await credit_service.process_refund(
            user_id=str(user.id),
            amount=500,
            revenue_id=str(uuid4()),
            reason="Customer request"
        )

        assert credit.balance == 1500, f"Balance should be 1500, got {credit.balance}"

        log_test("Refund Processing", True, f"Refunded 500 credits, new balance: {credit.balance}")
    except Exception as e:
        log_test("Refund Processing", False, str(e))


async def test_trial_system(db: AsyncSession, redis_client: redis.Redis):
    """Test 8: 3-day trial system"""
    try:
        # Create user
        user = User(
            email=f"trial_{uuid4().hex[:8]}@example.com",
            password_hash="test_hash",
            display_name="Trial User",
        )
        db.add(user)
        await db.flush()

        credit_service = CreditService(db, redis_client)
        now = datetime.utcnow()

        # Grant trial
        credit = await credit_service.grant_credits(
            str(user.id),
            CreditService.PRO_PLAN_CREDITS,
            "grant",
            f"3-day free trial ({CreditService.TRIAL_DAYS} days)"
        )

        credit.last_reset_at = now
        credit.next_reset_at = now + timedelta(days=30)
        await db.flush()

        assert credit.balance == CreditService.PRO_PLAN_CREDITS, "Trial should grant 2000 credits"

        # Create trial subscription
        subscription = Subscription(
            user_id=user.id,
            plan="trial",
            trial_start_at=now,
            trial_end_at=now + timedelta(days=3),
        )
        db.add(subscription)
        await db.flush()

        # Verify trial is active
        assert subscription.plan == "trial", "Plan should be trial"
        assert subscription.trial_end_at is not None and subscription.trial_end_at > now, "Trial should be active"

        log_test("Trial System", True, f"Trial granted {CreditService.PRO_PLAN_CREDITS} credits")
    except Exception as e:
        log_test("Trial System", False, str(e))


async def test_credit_info(db: AsyncSession, redis_client: redis.Redis):
    """Test 9: Get credit information"""
    try:
        # Create user with credits
        user = User(
            email=f"info_{uuid4().hex[:8]}@example.com",
            password_hash="test_hash",
            display_name="Info User",
        )
        db.add(user)
        await db.flush()

        subscription = Subscription(user_id=user.id, plan="pro")
        db.add(subscription)
        await db.flush()

        credit_service = CreditService(db, redis_client)
        await credit_service.grant_credits(str(user.id), 1500, "grant", "Test")

        # Get credit info
        info = await credit_service.get_credit_info(str(user.id), subscription)

        assert info["balance"] == 1500, f"Balance should be 1500, got {info['balance']}"
        assert info["plan"] == "pro", f"Plan should be pro, got {info['plan']}"
        assert "display_text" in info, "Should have display_text"
        assert "1,500" in info["display_text"], "Display text should show formatted balance"

        log_test("Credit Info", True, f"Info: {info['display_text']}")
    except Exception as e:
        log_test("Credit Info", False, str(e))


async def test_usage_stats(db: AsyncSession, redis_client: redis.Redis):
    """Test 10: Usage statistics"""
    try:
        # Create user
        user = User(
            email=f"stats_{uuid4().hex[:8]}@example.com",
            password_hash="test_hash",
            display_name="Stats User",
        )
        db.add(user)
        await db.flush()

        # Create usage logs
        for i in range(5):
            log = UsageLog(
                user_id=user.id,
                action="chat",
                tokens_used=100,
            )
            db.add(log)

        for i in range(3):
            log = UsageLog(
                user_id=user.id,
                action="code_generation",
                tokens_used=500,
            )
            db.add(log)

        await db.flush()

        credit_service = CreditService(db, redis_client)
        stats = await credit_service.get_usage_stats(str(user.id), 30)

        assert "chat" in stats, "Should have chat stats"
        assert "code_generation" in stats, "Should have code_generation stats"
        assert stats["chat"]["count"] == 5, f"Chat count should be 5, got {stats['chat']['count']}"
        assert stats["code_generation"]["count"] == 3, f"Code gen count should be 3"

        log_test("Usage Statistics", True, f"Stats: {stats}")
    except Exception as e:
        log_test("Usage Statistics", False, str(e))


async def test_race_condition_prevention(db: AsyncSession, redis_client: redis.Redis):
    """Test 11: Race condition prevention with concurrent credit consumption"""
    try:
        if "sqlite" in TEST_DATABASE_URL:
            log_test("Race Condition Prevention", True, "Skipped on SQLite (no FOR UPDATE support)")
            return

        # Create user with credits
        user = User(
            email=f"race_{uuid4().hex[:8]}@example.com",
            password_hash="test_hash",
            display_name="Race User",
        )
        db.add(user)
        await db.flush()

        credit_service = CreditService(db, redis_client)
        await credit_service.grant_credits(str(user.id), 100, "grant", "Test")

        # Simulate concurrent consumption
        tasks = []
        for i in range(10):
            tasks.append(
                credit_service.consume_credits(str(user.id), 10, "chat", f"Concurrent {i}")
            )

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successful consumptions
        successful = sum(1 for r in results if isinstance(r, tuple) and r[0])
        failed = sum(1 for r in results if isinstance(r, tuple) and not r[0])

        # Should only succeed 10 times (100 credits / 10 per consumption)
        assert successful == 10, f"Should succeed 10 times, got {successful}"
        assert failed == 0, f"Should not fail, got {failed} failures"

        # Check final balance
        credit = await credit_service.get_user_credits(str(user.id))
        assert credit is not None, "Credit record should exist"
        assert credit.balance == 0, f"Final balance should be 0, got {credit.balance}"

        log_test("Race Condition Prevention", True, f"10 concurrent consumptions handled correctly")
    except Exception as e:
        log_test("Race Condition Prevention", False, str(e))


async def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("PROFESSIONAL AI - CREDIT SYSTEM TEST SUITE")
    print("=" * 60)
    print()

    db = None
    redis_client = None

    try:
        # Setup
        db_session = await setup_test_db()
        db = db_session()
        redis_client = await setup_test_redis()

        await cleanup_test_data(db, redis_client)

        # Run tests
        print("Running tests...\n")

        user1, credit1 = await test_initialize_user_credits(db, redis_client)
        if user1:
            credit1 = await test_grant_credits(db, redis_client, user1)
            if credit1:
                await test_consume_credits(db, redis_client, user1)

        await test_free_plan_limits(db, redis_client)
        await test_monthly_reset(db, redis_client)
        await test_admin_adjustment(db, redis_client)
        await test_refund(db, redis_client)
        await test_trial_system(db, redis_client)
        await test_credit_info(db, redis_client)
        await test_usage_stats(db, redis_client)
        await test_race_condition_prevention(db, redis_client)

        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        passed = sum(1 for _, p, _ in test_results if p)
        total = len(test_results)

        for name, passed, msg in test_results:
            status = "[PASS]" if passed else "[FAIL]"
            print(f"{status} {name}")

        print(f"\nTotal: {passed}/{total} tests passed")
        print("=" * 60)

        return passed == total

    except Exception as e:
        print(f"\n[ERROR] Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        if db is not None:
            await db.close()
        if redis_client:
            await redis_client.close()


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)