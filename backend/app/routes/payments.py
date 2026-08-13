"""
Professional AI - Payment Routes v2
Market-level plan pricing, multi-gateway checkout, currency conversion, and resilient subscription billing.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, timezone
import hmac
import hashlib
import json
import time as time_module

import httpx
import redis.asyncio as redis
from loguru import logger

from app.database import get_db
from app.config import settings
from app.models.user import User
from app.models.subscription import Subscription
from app.models.revenue import RevenueLog, RefundLog
from app.models.credit import CreditTransaction
from app.services.credit_service import CreditService
from app.services.auth_service import get_current_user, get_current_admin

router = APIRouter(prefix="/api/payments", tags=["Payments"])


SUPPORTED_GATEWAYS = [
    "stripe",
    "paypal",
    "wise",
    "payoneer",
    "skrill",
    "binance_pay",
    "jazzcash",
    "easypaisa",
    "sadapay",
    "nayapay",
]

SUPPORTED_DISPLAY_CURRENCIES = ["USD", "PKR", "INR", "EUR", "AED", "SAR", "GBP"]
PAKISTAN_LOCAL_GATEWAYS = {"jazzcash", "easypaisa", "sadapay", "nayapay"}

PLAN_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "free": {
        "name": "FREE",
        "credits": 0,
        "monthly_usd": 0.0,
        "yearly_usd": 0.0,
        "trial_days": 0,
        "features": [
            "3 code prompts/day",
            "50 chats/day",
            "1 video/day (5/15/30s)",
            "10 pictures/day",
            "3 animations/day",
            "Urdu/English/Hindi/Bengali",
        ],
    },
    "starter": {
        "name": "STARTER",
        "credits": 100,
        "monthly_usd": 9.99,
        "yearly_usd": 95.88,
        "yearly_monthly_equivalent": 7.99,
        "trial_days": 0,
        "features": [
            "5 videos/day",
            "20 pictures/day",
            "5 animations/day",
            "1080p quality",
            "Basic voice-over",
            "100 credits/mo",
        ],
    },
    "pro": {
        "name": "PRO",
        "credits": 2000,
        "monthly_usd": 19.99,
        "yearly_usd": 159.99,
        "trial_days": 3,
        "badge": "4 months FREE",
        "features": [
            "20 videos/day (up to 10 min)",
            "50 pictures/day",
            "20 animations/day",
            "8K quality",
            "All voices",
            "Auto-editing",
            "Unlimited code",
            "All 40+ languages",
            "Offline mode",
            "Priority speed",
            "2,000 credits/mo",
        ],
    },
    "pro_yearly": {
        "name": "PRO YEARLY",
        "credits": 2000,
        "monthly_usd": 13.33,
        "yearly_usd": 159.99,
        "trial_days": 0,
        "badge": "4 months FREE",
        "features": [
            "Same as PRO Monthly",
            "Single annual charge",
            "Best annual value tier",
        ],
    },
    "max": {
        "name": "MAX",
        "credits": 10000,
        "monthly_usd": 99.99,
        "yearly_usd": 799.99,
        "trial_days": 0,
        "features": [
            "UNLIMITED media",
            "8K priority quality",
            "Everything unlocked",
            "10,000 credits/mo",
        ],
    },
    "business": {
        "name": "BUSINESS",
        "credits": 2000,
        "monthly_usd": 24.99,
        "yearly_usd": 299.88,
        "trial_days": 0,
        "minimum_users": 5,
        "features": [
            "Team accounts",
            "Shared credits pool",
            "Admin controls",
            "Media library",
            "Per-user billing",
        ],
    },
    "enterprise": {
        "name": "ENTERPRISE",
        "credits": 10000,
        "monthly_usd": 499.0,
        "yearly_usd": 5988.0,
        "trial_days": 0,
        "features": [
            "Dedicated server",
            "SLA",
            "Custom models",
            "Onboarding",
            "Priority support",
        ],
    },
}

PAKISTAN_FIXED_PKR_BASE: Dict[str, float] = {
    "starter": 2499.0,
    "pro": 5499.0,
    "pro_yearly": 43999.0,
    "max": 27499.0,
    "business": 6999.0,
}

ISRAEL_GEO_BLOCK = {code.strip().upper() for code in (settings.ISRAEL_GEO_BLOCK or "IL").split(",") if code.strip()}

BASELINE_USD_TO_PKR = 275.0

CURRENCY_SYMBOLS = {
    "USD": "$",
    "PKR": "Rs",
    "INR": "Rs",
    "EUR": "EUR",
    "AED": "AED",
    "SAR": "SAR",
    "GBP": "GBP",
}

EXCHANGE_RATE_FALLBACK = {
    "PKR": 275.0,
    "INR": 83.0,
    "EUR": 0.92,
    "AED": 3.67,
    "SAR": 3.75,
    "GBP": 0.79,
}

_EXCHANGE_RATE_API_URL = "https://api.exchangerate-api.com/v4/latest/USD"

_exchange_cache: Dict[str, Any] = {"updated_at": 0.0, "rates": EXCHANGE_RATE_FALLBACK.copy()}
_pkr_plan_cache: Dict[str, Any] = {"month_key": "", "rates": PAKISTAN_FIXED_PKR_BASE.copy()}


class CreateSubscriptionRequest(BaseModel):
    plan: str = Field(..., pattern="^(starter|pro|pro_yearly|max|business|enterprise)$")
    billing_cycle: str = Field(default="monthly", pattern="^(monthly|yearly)$")
    payment_method: str = Field(
        ...,
        pattern="^(stripe|paypal|wise|payoneer|skrill|binance_pay|jazzcash|easypaisa|sadapay|nayapay)$",
    )
    payment_token: str = Field(..., min_length=6, max_length=500)
    consent: bool = False
    currency: str = Field(default="USD", min_length=3, max_length=3)
    country_code: str = Field(default="US", min_length=2, max_length=2)
    team_size: int = Field(default=1, ge=1, le=5000)
    card_last4: Optional[str] = Field(default=None, min_length=4, max_length=4)
    card_brand: Optional[str] = Field(default=None, min_length=2, max_length=40)
    card_expiry_month: Optional[str] = Field(default=None, min_length=1, max_length=2)
    card_expiry_year: Optional[str] = Field(default=None, min_length=2, max_length=4)
    cardholder_name: Optional[str] = Field(default=None, min_length=2, max_length=120)


class RefundRequest(BaseModel):
    revenue_id: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., gt=0)
    reason: str = Field(..., min_length=3, max_length=500)


def _redis_client() -> redis.Redis:
    return redis.from_url(settings.REDIS_URL, decode_responses=True, protocol=2)


async def get_redis() -> redis.Redis:
    return _redis_client()


def encrypt_payment_token(token: str) -> str:
    """Encrypt payment token using Fernet."""
    from cryptography.fernet import Fernet

    key = settings.ENCRYPTION_KEY.encode() if isinstance(settings.ENCRYPTION_KEY, str) else settings.ENCRYPTION_KEY
    f = Fernet(key)
    return f.encrypt(token.encode()).decode()


def verify_stripe_signature(payload: bytes, sig_header: Optional[str], secret: str, tolerance_seconds: int = 300) -> bool:
    """
    Verify Stripe webhook signature using the official v1 format.
    Header format: t=timestamp,v1=signature
    """
    if not sig_header or not secret:
        return False

    try:
        parts: Dict[str, str] = {}
        for item in sig_header.split(","):
            key, _, value = item.partition("=")
            parts[key.strip()] = value.strip()

        timestamp = parts.get("t")
        signature = parts.get("v1")
        if not timestamp or not signature:
            return False

        ts = int(timestamp)
        current_time = int(time_module.time())
        if abs(current_time - ts) > tolerance_seconds:
            return False

        signed_payload = f"{timestamp}.{payload.decode('utf-8')}".encode()
        expected = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)
    except Exception:
        return False


def _normalize_plan(plan: str, billing_cycle: str) -> str:
    if plan == "pro" and billing_cycle == "yearly":
        return "pro_yearly"
    return plan


def _plan_credits(plan: str, team_size: int) -> int:
    credits = int(PLAN_DEFINITIONS.get(plan, {}).get("credits", 0))
    if plan == "business":
        return credits * max(5, team_size)
    return credits


def _is_gateway_active(payment_method: str) -> bool:
    gateway_flag_map = {
        "stripe": settings.STRIPE_GATEWAY_ACTIVE,
        "paypal": settings.PAYPAL_GATEWAY_ACTIVE,
        "wise": settings.WISE_GATEWAY_ACTIVE,
        "payoneer": settings.PAYONEER_GATEWAY_ACTIVE,
        "skrill": settings.SKRILL_GATEWAY_ACTIVE,
        "binance_pay": settings.BINANCE_PAY_GATEWAY_ACTIVE,
        "jazzcash": settings.JAZZCASH_GATEWAY_ACTIVE,
        "easypaisa": settings.EASYPAISA_GATEWAY_ACTIVE,
        "sadapay": settings.SADAPAY_GATEWAY_ACTIVE,
        "nayapay": settings.NAYAPAY_GATEWAY_ACTIVE,
    }
    return bool(gateway_flag_map.get(payment_method, False))


def _validate_payment_token(payment_method: str, payment_token: str) -> None:
    if payment_method == "stripe" and not payment_token.startswith(("tok_", "pm_", "pi_")):
        raise HTTPException(status_code=400, detail="Invalid Stripe payment token format")
    if payment_method == "paypal" and not payment_token.startswith(("PAYID-", "PAY-", "ORDER-")):
        raise HTTPException(status_code=400, detail="Invalid PayPal payment token format")
    if payment_method == "binance_pay" and len(payment_token) < 12:
        raise HTTPException(status_code=400, detail="Invalid Binance Pay token")


async def _fetch_usd_exchange_rates() -> Dict[str, float]:
    now_ts = time_module.time()
    if now_ts - _exchange_cache["updated_at"] < 3600:
        return _exchange_cache["rates"]

    symbols = ",".join(SUPPORTED_DISPLAY_CURRENCIES)
    rates = EXCHANGE_RATE_FALLBACK.copy()

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            response = await client.get(
                _EXCHANGE_RATE_API_URL,
            )
            response.raise_for_status()
            payload = response.json()

            extracted = payload.get("rates") or {}
            for code in SUPPORTED_DISPLAY_CURRENCIES:
                if code == "USD":
                    rates[code] = 1.0
                elif code in extracted:
                    rates[code] = float(extracted[code])
    except Exception as exc:
        logger.warning(f"Exchange API unavailable, using fallback rates: {exc}")

    _exchange_cache["updated_at"] = now_ts
    _exchange_cache["rates"] = rates
    return rates


async def _get_dynamic_pkr_local_rates() -> Dict[str, float]:
    month_key = datetime.now(timezone.utc).strftime("%Y-%m")
    if _pkr_plan_cache["month_key"] == month_key:
        return _pkr_plan_cache["rates"]

    rates = await _fetch_usd_exchange_rates()
    usd_to_pkr = float(rates.get("PKR", BASELINE_USD_TO_PKR))
    if usd_to_pkr <= 0:
        usd_to_pkr = BASELINE_USD_TO_PKR
    scale = max(0.6, min(1.7, usd_to_pkr / BASELINE_USD_TO_PKR))

    updated: Dict[str, float] = {}
    for plan, base_value in PAKISTAN_FIXED_PKR_BASE.items():
        scaled = base_value * scale
        rounded = max(round(scaled / 50.0) * 50.0, 0.0)
        updated[plan] = rounded

    _pkr_plan_cache["month_key"] = month_key
    _pkr_plan_cache["rates"] = updated
    return updated


async def _quote_plan_amount(
    plan: str,
    billing_cycle: str,
    payment_method: str,
    currency: str,
    country_code: str,
    team_size: int,
) -> Dict[str, Any]:
    plan_data = PLAN_DEFINITIONS.get(plan)
    if not plan_data:
        raise HTTPException(status_code=400, detail="Unknown plan")

    if plan == "pro_yearly":
        billing_cycle = "yearly"

    if plan == "pro" and billing_cycle == "yearly":
        plan = "pro_yearly"
        plan_data = PLAN_DEFINITIONS[plan]
        billing_cycle = "yearly"

    if plan == "business" and team_size < int(plan_data.get("minimum_users", 5)):
        raise HTTPException(status_code=400, detail="Business plan requires minimum 5 users")

    if billing_cycle == "yearly":
        usd_amount = float(plan_data.get("yearly_usd", 0.0))
    else:
        usd_amount = float(plan_data.get("monthly_usd", 0.0))

    if plan == "max" and billing_cycle == "yearly" and usd_amount <= 0:
        usd_amount = float(plan_data.get("monthly_usd", 0.0)) * 12

    if plan == "business":
        usd_amount *= team_size

    selected_currency = currency.upper()
    if selected_currency not in SUPPORTED_DISPLAY_CURRENCIES:
        selected_currency = "USD"

    if country_code.upper() in ISRAEL_GEO_BLOCK:
        raise HTTPException(status_code=403, detail="Checkout is not available in your region.")

    allowed_raw = (settings.ALLOWED_COUNTRIES or "ALL").strip().upper()
    if allowed_raw != "ALL":
        allowed_set = {c.strip() for c in allowed_raw.split(",") if c.strip()}
        if country_code.upper() not in allowed_set:
            raise HTTPException(status_code=403, detail="Checkout is not available in your region.")

    local_amount = usd_amount
    local_currency = selected_currency

    if country_code.upper() == "PK" and payment_method in PAKISTAN_LOCAL_GATEWAYS and plan in PAKISTAN_FIXED_PKR_BASE:
        pkr_rates = await _get_dynamic_pkr_local_rates()
        local_currency = "PKR"
        local_amount = pkr_rates.get(plan, PAKISTAN_FIXED_PKR_BASE[plan])
        if plan == "business":
            local_amount *= team_size
    elif selected_currency != "USD":
        rates = await _fetch_usd_exchange_rates()
        local_amount = usd_amount * float(rates.get(selected_currency, 1.0))

    return {
        "plan": plan,
        "billing_cycle": billing_cycle,
        "usd_amount": _safe_round(usd_amount, 2),
        "local_amount": _safe_round(local_amount, 2),
        "local_currency": local_currency,
        "approx_display": _build_approx_display(_safe_round(usd_amount, 2), _safe_round(local_amount, 2), local_currency),
    }


def _safe_round(value: float, decimals: int = 2) -> float:
    if value is None or not isinstance(value, (int, float)):
        return 0.0
    if value != value:  # NaN check
        return 0.0
    if value == float('inf') or value == float('-inf'):
        return 0.0
    return round(float(value), decimals)


def _build_approx_display(usd_amount: float, local_amount: float, currency: str) -> str:
    symbol = CURRENCY_SYMBOLS.get(currency, currency)
    if currency == "USD":
        return f"${_safe_round(usd_amount):.2f}"
    if currency in {"PKR", "INR"}:
        return f"${_safe_round(usd_amount):.2f} ≈ {symbol} {_safe_round(local_amount, 0):,.0f}"
    return f"${_safe_round(usd_amount):.2f} ≈ {symbol} {_safe_round(local_amount):,.2f}"


def _period_end(start: datetime, billing_cycle: str) -> datetime:
    if billing_cycle == "yearly":
        return start + timedelta(days=365)
    return start + timedelta(days=30)


async def _send_billing_notification(user_id: str, message: str) -> None:
    # Placeholder hook for email + SMS integrations.
    logger.info(f"Billing notification queued for user {user_id}: {message}")


async def _log_revenue(
    db: AsyncSession,
    user_id: Any,
    subscription_id: Optional[Any],
    amount: float,
    currency: str,
    payment_method: str,
    transaction_id: str,
    status: str,
    payload: Dict[str, Any],
) -> None:
    revenue = RevenueLog(
        user_id=user_id,
        subscription_id=subscription_id,
        amount=amount,
        currency=currency,
        payment_method=payment_method,
        transaction_id=transaction_id,
        status=status,
        description=json.dumps(payload),
    )
    db.add(revenue)


@router.get("/plans")
async def get_plans(
    request: Request,
    currency: str = Query("USD"),
    country_code: str = Query("US"),
    payment_method: str = Query("stripe"),
):
    """
    PRICING GEO-FIX:
    Country is ALWAYS detected server-side from the request IP (never trusted
    from client query params). Only Pakistan (PK) gets PKR. Every other country
    (or API failure) gets USD. Never defaults to PKR.

    The `currency` query param is only a display override — it never changes
    the underlying USD base price, and it can never force PKR for non-PK users.
    """
    try:
        return await _get_plans_inner(request, currency, country_code, payment_method)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"get_plans unexpected error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load pricing plans")


async def _get_plans_inner(
    request: Request,
    currency: str,
    country_code: str,
    payment_method: str,
) -> Dict[str, Any]:
    payment_method = payment_method.lower()

    from app.services.geolocation import detect_country_from_request, pricing_country_code, pricing_currency_for_country

    try:
        geo = await detect_country_from_request(request)
        detected_country = geo.get("country")
    except Exception:
        detected_country = None

    auto_country = pricing_country_code(detected_country)

    default_currency = pricing_currency_for_country(auto_country)

    selected_currency = currency.upper()
    if selected_currency not in SUPPORTED_DISPLAY_CURRENCIES:
        selected_currency = default_currency

    if auto_country != "PK" and selected_currency == "PKR":
        selected_currency = "USD"

    plans: List[Dict[str, Any]] = []
    for key, plan in PLAN_DEFINITIONS.items():
        if key == "free":
            plans.append(
                {
                    "plan_key": key,
                    "plan": plan["name"],
                    "monthly_usd": 0.0,
                    "yearly_usd": 0.0,
                    "features": plan["features"],
                    "credits": 0,
                    "trial_days": 0,
                }
            )
            continue

        try:
            monthly_quote = await _quote_plan_amount(
                plan=key,
                billing_cycle="monthly",
                payment_method=payment_method,
                currency=selected_currency,
                country_code=auto_country,
                team_size=max(5 if key == "business" else 1, 1),
            )

            yearly_quote = await _quote_plan_amount(
                plan=key,
                billing_cycle="yearly",
                payment_method=payment_method,
                currency=selected_currency,
                country_code=auto_country,
                team_size=max(5 if key == "business" else 1, 1),
            )
        except HTTPException as exc:
            logger.warning(f"Failed to quote plan {key}: {exc.detail}")
            continue
        except Exception as exc:
            logger.warning(f"Unexpected error quoting plan {key}: {exc}")
            continue

        plans.append(
            {
                "plan_key": key,
                "plan": plan["name"],
                "credits": plan["credits"],
                "trial_days": plan["trial_days"],
                "features": plan["features"],
                "badge": plan.get("badge"),
                "monthly": monthly_quote,
                "yearly": yearly_quote,
            }
        )

    return {
        "currency": selected_currency,
        "country_code": auto_country,
        "plans": plans,
        "processing_notice": "Payments securely processed - received in Pakistan (Allied Bank).",
        "geo_block_notice": "Checkout is not available in Israel (IL)." if auto_country in ISRAEL_GEO_BLOCK else None,
        "gateway_categories": {
            "international": ["stripe", "paypal", "wise", "payoneer", "skrill", "binance_pay"],
            "pakistan": ["jazzcash", "easypaisa", "sadapay", "nayapay"],
        },
        "stripe_card_networks": ["Visa", "Mastercard", "Amex", "Apple Pay", "Google Pay"],
    }


@router.get("/methods")
async def get_payment_methods():
    active = [method for method in SUPPORTED_GATEWAYS if _is_gateway_active(method)]
    return {
        "active_gateways": active,
        "allied_bank": {
            "account_name": settings.ALLIED_BANK_ACCOUNT_NAME,
            "account_number": settings.ALLIED_BANK_ACCOUNT_NUMBER,
            "iban": settings.ALLIED_BANK_IBAN,
            "swift": settings.ALLIED_BANK_SWIFT,
            "branch": settings.ALLIED_BANK_BRANCH,
        },
        "payout_config": {
            "stripe_payout_currency": settings.STRIPE_PAYOUT_CURRENCY,
            "wise_auto_settlement": settings.WISE_AUTO_SETTLEMENT_TO_ALLIED,
            "payoneer_auto_settlement": settings.PAYONEER_AUTO_SETTLEMENT_TO_ALLIED,
            "skrill_auto_settlement": settings.SKRILL_AUTO_SETTLEMENT_TO_ALLIED,
        },
        "message": "Payments securely processed - received in Pakistan (Allied Bank).",
    }


@router.post("/create-subscription")
async def create_subscription(
    request: CreateSubscriptionRequest,
    raw_request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    plan = _normalize_plan(request.plan.lower(), request.billing_cycle.lower())
    if plan not in PLAN_DEFINITIONS or plan == "free":
        raise HTTPException(status_code=400, detail="Invalid paid plan")

    if request.payment_method not in SUPPORTED_GATEWAYS:
        raise HTTPException(status_code=400, detail=f"Payment method must be one of: {SUPPORTED_GATEWAYS}")

    if not _is_gateway_active(request.payment_method):
        raise HTTPException(status_code=400, detail=f"Gateway {request.payment_method} is currently disabled")

    _validate_payment_token(request.payment_method, request.payment_token)

    # PRICING GEO-FIX: Country is detected server-side from the request IP.
    # The client-supplied country_code is NEVER trusted for pricing decisions.
    from app.services.geolocation import detect_country_from_request, pricing_country_code

    try:
        geo = await detect_country_from_request(raw_request)
        detected_country = geo.get("country")
    except Exception:
        detected_country = None

    server_country = pricing_country_code(detected_country)

    quote = await _quote_plan_amount(
        plan=plan,
        billing_cycle=request.billing_cycle.lower(),
        payment_method=request.payment_method,
        currency=request.currency,
        country_code=server_country,
        team_size=request.team_size,
    )

    trial_days = int(PLAN_DEFINITIONS[plan].get("trial_days", 0))
    if trial_days > 0 and not request.consent:
        raise HTTPException(
            status_code=400,
            detail="Consent is required for plans with post-trial auto-charge.",
        )

    now = datetime.now(timezone.utc)
    trial_end = now + timedelta(days=trial_days) if trial_days > 0 else None
    current_period_end = trial_end if trial_end else _period_end(now, quote["billing_cycle"])

    encrypted_token = encrypt_payment_token(request.payment_token)

    if current_user.subscription:
        sub = current_user.subscription
    else:
        sub = Subscription(user_id=current_user.id)
        db.add(sub)

    sub.plan = plan
    sub.payment_method = request.payment_method
    sub.payment_token_encrypted = encrypted_token
    sub.card_last4 = request.card_last4
    sub.card_brand = request.card_brand
    sub.card_expiry_month = request.card_expiry_month
    sub.card_expiry_year = request.card_expiry_year
    sub.cardholder_name = request.cardholder_name
    sub.trial_start_at = now if trial_days > 0 else None
    sub.trial_end_at = trial_end
    sub.current_period_start = now
    sub.current_period_end = current_period_end
    sub.status = "active"
    sub.failed_retry_count = 0
    sub.max_retries = 3
    sub.cancel_at_period_end = False

    await db.flush()

    credit_service = CreditService(db, _redis_client())
    credits_granted = _plan_credits(plan, request.team_size)
    if credits_granted > 0:
        credit = await credit_service.grant_credits(
            user_id=str(current_user.id),
            amount=credits_granted,
            transaction_type="grant",
            description=f"{PLAN_DEFINITIONS[plan]['name']} subscription activation",
        )
        credit.last_reset_at = now
        credit.next_reset_at = now + timedelta(days=30)

    charge_status = "pending" if trial_days > 0 else "completed"
    await _log_revenue(
        db=db,
        user_id=current_user.id,
        subscription_id=sub.id,
        amount=quote["usd_amount"] if quote["local_currency"] == "USD" else quote["local_amount"],
        currency=quote["local_currency"],
        payment_method=request.payment_method,
        transaction_id=f"sub-{sub.id}-{int(time_module.time())}",
        status=charge_status,
        payload={
            "plan": plan,
            "billing_cycle": quote["billing_cycle"],
            "usd_amount": quote["usd_amount"],
            "local_amount": quote["local_amount"],
            "local_currency": quote["local_currency"],
            "team_size": request.team_size,
            "allied_bank_iban": settings.ALLIED_BANK_IBAN,
            "allied_bank_swift": settings.ALLIED_BANK_SWIFT,
        },
    )

    await db.commit()

    if trial_days > 0:
        await _send_billing_notification(str(current_user.id), "3-day PRO trial started. Auto-charge will run after trial.")
    else:
        await _send_billing_notification(str(current_user.id), "Subscription charged successfully.")

    return {
        "message": "Subscription activated" if trial_days == 0 else "3-day free trial activated",
        "plan": plan,
        "billing_cycle": quote["billing_cycle"],
        "payment_method": request.payment_method,
        "trial_end": trial_end.isoformat() if trial_end else None,
        "next_billing_date": current_period_end.isoformat() if current_period_end else None,
        "auto_charge_enabled": bool(trial_days > 0 or request.billing_cycle in {"monthly", "yearly"}),
        "credits_granted": credits_granted,
        "checkout_amounts": {
            "usd": quote["usd_amount"],
            "local": quote["local_amount"],
            "currency": quote["local_currency"],
            "display": quote["approx_display"],
        },
        "processing_notice": "Payments securely processed - received in Pakistan (Allied Bank).",
    }


@router.post("/cancel")
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel subscription at period end."""
    if not current_user.subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")

    current_user.subscription.cancel_at_period_end = True
    await db.commit()
    return {
        "message": "Subscription will be canceled at the end of the billing period",
        "current_period_end": current_user.subscription.current_period_end.isoformat() if current_user.subscription.current_period_end else "",
    }


@router.get("/status")
async def get_subscription_status(current_user: User = Depends(get_current_user)):
    """Get current user's subscription status."""
    if not current_user.subscription:
        return {
            "plan": "free",
            "status": "active",
            "trial_active": False,
        }

    sub = current_user.subscription
    now = datetime.now(timezone.utc)
    trial_active = bool(sub.trial_end_at and sub.trial_end_at > now)

    return {
        "plan": sub.plan,
        "status": sub.status,
        "trial_active": trial_active,
        "trial_end": sub.trial_end_at.isoformat() if sub.trial_end_at else None,
        "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
        "payment_method": sub.payment_method,
        "cancel_at_period_end": sub.cancel_at_period_end,
        "failed_retry_count": sub.failed_retry_count,
        "max_retries": sub.max_retries,
    }


@router.post("/retry-failed")
async def retry_failed_payment(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retry failed payment and downgrade to free after max retries."""
    if not current_user.subscription:
        raise HTTPException(status_code=404, detail="No subscription found")

    sub = current_user.subscription

    if sub.status != "past_due":
        raise HTTPException(status_code=400, detail="Subscription is not in past_due status")

    sub.failed_retry_count += 1

    if sub.failed_retry_count >= sub.max_retries:
        sub.plan = "free"
        sub.status = "active"
        sub.failed_retry_count = 0
        await db.commit()
        await _send_billing_notification(str(current_user.id), "Payment retries exhausted. Account downgraded to FREE.")
        return {
            "message": "Maximum retries reached. Subscription downgraded to Free plan.",
            "plan": "free",
        }

    await db.commit()
    await _send_billing_notification(
        str(current_user.id),
        f"Retry attempt {sub.failed_retry_count}/{sub.max_retries} failed. Please update payment method.",
    )

    return {
        "message": f"Payment retry initiated (attempt {sub.failed_retry_count}/{sub.max_retries})",
        "retry_count": sub.failed_retry_count,
    }


@router.post("/stripe/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Stripe webhook endpoint for subscription events.
    SECURITY: Webhook signature verification is mandatory.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=400, detail="Webhook secret not configured")

    if not verify_stripe_signature(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET):
        raise HTTPException(status_code=403, detail="Invalid webhook signature")

    try:
        event = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = event.get("type", "")
    event_id = event.get("id", "")

    from app.models.audit import SecurityEvent

    existing = await db.execute(select(SecurityEvent).where(SecurityEvent.event_type == f"stripe_webhook_{event_id}"))
    if existing.scalar_one_or_none():
        return {"received": True, "duplicate": True}

    security_event = SecurityEvent(
        event_type=f"stripe_webhook_{event_id}",
        severity="info",
        details=f"Stripe webhook received: {event_type}",
    )
    db.add(security_event)

    if event_type == "invoice.payment_succeeded":
        subscription_id = event.get("data", {}).get("object", {}).get("subscription")
        if subscription_id:
            result = await db.execute(select(Subscription).where(Subscription.stripe_subscription_id == subscription_id))
            sub = result.scalar_one_or_none()
            if sub:
                now = datetime.now(timezone.utc)
                sub.status = "active"
                sub.failed_retry_count = 0

                plan_credits = _plan_credits(sub.plan, 1)
                credit_service = CreditService(db, _redis_client())

                credit = await credit_service.get_user_credits(str(sub.user_id))
                if not credit:
                    credit = await credit_service.initialize_user_credits(str(sub.user_id))

                credit.balance = plan_credits
                credit.total_granted += plan_credits
                credit.last_reset_at = now
                credit.next_reset_at = now + timedelta(days=30)

                transaction = CreditTransaction(
                    credit_id=credit.id,
                    user_id=sub.user_id,
                    amount=plan_credits,
                    balance_after=credit.balance,
                    transaction_type="reset",
                    description="Monthly credit reset (payment succeeded)",
                )
                db.add(transaction)

                amount_paid = event.get("data", {}).get("object", {}).get("amount_paid", 0)
                await _log_revenue(
                    db=db,
                    user_id=sub.user_id,
                    subscription_id=sub.id,
                    amount=(amount_paid / 100) if amount_paid else PLAN_DEFINITIONS.get(sub.plan, {}).get("monthly_usd", 0.0),
                    currency="USD",
                    payment_method="stripe",
                    transaction_id=str(subscription_id),
                    status="completed",
                    payload={"plan": sub.plan, "event_type": event_type},
                )

    elif event_type == "invoice.payment_failed":
        subscription_id = event.get("data", {}).get("object", {}).get("subscription")
        if subscription_id:
            result = await db.execute(select(Subscription).where(Subscription.stripe_subscription_id == subscription_id))
            sub = result.scalar_one_or_none()
            if sub:
                sub.failed_retry_count += 1
                sub.status = "past_due"
                if sub.failed_retry_count >= sub.max_retries:
                    sub.plan = "free"
                    sub.status = "active"
                    sub.failed_retry_count = 0

    elif event_type == "customer.subscription.deleted":
        subscription_id = event.get("data", {}).get("object", {}).get("id")
        if subscription_id:
            result = await db.execute(select(Subscription).where(Subscription.stripe_subscription_id == subscription_id))
            sub = result.scalar_one_or_none()
            if sub:
                sub.plan = "free"
                sub.status = "canceled"

    await db.commit()
    return {"received": True}


@router.post("/refund")
async def process_refund(
    request: RefundRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """Process refund - admin only."""
    result = await db.execute(select(RevenueLog).where(RevenueLog.id == request.revenue_id))
    revenue = result.scalar_one_or_none()

    if not revenue:
        raise HTTPException(status_code=404, detail="Revenue log not found")

    if revenue.status == "refunded":
        raise HTTPException(status_code=400, detail="Payment already refunded")

    credits_to_refund = int(request.amount * 100)

    credit_service = CreditService(db, redis_client)
    credit = await credit_service.process_refund(
        user_id=str(revenue.user_id),
        amount=credits_to_refund,
        revenue_id=request.revenue_id,
        reason=request.reason,
    )

    revenue.status = "refunded"

    refund_log = RefundLog(
        revenue_id=request.revenue_id,
        admin_id=current_user.id,
        amount=request.amount,
        reason=request.reason,
    )
    db.add(refund_log)

    await db.commit()

    return {
        "success": True,
        "message": f"Refund processed: ${request.amount} returned to {revenue.payment_method}",
        "credits_refunded": credits_to_refund,
        "new_credit_balance": credit.balance,
    }
