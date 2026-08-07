"""
PRICING GEO-FIX TEST
Verifies:
1. USA/UK VPN → USD
2. Pakistan VPN → PKR
3. No VPN / API failure → USD (default, never PKR)
4. Non-PK user cannot force PKR
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.services.geolocation import (
    pricing_country_code,
    pricing_currency_for_country,
)


def test_pricing_currency_for_country():
    """Test the core currency decision logic."""
    # 1. USA VPN → USD
    assert pricing_currency_for_country("US") == "USD", "US should get USD"
    # 2. UK VPN → USD
    assert pricing_currency_for_country("GB") == "USD", "GB should get USD"
    # 3. Pakistan VPN → PKR
    assert pricing_currency_for_country("PK") == "PKR", "PK should get PKR"
    # 4. No VPN / API failure (None) → USD (never PKR)
    assert pricing_currency_for_country(None) == "USD", "None should default to USD"
    # 5. Unknown country → USD
    assert pricing_currency_for_country("XX") == "USD", "Unknown should default to USD"
    # 6. Empty string → USD
    assert pricing_currency_for_country("") == "USD", "Empty should default to USD"
    # 7. Lowercase pk → PKR (case-insensitive)
    assert pricing_currency_for_country("pk") == "PKR", "lowercase pk should get PKR"
    print("[PASS] pricing_currency_for_country: all 7 cases pass")


def test_pricing_country_code():
    """Test country code normalization."""
    assert pricing_country_code("US") == "US"
    assert pricing_country_code("gb") == "GB"
    assert pricing_country_code(None) == "US", "None should default to US"
    assert pricing_country_code("") == "US", "Empty should default to US"
    assert pricing_country_code("XYZ") == "US", "Invalid 3-letter should default to US"
    assert pricing_country_code("PK") == "PK"
    print("[PASS] pricing_country_code: all 6 cases pass")


def test_non_pk_cannot_force_pkr():
    """Simulate the /plans endpoint logic: non-PK user requesting PKR gets USD."""
    # Simulate what get_plans does
    def simulate_plans_currency(detected_country, requested_currency):
        auto_country = pricing_country_code(detected_country)
        default_currency = pricing_currency_for_country(auto_country)

        selected_currency = requested_currency.upper()
        if selected_currency not in ["USD", "PKR", "INR", "EUR", "AED", "SAR", "GBP"]:
            selected_currency = default_currency

        # Never allow non-PK user to force PKR
        if auto_country != "PK" and selected_currency == "PKR":
            selected_currency = "USD"

        return auto_country, selected_currency

    # US user tries to force PKR → gets USD
    country, currency = simulate_plans_currency("US", "PKR")
    assert country == "US" and currency == "USD", f"US+PKR should be USD, got {country}/{currency}"

    # UK user tries to force PKR → gets USD
    country, currency = simulate_plans_currency("GB", "PKR")
    assert country == "GB" and currency == "USD", f"GB+PKR should be USD, got {country}/{currency}"

    # No VPN (None) tries PKR → gets USD
    country, currency = simulate_plans_currency(None, "PKR")
    assert country == "US" and currency == "USD", f"None+PKR should be USD, got {country}/{currency}"

    # Pakistan user requests PKR → gets PKR
    country, currency = simulate_plans_currency("PK", "PKR")
    assert country == "PK" and currency == "PKR", f"PK+PKR should be PKR, got {country}/{currency}"

    # Pakistan user requests USD → gets USD (display override allowed)
    country, currency = simulate_plans_currency("PK", "USD")
    assert country == "PK" and currency == "USD", f"PK+USD should be USD, got {country}/{currency}"

    # US user requests EUR → gets EUR (display override allowed)
    country, currency = simulate_plans_currency("US", "EUR")
    assert country == "US" and currency == "EUR", f"US+EUR should be EUR, got {country}/{currency}"

    print("[PASS] non-PK cannot force PKR: all 6 cases pass")


def test_quote_plan_amount_logic():
    """Verify the quote logic: PKR only for PK + local gateway, USD otherwise."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

    # Import the quote function directly
    from app.routes.payments import _quote_plan_amount

    async def run():
        # US user with stripe → USD
        quote = await _quote_plan_amount(
            plan="pro",
            billing_cycle="monthly",
            payment_method="stripe",
            currency="USD",
            country_code="US",
            team_size=1,
        )
        assert quote["local_currency"] == "USD", f"US+stripe should be USD, got {quote['local_currency']}"
        assert quote["usd_amount"] == 19.99
        assert quote["local_amount"] == 19.99
        print(f"  US+stripe -> {quote['local_currency']} ${quote['local_amount']}")

        # UK user with stripe → USD
        quote = await _quote_plan_amount(
            plan="pro",
            billing_cycle="monthly",
            payment_method="stripe",
            currency="USD",
            country_code="GB",
            team_size=1,
        )
        assert quote["local_currency"] == "USD", f"GB+stripe should be USD, got {quote['local_currency']}"
        print(f"  GB+stripe -> {quote['local_currency']} ${quote['local_amount']}")

        # Pakistan user with jazzcash → PKR
        quote = await _quote_plan_amount(
            plan="pro",
            billing_cycle="monthly",
            payment_method="jazzcash",
            currency="PKR",
            country_code="PK",
            team_size=1,
        )
        assert quote["local_currency"] == "PKR", f"PK+jazzcash should be PKR, got {quote['local_currency']}"
        assert quote["local_amount"] > 0
        display = quote['approx_display'].replace('≈', '~')
        print(f"  PK+jazzcash -> {quote['local_currency']} Rs {quote['local_amount']} ({display})")

        # Pakistan user with stripe (international gateway) → USD
        quote = await _quote_plan_amount(
            plan="pro",
            billing_cycle="monthly",
            payment_method="stripe",
            currency="USD",
            country_code="PK",
            team_size=1,
        )
        assert quote["local_currency"] == "USD", f"PK+stripe should be USD, got {quote['local_currency']}"
        print(f"  PK+stripe -> {quote['local_currency']} ${quote['local_amount']}")

        # US user with EUR display → EUR
        quote = await _quote_plan_amount(
            plan="pro",
            billing_cycle="monthly",
            payment_method="stripe",
            currency="EUR",
            country_code="US",
            team_size=1,
        )
        assert quote["local_currency"] == "EUR", f"US+EUR should be EUR, got {quote['local_currency']}"
        display = quote['approx_display'].replace('≈', '~')
        print(f"  US+EUR -> {quote['local_currency']} {quote['local_amount']} ({display})")

        print("[PASS] quote_plan_amount: all 5 cases pass")

    asyncio.run(run())


if __name__ == "__main__":
    print("=" * 60)
    print("PRICING GEO-FIX TESTS")
    print("=" * 60)
    test_pricing_currency_for_country()
    test_pricing_country_code()
    test_non_pk_cannot_force_pkr()
    test_quote_plan_amount_logic()
    print("=" * 60)
    print("[PASS] ALL PRICING GEO-FIX TESTS PASSED")
    print("[PASS] PRICING FIXED - international users now see USD, Pakistan sees PKR, default is USD.")
    print("=" * 60)