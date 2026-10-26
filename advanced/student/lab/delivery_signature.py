"""Shared local delivery contract: HMAC of timestamp + newline + exact bytes."""
import hashlib,hmac,re
def signature(secret,timestamp,body):return hmac.new(secret.encode(),str(timestamp).encode()+b'\n'+body,hashlib.sha256).hexdigest()
def valid(secret,timestamp,body,supplied,now):
    try:stamp=int(timestamp)
    except (ValueError,TypeError):return False
    return bool(re.fullmatch('[0-9a-f]{64}',supplied)) and abs(now-stamp)<=300 and hmac.compare_digest(signature(secret,timestamp,body),supplied)
