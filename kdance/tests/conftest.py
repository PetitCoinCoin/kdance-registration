import pytest

# import stripe


@pytest.fixture(autouse=True)
def mock_stripe(monkeypatch):
    monkeypatch.setattr(
        "stripe.Product.create", lambda *a, **k: {"id": "stripe_product_id"}
    )
    monkeypatch.setattr(
        "stripe.Price.create", lambda *a, **k: {"id": "stripe_price_id"}
    )
    monkeypatch.setattr(
        "stripe.Price.modify", lambda *a, **k: {"id": "stripe_other_price_id"}
    )
    monkeypatch.setattr(
        "stripe.Coupon.create", lambda *a, **k: {"id": "stripe_coupon_id"}
    )
    monkeypatch.setattr(
        "stripe.checkout.Session.create",
        lambda *a, **k: {"client_secret": "session_secret"},
    )
    monkeypatch.setattr(
        "stripe.Price.create", lambda *a, **k: {"id": "stripe_price_id"}
    )
