import hashlib, hmac, json, time

def sign_payload(payload: dict, secret: str) -> tuple[str, str]:
    timestamp = str(int(time.time()))
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    signature = hmac.new(secret.encode(), timestamp.encode() + b"." + body, hashlib.sha256).hexdigest()
    return timestamp, signature

def verify_signature(payload: bytes, timestamp: str, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), timestamp.encode() + b"." + payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
