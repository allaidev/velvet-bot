from __future__ import annotations

import hashlib
import hmac

from bot.services.cryptobot import verify_webhook_signature


def _sign(token: str, body: bytes) -> str:
    secret = hashlib.sha256(token.encode()).digest()
    return hmac.new(secret, body, hashlib.sha256).hexdigest()


def test_signature_valid() -> None:
    token = "super-secret"
    body = b'{"update_type":"invoice_paid","payload":{"invoice_id":1}}'
    sig = _sign(token, body)
    assert verify_webhook_signature(token, body, sig)


def test_signature_invalid_when_body_changed() -> None:
    token = "super-secret"
    body = b'{"update_type":"invoice_paid"}'
    sig = _sign(token, body)
    assert not verify_webhook_signature(token, b"tampered", sig)


def test_signature_missing() -> None:
    assert not verify_webhook_signature("t", b"body", None)
    assert not verify_webhook_signature("t", b"body", "")


def test_signature_wrong_token() -> None:
    body = b'{"a":1}'
    sig = _sign("real-token", body)
    assert not verify_webhook_signature("other-token", body, sig)
