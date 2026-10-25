import hmac, hashlib
secret, raw = b"demo-only", b'{"id":1}'
signature = hmac.new(secret, raw, hashlib.sha256).hexdigest()
print(hmac.compare_digest(signature, signature))
